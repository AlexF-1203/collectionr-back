from django.contrib import admin
from django.urls import path, include
from pokemon.views import PokemonCardView
from rest_framework.permissions import AllowAny
from api.views.user import CustomTokenObtainPairView, CustomTokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path("api-auth/", include("rest_framework.urls")),

    path('pokemon/cards/', PokemonCardView.as_view(), name='pokemon-cards'),
    path('api/', include('pokemon.urls')),
]
