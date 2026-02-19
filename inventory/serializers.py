from rest_framework import serializers
from .models import Product


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
        ]
