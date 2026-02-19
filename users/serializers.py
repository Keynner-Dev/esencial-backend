from rest_framework import serializers
from .models import User

class MeSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "is_active", "groups", "permissions"]

    def get_groups(self, obj):
        return [g.name for g in obj.groups.all()]

    def get_permissions(self, obj):
        # devuelve codenames de permisos (incluye can_refund si aplica)
        return list(obj.get_all_permissions())
