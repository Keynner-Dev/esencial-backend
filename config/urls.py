from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("users.urls")),
    path("api/", include("core.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("perfume.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

]

