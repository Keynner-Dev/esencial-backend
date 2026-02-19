from rest_framework import serializers
from .models import Fragrance, Presentation


class FragranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fragrance
        fields = ["id", "name"]


class PresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = ["id", "name", "ml"]
