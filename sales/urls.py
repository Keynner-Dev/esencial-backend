from django.urls import path
from .views import (
    POSView,
    RefundSaleView,
    SalesSummaryView,
    SalesReportByRangeView,
    TopItemsView,
    SaleListView,
    SaleDetailView,
)

urlpatterns = [
    # POS
    path("sales/pos/", POSView.as_view(), name="pos-sale"),
    path("sales/<int:sale_id>/refund/", RefundSaleView.as_view(), name="refund-sale"),

    # Reportes
    path("sales/summary/", SalesSummaryView.as_view(), name="sales-summary"),
    path("sales/report-range/", SalesReportByRangeView.as_view(), name="sales-report-range"),
    path("sales/top-items/", TopItemsView.as_view(), name="sales-top-items"),

    # Historial
    path("sales/", SaleListView.as_view(), name="sales-list"),
    path("sales/<int:sale_id>/", SaleDetailView.as_view(), name="sales-detail"),
]