from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from core.permissions import IsSellerOrAdmin, CanRefundOrAdmin
from core.models import Account, Transaction, TxType, TxCategory

from inventory.models import Product, InventoryMovement
from perfume.models import Fragrance, PresentationDose, AlcoholCostByPresentation

from .models import Sale, SaleItem
from .serializers import POSSerializer, SaleSerializer


class POSView(APIView):
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]

    @transaction.atomic
    def post(self, request):
        serializer = POSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account = Account.objects.get(id=data["account_id"])

        sale = Sale.objects.create(
            created_by=request.user,
            account=account,
        )

        total = Decimal("0.00")
        total_cost = Decimal("0.00")

        for item in data["items"]:
            item_type = item["type"]

            # ===================== PERFUME =====================
            if item_type == "PERFUME":
                fragrance = Fragrance.objects.get(id=item["fragrance_id"])
                dose = PresentationDose.objects.get(presentation_id=item["presentation_id"])
                alcohol_cost = AlcoholCostByPresentation.objects.get(presentation_id=item["presentation_id"])

                essence_product = fragrance.essence_product
                grams_needed = dose.grams_essence

                if essence_product.stock_qty < grams_needed:
                    raise ValidationError(f"No hay suficiente stock de {essence_product.name}")

                essence_cost = grams_needed * essence_product.avg_cost_per_unit
                total_item_cost = essence_cost + dose.extras_cost + alcohol_cost.alcohol_cost

                sale_price = item["sale_price"]
                profit = sale_price - total_item_cost

                essence_product.stock_qty -= grams_needed
                essence_product.save(update_fields=["stock_qty"])

                InventoryMovement.objects.create(
                    product=essence_product,
                    movement_type=InventoryMovement.OUT,
                    quantity=grams_needed,
                    reference_type="Sale",
                    reference_id=str(sale.id),
                )

                SaleItem.objects.create(
                    sale=sale,
                    item_type="PERFUME",
                    product=essence_product,
                    fragrance=fragrance,
                    presentation=dose.presentation,
                    grams_used=grams_needed,
                    qty=Decimal("1.000"),
                    sale_price=sale_price,
                    cost=total_item_cost,
                    profit=profit,
                    description=f"{fragrance.name} {dose.presentation.name}",
                )

                total += sale_price
                total_cost += total_item_cost

            # ===================== PRODUCT =====================
            elif item_type == "PRODUCT":
                product = Product.objects.get(id=item["product_id"])
                qty = item["qty"]

                if product.manages_stock and product.stock_qty < qty:
                    raise ValidationError(f"No hay suficiente stock de {product.name}")

                cost = qty * product.avg_cost_per_unit
                sale_price = item["sale_price"]
                profit = sale_price - cost

                if product.manages_stock:
                    product.stock_qty -= qty
                    product.save(update_fields=["stock_qty"])

                    InventoryMovement.objects.create(
                        product=product,
                        movement_type=InventoryMovement.OUT,
                        quantity=qty,
                        reference_type="Sale",
                        reference_id=str(sale.id),
                    )

                SaleItem.objects.create(
                    sale=sale,
                    item_type="PRODUCT",
                    product=product,
                    qty=qty,
                    sale_price=sale_price,
                    cost=cost,
                    profit=profit,
                    description=product.name,
                )

                total += sale_price
                total_cost += cost

            # ===================== ESSENCE =====================
            elif item_type == "ESSENCE":
                product = Product.objects.get(id=item["product_id"])
                qty = item["qty"]

                if product.stock_qty < qty:
                    raise ValidationError(f"No hay suficiente stock de {product.name}")

                cost = qty * product.avg_cost_per_unit
                sale_price = item["sale_price"]
                profit = sale_price - cost

                product.stock_qty -= qty
                product.save(update_fields=["stock_qty"])

                InventoryMovement.objects.create(
                    product=product,
                    movement_type=InventoryMovement.OUT,
                    quantity=qty,
                    reference_type="Sale",
                    reference_id=str(sale.id),
                )

                SaleItem.objects.create(
                    sale=sale,
                    item_type="ESSENCE",
                    product=product,
                    qty=qty,
                    sale_price=sale_price,
                    cost=cost,
                    profit=profit,
                    description=f"{product.name} ({qty}g)",
                )

                total += sale_price
                total_cost += cost

            else:
                raise ValidationError(f"Tipo de item inválido: {item_type}")

        sale.total = total
        sale.total_cost = total_cost
        sale.total_profit = total - total_cost
        sale.save(update_fields=["total", "total_cost", "total_profit"])

        Transaction.objects.create(
            created_by=request.user,
            type=TxType.SALE_INCOME,
            category=TxCategory.VENTA,
            description=f"Venta #{sale.id}",
            amount=total,
            to_account=account,
            reference_type="Sale",
            reference_id=str(sale.id),
        )

        return Response({
            "sale_id": sale.id,
            "total": float(total),
            "profit": float(sale.total_profit),
        })


