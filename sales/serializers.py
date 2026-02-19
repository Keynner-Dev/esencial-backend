from rest_framework import serializers


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
