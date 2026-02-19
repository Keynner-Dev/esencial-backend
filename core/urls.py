from django.urls import path
from .views import AccountsListView, LedgerDailySummaryView

urlpatterns = [
    path("accounts/", AccountsListView.as_view(), name="accounts"),
    path("ledger/summary/", LedgerDailySummaryView.as_view(), name="ledger-summary"),
    path("loans/create/", CreateLoanView.as_view()),

]
