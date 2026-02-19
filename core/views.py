from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Account, Transaction, TxType, TxCategory, Loan
from .serializers import (
    AccountSerializer,
    TransactionSerializer,
    CreateTransactionSerializer,
    LoanSerializer,
    CreateLoanSerializer,
    PayLoanSerializer,
)
from .permissions import IsAdminGroup


def _parse_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class AccountsListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        qs = Account.objects.filter(is_active=True).order_by("name")
        return Response(AccountSerializer(qs, many=True).data)


class LedgerDailySummaryView(APIView):
    """
    Admin: puede consultar cualquier fecha con ?date=YYYY-MM-DD
    Seller: SOLO puede ver HOY (si lo quieres, cambia permiso y lógica)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = request.user.groups.filter(name="ADMIN").exists()
        date_param = request.query_params.get("date")

        today = timezone.localdate()
        target_date = _parse_date(date_param) if (is_admin and date_param) else today

        start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))

        accounts = Account.objects.filter(is_active=True)
        summary = []

        for acc in accounts:
            inflow = Transaction.objects.filter(
                to_account=acc, created_at__range=(start, end)
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0")

            outflow = Transaction.objects.filter(
                from_account=acc, created_at__range=(start, end)
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0")

            summary.append({
                "account_id": acc.id,
                "account_name": acc.name,
                "inflow": float(inflow),
                "outflow": float(outflow),
                "net": float(inflow - outflow),
            })

        return Response({
            "date": str(target_date),
            "summary": summary,
            "scope": "ADMIN_ANY_DATE" if is_admin else "SELLER_TODAY_ONLY",
        })


class CreateLedgerTransactionView(APIView):
    """
    Crear movimientos de caja:
    - GASTOS (EXPENSE)
    - CAPITAL (CAPITAL_IN)
    - TRANSFER (TRANSFER)
    - AJUSTE (ADJUSTMENT)
    """
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def post(self, request):
        s = CreateTransactionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        from_acc = Account.objects.get(id=d["from_account_id"]) if d.get("from_account_id") else None
        to_acc = Account.objects.get(id=d["to_account_id"]) if d.get("to_account_id") else None

        tx = Transaction.objects.create(
            created_by=request.user,
            type=d["type"],
            category=d["category"],
            description=d.get("description", ""),
            amount=d["amount"],
            from_account=from_acc,
            to_account=to_acc,
            reference_type=d.get("reference_type", ""),
            reference_id=d.get("reference_id", ""),
        )
        return Response(TransactionSerializer(tx).data, status=201)


class TransactionListView(APIView):
    """
    Listar transacciones con filtros:
      ?start=YYYY-MM-DD&end=YYYY-MM-DD
      ?account_id= (match from o to)
      ?type=
      ?category=
    """
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        account_id = request.query_params.get("account_id")
        t = request.query_params.get("type")
        cat = request.query_params.get("category")

        qs = Transaction.objects.all().order_by("-created_at")

        if start and end:
            qs = qs.filter(created_at__date__range=[start, end])
        if account_id:
            qs = qs.filter(from_account_id=account_id) | qs.filter(to_account_id=account_id)
        if t:
            qs = qs.filter(type=t)
        if cat:
            qs = qs.filter(category=cat)

        qs = qs[:500]
        return Response(TransactionSerializer(qs, many=True).data)


class AccountBalanceView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        accounts = Account.objects.all()
        result = []

        for acc in accounts:
            inflow = Transaction.objects.filter(to_account=acc).aggregate(s=Sum("amount"))["s"] or 0
            outflow = Transaction.objects.filter(from_account=acc).aggregate(s=Sum("amount"))["s"] or 0

            result.append({
                "account_id": acc.id,
                "account": acc.name,
                "balance": float(Decimal(inflow) - Decimal(outflow)),
            })

        return Response(result)


class CreateLoanView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def post(self, request):
        s = CreateLoanSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        account = Account.objects.get(id=d["account_id"])
        amount = d["amount"]

        loan = Loan.objects.create(
            lender_name=d["lender_name"],
            total_amount=amount,
            remaining_amount=amount,
            account=account,
            created_by=request.user,
        )

        Transaction.objects.create(
            created_by=request.user,
            type=TxType.LOAN_IN,
            category=TxCategory.PRESTAMO,
            description=f"Préstamo de {loan.lender_name}",
            amount=amount,
            to_account=account,
            reference_type="Loan",
            reference_id=str(loan.id),
        )

        return Response(LoanSerializer(loan).data, status=201)


class PayLoanView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def post(self, request, loan_id: int):
        loan = Loan.objects.get(id=loan_id)

        s = PayLoanSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        amount = d["amount"]
        from_account = Account.objects.get(id=d["from_account_id"])

        if amount > loan.remaining_amount:
            raise ValidationError("El pago no puede ser mayor al saldo restante del préstamo.")

        loan.remaining_amount -= amount
        loan.save(update_fields=["remaining_amount"])

        Transaction.objects.create(
            created_by=request.user,
            type=TxType.LOAN_PAYMENT,
            category=TxCategory.PRESTAMO,
            description=f"Pago préstamo {loan.lender_name} (Loan #{loan.id})",
            amount=amount,
            from_account=from_account,
            reference_type="LoanPayment",
            reference_id=str(loan.id),
        )

        return Response(LoanSerializer(loan).data)


class LoanListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        qs = Loan.objects.all().order_by("-created_at")
        return Response(LoanSerializer(qs, many=True).data)