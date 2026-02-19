from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("users.urls")),
    path("api/", include("core.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("perfume.urls")),

]
