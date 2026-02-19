from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "created_by", "account", "total", "is_void")
    list_filter = ("account", "is_void")
    date_hierarchy = "created_at"
