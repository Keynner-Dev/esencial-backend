from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404

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


class ProductListView(ListAPIView):
    queryset = Product.objects.filter(is_active=True).order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]


class PurchaseListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        qs = PurchaseInvoice.objects.all().order_by("-created_at")[:200]
        return Response(PurchaseInvoiceSerializer(qs, many=True).data)


class PurchaseDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request, purchase_id: int):
        inv = get_object_or_404(PurchaseInvoice, id=purchase_id)
        return Response(PurchaseInvoiceSerializer(inv).data)


class PurchaseCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroup]

    @transaction.atomic
    def post(self, request):
        s = PurchaseCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        paid_from = None
        paid_from_id = data.get("paid_from_account_id", None)
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

        # crear items
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

        # finalizar
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


class InventoryMovementListView(APIView):
    """
    Kardex: movimientos por producto y/o rango de fechas
    Query params:
      - product_id (opcional)
      - start (YYYY-MM-DD opcional)
      - end (YYYY-MM-DD opcional)
    """
    permission_classes = [IsAuthenticated, IsAdminGroup]

    def get(self, request):
        product_id = request.query_params.get("product_id")
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        qs = InventoryMovement.objects.all().order_by("-created_at")

        if product_id:
            qs = qs.filter(product_id=product_id)

        if start and end:
            qs = qs.filter(created_at__date__range=[start, end])

        qs = qs[:500]  # límite para no reventar el frontend
        return Response(InventoryMovementSerializer(qs, many=True).data)