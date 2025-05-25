from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from pokemon.views import PokemonCardView
from rest_framework.permissions import AllowAny
from api.views.user import CustomTokenObtainPairView, CustomTokenRefreshView
from api.views.user_google import GoogleLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path("api-auth/", include("rest_framework.urls")),
    path('auth/api/login/google/', GoogleLoginView.as_view(), name='google-login'),

    path('pokemon/cards/', PokemonCardView.as_view(), name='pokemon-cards'),
    path('api/', include('pokemon.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
