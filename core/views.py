from datetime import datetime
from django.utils import timezone
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Account, Transaction
from .serializers import AccountSerializer
from .permissions import IsAdminGroup

def _parse_date(date_str: str):
    # YYYY-MM-DD
    return datetime.strptime(date_str, "%Y-%m-%d").date()

class AccountsListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        qs = Account.objects.filter(is_active=True).order_by("name")
        return Response(AccountSerializer(qs, many=True).data)

class LedgerDailySummaryView(APIView):
    """
    Admin: puede consultar cualquier fecha con ?date=YYYY-MM-DD (o sin date = hoy)
    Seller: SOLO puede ver HOY (ignora cualquier date enviado)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = request.user.groups.filter(name="ADMIN").exists()
        date_param = request.query_params.get("date")

        today = timezone.localdate()

        if is_admin:
            target_date = _parse_date(date_param) if date_param else today
        else:
            target_date = today  # vendedor solo hoy

        start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))

        accounts = Account.objects.filter(is_active=True)

        summary = []
        for acc in accounts:
            inflow = Transaction.objects.filter(
                to_account=acc, created_at__range=(start, end)
            ).aggregate(s=Sum("amount"))["s"] or 0

            outflow = Transaction.objects.filter(
                from_account=acc, created_at__range=(start, end)
            ).aggregate(s=Sum("amount"))["s"] or 0

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
