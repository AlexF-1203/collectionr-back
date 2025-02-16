from rest_framework.views import APIView
from rest_framework.response import Response
from .card_manager import PokemonCardManager
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination

class PokemonPagination(PageNumberPagination):
    page_size = 5  # Nombre de cartes par page
    page_size_query_param = 'page_size'
    max_page_size = 20

class PokemonCardView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PokemonPagination

    def get(self, request):
        try:
            manager = PokemonCardManager()
            if not manager.cards_data:
                # Chargez les données depuis le fichier seed
                import json
                import os
                seed_path = os.path.join(os.path.dirname(__file__), '..', 'seeds', 'pokemon_cards_seed.json')
                with open(seed_path, 'r') as f:
                    manager.cards_data = json.load(f)
            
            paginator = self.pagination_class()
            paginated_cards = paginator.paginate_queryset(manager.cards_data, request)
            
            return paginator.get_paginated_response(paginated_cards)
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 