from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from pokemon.views import PokemonCardView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

# Créer une sous-classe pour personnaliser les permissions
class TokenObtainPairView(BaseTokenObtainPairView):
    permission_classes = [AllowAny]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api-auth/", include("rest_framework.urls")),
    path('pokemon/cards/', PokemonCardView.as_view(), name='pokemon-cards'),
    path('api/', include('pokemon.urls')),
]