class RefundSaleView(APIView):
    permission_classes = [IsAuthenticated, CanRefundOrAdmin]

    @transaction.atomic
    def post(self, request, sale_id):
        sale = Sale.objects.get(id=sale_id)

        if sale.is_void:
            return Response({"error": "La venta ya está anulada."}, status=400)

        for item in sale.items.select_related("product").all():
            if not item.product:
                continue

            if item.item_type == "PERFUME":
                if not item.grams_used:
                    raise ValidationError("Este perfume no tiene grams_used guardado. No se puede devolver stock.")
                item.product.stock_qty += item.grams_used
                item.product.save(update_fields=["stock_qty"])

                InventoryMovement.objects.create(
                    product=item.product,
                    movement_type=InventoryMovement.IN,
                    quantity=item.grams_used,
                    reference_type="Refund",
                    reference_id=str(sale.id),
                )

            elif item.item_type in ["PRODUCT", "ESSENCE"]:
                if item.product.manages_stock:
                    item.product.stock_qty += item.qty
                    item.product.save(update_fields=["stock_qty"])

                    InventoryMovement.objects.create(
                        product=item.product,
                        movement_type=InventoryMovement.IN,
                        quantity=item.qty,
                        reference_type="Refund",
                        reference_id=str(sale.id),
                    )

        # ✅ FIX: TxType es ADJUSTMENT (no ADJUSTMENT mal escrito)
        Transaction.objects.create(
            created_by=request.user,
            type=TxType.ADJUSTMENT if hasattr(TxType, "ADJUSTMENT") else TxType.ADJUSTMENT,  # safety
            category=TxCategory.VENTA,
            description=f"Anulación venta #{sale.id}",
            amount=sale.total,
            from_account=sale.account,
            reference_type="SaleRefund",
            reference_id=str(sale.id),
        )

        sale.is_void = True
        sale.void_reason = "Anulada"
        sale.save(update_fields=["is_void", "void_reason"])

        return Response({"message": "Venta anulada correctamente."})


class SalesSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        sales = Sale.objects.filter(created_at__date=today, is_void=False)

        total = sales.aggregate(total=Sum("total"))["total"] or 0
        profit = sales.aggregate(profit=Sum("total_profit"))["profit"] or 0

        return Response({
            "date": str(today),
            "total_sales": float(total),
            "total_profit": float(profit),
        })


class SalesReportByRangeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        if not start or not end:
            return Response({"error": "Debe enviar start y end YYYY-MM-DD"}, status=400)

        sales = Sale.objects.filter(created_at__date__range=[start, end], is_void=False)

        total = sales.aggregate(total=Sum("total"))["total"] or 0
        profit = sales.aggregate(profit=Sum("total_profit"))["profit"] or 0

        return Response({
            "start": start,
            "end": end,
            "total_sales": float(total),
            "total_profit": float(profit),
        })


class TopItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top = (
            SaleItem.objects
            .filter(sale__is_void=False)
            .values("description")
            .annotate(total_sold=Count("id"))
            .order_by("-total_sold")[:5]
        )
        return Response(list(top))


class SaleListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]
    serializer_class = SaleSerializer

    def get_queryset(self):
        qs = (
            Sale.objects
            .all()
            .select_related("account", "created_by")
            .prefetch_related("items", "items__product", "items__fragrance", "items__presentation")
            .order_by("-created_at")
        )

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        account_id = self.request.query_params.get("account_id")
        is_void = self.request.query_params.get("is_void")
        q = self.request.query_params.get("q")

        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if is_void in ["true", "false"]:
            qs = qs.filter(is_void=(is_void == "true"))
        if q:
            qs = qs.filter(items__description__icontains=q).distinct()

        return qs


class SaleDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]
    serializer_class = SaleSerializer
    lookup_url_kwarg = "sale_id"

    def get_queryset(self):
        return (
            Sale.objects
            .all()
            .select_related("account", "created_by")
            .prefetch_related("items", "items__product", "items__fragrance", "items__presentation")
        )