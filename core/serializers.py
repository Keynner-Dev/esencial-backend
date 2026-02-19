from rest_framework import serializers
from .models import Account, Transaction, Loan


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "type", "is_active"]


class TransactionSerializer(serializers.ModelSerializer):
    from_account_name = serializers.CharField(source="from_account.name", read_only=True)
    to_account_name = serializers.CharField(source="to_account.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "created_at",
            "created_by",
            "type",
            "category",
            "description",
            "amount",
            "from_account",
            "from_account_name",
            "to_account",
            "to_account_name",
            "reference_type",
            "reference_id",
        ]
        read_only_fields = ["id", "created_at", "created_by"]


class CreateTransactionSerializer(serializers.Serializer):
    """
    Para gastos/capital/transferencias/ajustes genéricos
    """
    type = serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    from_account_id = serializers.IntegerField(required=False, allow_null=True)
    to_account_id = serializers.IntegerField(required=False, allow_null=True)

    reference_type = serializers.CharField(required=False, allow_blank=True)
    reference_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["amount"] <= 0:
            raise serializers.ValidationError("amount debe ser > 0")

        t = attrs["type"]
        fa = attrs.get("from_account_id")
        ta = attrs.get("to_account_id")

        # reglas simples (puedes endurecerlas luego)
        if t in ["EXPENSE", "PURCHASE_OUTFLOW", "LOAN_PAYMENT"]:
            if not fa:
                raise serializers.ValidationError("from_account_id requerido para salidas.")
        if t in ["SALE_INCOME", "CAPITAL_IN", "LOAN_IN"]:
            if not ta:
                raise serializers.ValidationError("to_account_id requerido para entradas.")
        if t == "TRANSFER":
            if not fa or not ta:
                raise serializers.ValidationError("TRANSFER requiere from_account_id y to_account_id.")
            if fa == ta:
                raise serializers.ValidationError("TRANSFER no puede ser a la misma cuenta.")
        return attrs


class LoanSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "created_at", "lender_name", "total_amount", "remaining_amount", "account", "account_name"]


class CreateLoanSerializer(serializers.Serializer):
    lender_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    account_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs["amount"] <= 0:
            raise serializers.ValidationError("amount debe ser > 0")
        return attrs


class PayLoanSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    from_account_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs["amount"] <= 0:
            raise serializers.ValidationError("amount debe ser > 0")
        return attrs