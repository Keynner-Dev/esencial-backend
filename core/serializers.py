from rest_framework import serializers
from .models import Account, Transaction

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "type", "is_active"]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id", "created_at", "created_by", "type", "category",
            "description", "amount", "from_account", "to_account",
            "reference_type", "reference_id"
        ]
        read_only_fields = ["created_at", "created_by"]
