from django.contrib import admin
from .models import Account, Transaction

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "type", "category", "amount", "from_account", "to_account", "created_by")
    list_filter = ("type", "category", "from_account", "to_account")
    search_fields = ("description", "reference_type", "reference_id")
    date_hierarchy = "created_at"
