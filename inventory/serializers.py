from decimal import Decimal
from rest_framework import serializers

from .models import Product, PurchaseInvoice, PurchaseItem, InventoryMovement


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_type",
            "unit",
            "manages_stock",
            "stock_qty",
            "avg_cost_per_unit",
            "is_active",
        ]


class PurchaseItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4)
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)

    def validate(self, attrs):
        if attrs["qty"] <= 0:
            raise serializers.ValidationError("qty debe ser > 0")
        if attrs["unit_cost"] < 0:
            raise serializers.ValidationError("unit_cost no puede ser negativo")
        return attrs


class PurchaseCreateSerializer(serializers.Serializer):
    supplier_name = serializers.CharField(required=False, allow_blank=True)
    invoice_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    category = serializers.CharField()  # TxCategory value
    paid_from_account_id = serializers.IntegerField(required=False, allow_null=True)

    items = PurchaseItemCreateSerializer(many=True)
    finalize = serializers.BooleanField(default=True)


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ["id", "product", "product_name", "qty", "unit_cost", "line_total"]


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    paid_from_account_name = serializers.CharField(source="paid_from_account.name", read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            "id",
            "created_at",
            "supplier_name",
            "invoice_number",
            "notes",
            "category",
            "paid_from_account",
            "paid_from_account_name",
            "total_amount",
            "ledger_created",
            "items",
        ]


class InventoryMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "created_at",
            "product",
            "product_name",
            "movement_type",
            "quantity",
            "reference_type",
            "reference_id",
        ]