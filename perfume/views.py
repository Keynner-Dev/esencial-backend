from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSellerOrAdmin
from .models import Fragrance, Presentation
from .serializers import FragranceSerializer, PresentationSerializer


class FragranceListView(ListAPIView):
    queryset = Fragrance.objects.all()
    serializer_class = FragranceSerializer
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]


class PresentationListView(ListAPIView):
    queryset = Presentation.objects.all()
    serializer_class = PresentationSerializer
    permission_classes = [IsAuthenticated, IsSellerOrAdmin]
