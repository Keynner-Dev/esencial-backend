from django.urls import path
from .views import POSView, RefundSaleView, SalesReportByRangeView, SalesSummaryView, TopItemsView

urlpatterns = [
    path("sales/pos/", POSView.as_view(), name="pos-sale"),
    path("sales/<int:sale_id>/refund/", RefundSaleView.as_view(), name="refund-sale"),
    path("sales/summary/", SalesSummaryView.as_view()),
    path("sales/report-range/", SalesReportByRangeView.as_view()),
    path("sales/top-items/", TopItemsView.as_view()),

]
