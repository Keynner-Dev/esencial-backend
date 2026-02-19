from rest_framework.permissions import BasePermission

class IsAdminGroup(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name="ADMIN").exists()

class IsSellerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=["ADMIN", "SELLER"]).exists()

class CanRefundOrAdmin(BasePermission):
    """
    Permite refund a:
    - ADMIN
    - o quien tenga permiso sales.can_refund
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.groups.filter(name="ADMIN").exists():
            return True
        return request.user.has_perm("sales.can_refund")
