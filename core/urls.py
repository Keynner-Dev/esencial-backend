from django.urls import path
from .views import (
    CatalogsView,
    AccountsListView,
    LedgerDailySummaryView,
    CreateLedgerTransactionView,
    TransactionListView,
    AccountBalanceView,
    CreateLoanView,
    PayLoanView,
    LoanListView,
)

urlpatterns = [
    # Catálogos
    path("catalogs/", CatalogsView.as_view(), name="catalogs"),

    # Cuentas y caja
    path("accounts/", AccountsListView.as_view(), name="accounts"),
    path("ledger/summary/", LedgerDailySummaryView.as_view(), name="ledger-summary"),
    path("accounts/balance/", AccountBalanceView.as_view(), name="accounts-balance"),

    # Transacciones
    path("ledger/transactions/", TransactionListView.as_view(), name="tx-list"),
    path("ledger/transactions/create/", CreateLedgerTransactionView.as_view(), name="tx-create"),

    # Préstamos
    path("loans/", LoanListView.as_view(), name="loan-list"),
    path("loans/create/", CreateLoanView.as_view(), name="loan-create"),
    path("loans/<int:loan_id>/pay/", PayLoanView.as_view(), name="loan-pay"),
]