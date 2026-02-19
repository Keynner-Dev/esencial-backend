from django.urls import path
from .views import POSView, RefundSaleView

urlpatterns = [
    path("sales/pos/", POSView.as_view(), name="pos-sale"),
    path("sales/<int:sale_id>/refund/", RefundSaleView.as_view(), name="refund-sale"),
    path("sales/summary/", SalesSummaryView.as_view()),

]
