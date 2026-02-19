from django.contrib import admin
from .models import Product, PurchaseInvoice, PurchaseItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "unit", "stock_qty", "avg_cost_per_unit", "manages_stock")
    list_filter = ("product_type", "manages_stock")
    search_fields = ("name",)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "supplier_name", "category", "total_amount", "paid_from_account")
    list_filter = ("category", "paid_from_account")
    inlines = [PurchaseItemInline]
    date_hierarchy = "created_at"
