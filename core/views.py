from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum, Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView

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
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise ValidationError("Fecha inválida. Formato esperado: YYYY-MM-DD")


class CatalogsView(APIView):
    """
    Catálogos para frontend (combos).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "tx_types": [{"value": v, "label": l} for v, l in TxType.choices],
            "tx_categories": [{"value": v, "label": l} for v, l in TxCategory.choices],
        })


class AccountsListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        qs = Account.objects.filter(is_active=True).order_by("name")
        return Response(AccountSerializer(qs, many=True).data)


class LedgerDailySummaryView(APIView):
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


class TransactionListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.all().select_related(
            "from_account",
            "to_account",
            "created_by"
        ).order_by("-created_at")

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        account_id = self.request.query_params.get("account_id")
        t = self.request.query_params.get("type")
        cat = self.request.query_params.get("category")
        q = self.request.query_params.get("q")

        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)

        if account_id:
            qs = qs.filter(Q(from_account_id=account_id) | Q(to_account_id=account_id))

        if t:
            qs = qs.filter(type=t)
        if cat:
            qs = qs.filter(category=cat)
        if q:
            qs = qs.filter(description__icontains=q)

        return qs


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


class LoanListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]
    serializer_class = LoanSerializer

    def get_queryset(self):
        return Loan.objects.all().select_related("account", "created_by").order_by("-created_at")