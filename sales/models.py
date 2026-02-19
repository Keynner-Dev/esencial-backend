from decimal import Decimal
from django.db import models
from django.conf import settings
from core.models import Account


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_profit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    is_void = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = [
            ("can_refund", "Can refund/void sales"),
        ]

    def __str__(self):
        return f"Sale #{self.id}"


class SaleItem(models.Model):
    PERFUME = "PERFUME"
    PRODUCT = "PRODUCT"
    ESSENCE = "ESSENCE"

    TYPE_CHOICES = [
        (PERFUME, "Perfume preparado"),
        (PRODUCT, "Producto normal"),
        (ESSENCE, "Esencia por gramos"),
    ]

    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    description = models.CharField(max_length=255)

    qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("1.000"))

    sale_price = models.DecimalField(max_digits=14, decimal_places=2)
    cost = models.DecimalField(max_digits=14, decimal_places=2)
    profit = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return self.description
