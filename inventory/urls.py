from django.urls import path
from .views import (
    ProductListView,
    PurchaseCreateView,
    PurchaseListView,
    PurchaseDetailView,
    PurchaseFinalizeView,
    InventoryMovementListView,
)

urlpatterns = [
    # Productos
    path("products/", ProductListView.as_view(), name="product-list"),

    # Compras
    path("purchases/", PurchaseListView.as_view(), name="purchase-list"),
    path("purchases/create/", PurchaseCreateView.as_view(), name="purchase-create"),
    path("purchases/<int:purchase_id>/", PurchaseDetailView.as_view(), name="purchase-detail"),
    path("purchases/<int:purchase_id>/finalize/", PurchaseFinalizeView.as_view(), name="purchase-finalize"),

    # Kardex
    path("inventory/movements/", InventoryMovementListView.as_view(), name="inventory-movements"),
]