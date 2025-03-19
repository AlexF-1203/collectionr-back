from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

# Plus besoin de définir le routeur ici puisqu'il est déjà défini dans api/urls.py
# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # Inclure les URLs de l'application api
    path('api-auth/', include('rest_framework.urls')),
] 