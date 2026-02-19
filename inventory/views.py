from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from core.permissions import IsAdminGroup, IsSellerOrAdmin
from core.models import Account

from .models import Product, PurchaseInvoice, PurchaseItem, InventoryMovement
from .serializers import (
    ProductSerializer,
    PurchaseCreateSerializer,
    PurchaseInvoiceSerializer,
    InventoryMovementSerializer,
)


def _parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        raise ValidationError(f"Fecha inválida: {date_str}. Formato esperado: YYYY-MM-DD")


# =========================
# PRODUCTS
# =========================
class ProductListView(ListAPIView):
    """
    Productos (seller/admin).
    Query params:
      - q: búsqueda por nombre
      - product_type: ESSENCE | RESALE | SUPPLY | BOTTLE | COST_ONLY
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).order_by("name")

        q = self.request.query_params.get("q")
        product_type = self.request.query_params.get("product_type")

        if q:
            qs = qs.filter(name__icontains=q)

        if product_type:
            qs = qs.filter(product_type=product_type)

        return qs


# =========================
# PURCHASES
# =========================
class PurchaseListView(ListAPIView):
    """
    Lista de compras paginada (admin).
    Query params:
      - q: busca en supplier_name o invoice_number
    """
    permission_classes = [IsAuthenticated, IsAdminGroup]
    serializer_class = PurchaseInvoiceSerializer

    def get_queryset(self):
        qs = (
            PurchaseInvoice.objects
            .all()
            .select_related("paid_from_account")
            .prefetch_related("items", "items__product")
            .order_by("-created_at")
        )

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(supplier_name__icontains=q) |
                Q(invoice_number__icontains=q)
            )

        return qs


class PurchaseDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request, purchase_id: int):
        inv = (
            PurchaseInvoice.objects
            .select_related("paid_from_account")
            .prefetch_related("items", "items__product")
            .filter(id=purchase_id)
            .first()
        )
        if not inv:
            return Response({"error": "Compra no encontrada."}, status=404)

        return Response(PurchaseInvoiceSerializer(inv).data)


class PurchaseCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    @transaction.atomic
    def post(self, request):
        s = PurchaseCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        paid_from = None
        paid_from_id = data.get("paid_from_account_id")
        if paid_from_id:
            paid_from = get_object_or_404(Account, id=paid_from_id)

        invoice = PurchaseInvoice.objects.create(
            supplier_name=data.get("supplier_name", ""),
            invoice_number=data.get("invoice_number", ""),
            notes=data.get("notes", ""),
            category=data["category"],
            paid_from_account=paid_from,
            created_by=request.user,
        )

        if not data["items"]:
            raise ValidationError("Debe enviar al menos 1 item.")

        for it in data["items"]:
            product = get_object_or_404(Product, id=it["product_id"])

            qty = it["qty"]
            unit_cost = it["unit_cost"]

            line_total = it.get("line_total")
            if line_total is None:
                line_total = (qty * unit_cost).quantize(Decimal("0.01"))

            PurchaseItem.objects.create(
                invoice=invoice,
                product=product,
                qty=qty,
                unit_cost=unit_cost,
                line_total=line_total,
            )

        if data.get("finalize", True):
            invoice.finalize()

        invoice.refresh_from_db()
        return Response(PurchaseInvoiceSerializer(invoice).data, status=201)


class PurchaseFinalizeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    @transaction.atomic
    def post(self, request, purchase_id: int):
        invoice = get_object_or_404(PurchaseInvoice, id=purchase_id)
        invoice.finalize()
        invoice.refresh_from_db()
        return Response(PurchaseInvoiceSerializer(invoice).data)


# =========================
# KARDEX / INVENTORY MOVEMENTS
# =========================
class InventoryMovementListView(ListAPIView):
    """
    Kardex paginado (admin).

    Query params:
      - product_id (opcional)
      - start (YYYY-MM-DD opcional)  -> desde esta fecha (inclusive)
      - end   (YYYY-MM-DD opcional)  -> hasta esta fecha (inclusive)
    """
    permission_classes = [IsAuthenticated, IsAdminGroup]
    serializer_class = InventoryMovementSerializer

    def get_queryset(self):
        product_id = self.request.query_params.get("product_id")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        qs = InventoryMovement.objects.all().select_related("product").order_by("-created_at")

        if product_id:
            qs = qs.filter(product_id=product_id)

        if start:
            start_date = _parse_date(start)
            qs = qs.filter(created_at__date__gte=start_date)

        if end:
            end_date = _parse_date(end)
            qs = qs.filter(created_at__date__lte=end_date)

        return qs