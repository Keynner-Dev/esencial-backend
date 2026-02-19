from django.urls import path
from .views import FragranceListView, PresentationListView

urlpatterns = [
    path("fragrances/", FragranceListView.as_view()),
    path("presentations/", PresentationListView.as_view()),
]
