from decimal import Decimal
from django.db import models, transaction
from django.conf import settings

from core.models import Account, Transaction as LedgerTransaction, TxType, TxCategory


class Unit(models.TextChoices):
    GRAM = "g", "Gramos"
    ML = "ml", "Mililitros"
    UNIT = "unit", "Unidad"


class ProductType(models.TextChoices):
    ESSENCE = "ESSENCE", "Esencia"
    RESALE = "RESALE", "Producto reventa"
    SUPPLY = "SUPPLY", "Insumo"
    BOTTLE = "BOTTLE", "Envase"
    COST_ONLY = "COST_ONLY", "Solo costo (sin stock)"


class Product(models.Model):
    name = models.CharField(max_length=120, unique=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    unit = models.CharField(max_length=10, choices=Unit.choices)

    manages_stock = models.BooleanField(default=True)
    stock_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0.000"))
    avg_cost_per_unit = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PurchaseInvoice(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    supplier_name = models.CharField(max_length=120, blank=True)
    invoice_number = models.CharField(max_length=60, blank=True)
    notes = models.TextField(blank=True)

    # Clasificación contable
    category = models.CharField(
        max_length=30,
        choices=TxCategory.choices,
        default=TxCategory.MERCANCIA
    )

    # Desde qué cuenta se pagó (efectivo, nequi, banco)
    paid_from_account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL
    )

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # Para evitar que cree ledger 2 veces
    ledger_created = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice #{self.id}"

    def create_ledger_entry(self):
        """
        Crea la salida de caja por compra.
        Solo se crea una vez (ledger_created=True).
        """
        if self.ledger_created:
            return

        if self.paid_from_account and self.total_amount > 0:
            LedgerTransaction.objects.create(
                created_by=self.created_by,
                type=TxType.PURCHASE_OUTFLOW,
                category=self.category,
                description=f"Compra factura #{self.id}",
                amount=self.total_amount,
                from_account=self.paid_from_account,
                reference_type="PurchaseInvoice",
                reference_id=str(self.id),
            )
            self.ledger_created = True
            self.save(update_fields=["ledger_created"])

    @transaction.atomic
    def finalize(self):
        """
        Llamar cuando ya terminaste de agregar items.
        Calcula total (por si hay inconsistencias) y crea el ledger.
        """
        total = self.items.aggregate(s=models.Sum("line_total"))["s"] or Decimal("0.00")
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        self.create_ledger_entry()


class PurchaseItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    qty = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        creating = self.pk is None

        with transaction.atomic():
            super().save(*args, **kwargs)

            if creating:
                # Actualizar stock y costo promedio ponderado si maneja stock
                if self.product.manages_stock:
                    p = self.product
                    old_qty = p.stock_qty
                    old_avg = p.avg_cost_per_unit

                    new_qty = old_qty + self.qty

                    if new_qty > 0:
                        new_avg = ((old_qty * old_avg) + (self.qty * self.unit_cost)) / new_qty
                    else:
                        new_avg = old_avg

                    p.stock_qty = new_qty
                    p.avg_cost_per_unit = new_avg
                    p.save(update_fields=["stock_qty", "avg_cost_per_unit"])

                # Actualiza total_amount de la factura sumando el item (rápido)
                PurchaseInvoice.objects.filter(pk=self.invoice_id).update(
                    total_amount=models.F("total_amount") + self.line_total
                )
