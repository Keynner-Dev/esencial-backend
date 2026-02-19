from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSellerOrAdmin
from .models import Product
from .serializers import ProductSerializer


class ProductListView(ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]
