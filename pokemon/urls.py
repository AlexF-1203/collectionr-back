from django.urls import path
from .views import PokemonCardView

urlpatterns = [
    path('pokemon/cards/', PokemonCardView.as_view(), name='pokemon-cards'),
] 