from rest_framework import serializers
from .models import Sale, SaleItem


class POSItemSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["PERFUME", "PRODUCT", "ESSENCE"])

    # PERFUME
    fragrance_id = serializers.IntegerField(required=False)
    presentation_id = serializers.IntegerField(required=False)
    is_refill = serializers.BooleanField(required=False, default=False)

    # PRODUCT / ESSENCE
    product_id = serializers.IntegerField(required=False)
    qty = serializers.DecimalField(max_digits=14, decimal_places=3, required=False)

    sale_price = serializers.DecimalField(max_digits=14, decimal_places=2)


class POSSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    items = POSItemSerializer(many=True)



class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    fragrance_name = serializers.CharField(source="fragrance.name", read_only=True)
    presentation_name = serializers.CharField(source="presentation.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "item_type",
            "description",
            "qty",
            "grams_used",
            "sale_price",
            "cost",
            "profit",
            "product",
            "product_name",
            "fragrance",
            "fragrance_name",
            "presentation",
            "presentation_name",
        ]


class SaleSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "created_at",
            "created_by",
            "created_by_username",
            "account",
            "account_name",
            "total",
            "total_cost",
            "total_profit",
            "is_void",
            "void_reason",
            "items",
        ]