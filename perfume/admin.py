from django.contrib import admin
from .models import Presentation, Fragrance, PresentationDose, AlcoholCostByPresentation


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ("name", "ml")


@admin.register(Fragrance)
class FragranceAdmin(admin.ModelAdmin):
    list_display = ("name", "essence_product")


@admin.register(PresentationDose)
class PresentationDoseAdmin(admin.ModelAdmin):
    list_display = ("presentation", "grams_essence", "extras_cost")


@admin.register(AlcoholCostByPresentation)
class AlcoholCostAdmin(admin.ModelAdmin):
    list_display = ("presentation", "alcohol_cost")
