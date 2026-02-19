from decimal import Decimal
from django.db import models
from inventory.models import Product


class Presentation(models.Model):
    name = models.CharField(max_length=20, unique=True)  # 30ml, 60ml, 100ml
    ml = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Fragrance(models.Model):
    name = models.CharField(max_length=120, unique=True)
    essence_product = models.ForeignKey(Product, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class PresentationDose(models.Model):
    presentation = models.OneToOneField(Presentation, on_delete=models.CASCADE)
    grams_essence = models.DecimalField(max_digits=10, decimal_places=3)
    extras_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("500.00"))

    def __str__(self):
        return f"Dose {self.presentation.name}"


class AlcoholCostByPresentation(models.Model):
    presentation = models.OneToOneField(Presentation, on_delete=models.CASCADE)
    alcohol_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"Alcohol cost {self.presentation.name}"
