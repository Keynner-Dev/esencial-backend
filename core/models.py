from django.conf import settings
from django.db import models

class Account(models.Model):
    CASH = "CASH"
    WALLET = "WALLET"
    BANK = "BANK"
    TYPE_CHOICES = [(CASH, "Efectivo"), (WALLET, "Billetera"), (BANK, "Banco")]

    name = models.CharField(max_length=50, unique=True)  # Efectivo, Nequi, Bancolombia
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class TxCategory(models.TextChoices):
    MERCANCIA = "MERCANCIA", "Mercancía"
    MONTAJE = "MONTAJE", "Montaje/Mobiliario"
    GASTOS = "GASTOS", "Gastos"
    CAPITAL = "CAPITAL", "Capital"
    PRESTAMO = "PRESTAMO", "Préstamo"
    TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
    AJUSTE = "AJUSTE", "Ajuste"
    VENTA = "VENTA", "Venta"


class TxType(models.TextChoices):
    SALE_INCOME = "SALE_INCOME", "Ingreso por venta"
    PURCHASE_OUTFLOW = "PURCHASE_OUTFLOW", "Salida por compra"
    EXPENSE = "EXPENSE", "Gasto"
    LOAN_IN = "LOAN_IN", "Préstamo recibido"
    LOAN_PAYMENT = "LOAN_PAYMENT", "Pago préstamo"
    CAPITAL_IN = "CAPITAL_IN", "Ingreso capital"
    TRANSFER = "TRANSFER", "Transferencia"
    ADJUSTMENT = "ADJUSTMENT", "Ajuste"


class Transaction(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    type = models.CharField(max_length=30, choices=TxType.choices)
    category = models.CharField(max_length=30, choices=TxCategory.choices)

    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # siempre positivo

    from_account = models.ForeignKey(Account, null=True, blank=True, related_name="outflows", on_delete=models.PROTECT)
    to_account = models.ForeignKey(Account, null=True, blank=True, related_name="inflows", on_delete=models.PROTECT)

    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:
        return f"{self.type} {self.amount}"

class Loan(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    lender_name = models.CharField(max_length=120)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Loan {self.lender_name}"
