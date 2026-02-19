from decimal import Decimal
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsSellerOrAdmin, CanRefundOrAdmin
from core.models import Account, Transaction, TxType, TxCategory
from inventory.models import Product
from perfume.models import Fragrance, PresentationDose, AlcoholCostByPresentation
from .models import Sale, SaleItem
from .serializers import POSSerializer
from django.db.models import Sum
from django.utils import timezone




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
                alcohol_cost = AlcoholCostByPresentation.objects.get(
                    presentation_id=item["presentation_id"]
                )

                essence_product = fragrance.essence_product
                grams_needed = dose.grams_essence

                if essence_product.stock_qty < grams_needed:
                    raise Exception(f"No hay suficiente stock de {essence_product.name}")

                essence_cost = grams_needed * essence_product.avg_cost_per_unit
                total_item_cost = essence_cost + dose.extras_cost + alcohol_cost.alcohol_cost

                sale_price = item["sale_price"]
                profit = sale_price - total_item_cost

                essence_product.stock_qty -= grams_needed
                essence_product.save(update_fields=["stock_qty"])

                SaleItem.objects.create(
                    sale=sale,
                    item_type="PERFUME",
                    description=f"{fragrance.name} {dose.presentation.name}",
                    qty=1,
                    sale_price=sale_price,
                    cost=total_item_cost,
                    profit=profit,
                )

                total += sale_price
                total_cost += total_item_cost

            # ===================== PRODUCT =====================
            elif item_type == "PRODUCT":
                product = Product.objects.get(id=item["product_id"])
                qty = item["qty"]

                if product.manages_stock and product.stock_qty < qty:
                    raise Exception(f"No hay suficiente stock de {product.name}")

                cost = qty * product.avg_cost_per_unit
                sale_price = item["sale_price"]
                profit = sale_price - cost

                if product.manages_stock:
                    product.stock_qty -= qty
                    product.save(update_fields=["stock_qty"])

                SaleItem.objects.create(
                    sale=sale,
                    item_type="PRODUCT",
                    description=product.name,
                    qty=qty,
                    sale_price=sale_price,
                    cost=cost,
                    profit=profit,
                )

                total += sale_price
                total_cost += cost

            # ===================== ESSENCE =====================
            elif item_type == "ESSENCE":
                product = Product.objects.get(id=item["product_id"])
                qty = item["qty"]

                if product.stock_qty < qty:
                    raise Exception(f"No hay suficiente stock de {product.name}")

                cost = qty * product.avg_cost_per_unit
                sale_price = item["sale_price"]
                profit = sale_price - cost

                product.stock_qty -= qty
                product.save(update_fields=["stock_qty"])

                SaleItem.objects.create(
                    sale=sale,
                    item_type="ESSENCE",
                    description=f"{product.name} ({qty}g)",
                    qty=qty,
                    sale_price=sale_price,
                    cost=cost,
                    profit=profit,
                )

                total += sale_price
                total_cost += cost

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


# ===================== REFUND =====================

class RefundSaleView(APIView):
    permission_classes = [IsAuthenticated, CanRefundOrAdmin]

    @transaction.atomic
    def post(self, request, sale_id):
        sale = Sale.objects.get(id=sale_id)

        if sale.is_void:
            return Response({"error": "La venta ya está anulada."}, status=400)

        # devolver stock
        for item in sale.items.all():
            if item.item_type == "PERFUME":
                # no tenemos gramos guardados, pero se puede mejorar luego
                pass
            elif item.item_type in ["PRODUCT", "ESSENCE"]:
                product = Product.objects.get(name=item.description.split(" (")[0])
                if product.manages_stock:
                    product.stock_qty += item.qty
                    product.save(update_fields=["stock_qty"])

        # reversar caja
        Transaction.objects.create(
            created_by=request.user,
            type=TxType.ADJUSTMENT,
            category=TxCategory.VENTA,
            description=f"Anulación venta #{sale.id}",
            amount=sale.total,
            from_account=sale.account,
            reference_type="Sale",
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
