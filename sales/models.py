from django.conf import settings
from django.db import models
from core.models import Account

class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    account = models.ForeignKey(Account, on_delete=models.PROTECT)  # Efectivo/Nequi/Bancolombia
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    is_void = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = [
            ("can_refund", "Can refund/void sales"),
        ]

    def __str__(self) -> str:
        return f"Sale #{self.id}"
