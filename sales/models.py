from decimal import Decimal
from django.db import models
from django.conf import settings
from core.models import Account
from inventory.models import Product
from perfume.models import Fragrance, Presentation


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sales"
    )

    account = models.ForeignKey(Account, on_delete=models.PROTECT)

    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_profit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    is_void = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
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

    sale = models.ForeignKey(
        Sale,
        related_name="items",
        on_delete=models.CASCADE
    )

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Relaciones reales
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    fragrance = models.ForeignKey(
        Fragrance,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    presentation = models.ForeignKey(
        Presentation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # Datos operativos
    qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("1.000"))
    grams_used = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)

    # Datos contables
    sale_price = models.DecimalField(max_digits=14, decimal_places=2)
    cost = models.DecimalField(max_digits=14, decimal_places=2)
    profit = models.DecimalField(max_digits=14, decimal_places=2)

    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.description
