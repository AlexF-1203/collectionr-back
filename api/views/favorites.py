from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Favorites, Card
from api.serializers import FavoritesSerializer
from django.db.models import Count
from django.core.exceptions import ValidationError
import logging
import traceback

logger = logging.getLogger(__name__)

class FavoritesViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorites.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        try:
            serializer.save()
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        try:
            favorite_id = kwargs.get('pk')
            user = request.user
            
            logger.info("=== SUPPRESSION FAVORI DEMANDÉE ===")
            logger.info(f"User: {user.username} (ID: {user.id})")
            logger.info(f"Paramètre PK: {favorite_id}")
            
            all_favorites = self.get_queryset()
            logger.info(f"Tous les favoris de l'utilisateur ({all_favorites.count()}):")
            for fav in all_favorites:
                logger.info(f"  - Favori ID: {fav.id}, Carte ID: {fav.card.id}, Nom: {fav.card.name}")
            
            by_favorite_id = all_favorites.filter(id=favorite_id).first()
            by_card_id = all_favorites.filter(card__id=favorite_id).first()
            
            logger.info(f"Recherche par ID de favori: {by_favorite_id}")
            logger.info(f"Recherche par ID de carte: {by_card_id}")
            
            favorite = by_favorite_id or by_card_id
            
            if not favorite:
                try:
                    if isinstance(favorite_id, str) and favorite_id.isdigit():
                        numeric_id = int(favorite_id)
                        by_favorite_id_int = all_favorites.filter(id=numeric_id).first()
                        by_card_id_int = all_favorites.filter(card__id=numeric_id).first()
                        favorite = by_favorite_id_int or by_card_id_int
                        logger.info(f"Après conversion en entier - Favori trouvé: {favorite}")
                except Exception as conversion_error:
                    logger.error(f"Erreur lors de la conversion: {str(conversion_error)}")
            
            if not favorite:
                logger.warning(f"AUCUN FAVORI TROUVÉ pour {favorite_id}")
                return Response(
                    {"error": f"Favori non trouvé pour l'utilisateur {user.username}"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            logger.info(f"SUPPRESSION du favori ID={favorite.id} (carte: {favorite.card.name}, ID={favorite.card.id})")
            favorite.delete()
            logger.info(f"SUPPRESSION RÉUSSIE")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"ERREUR DE SUPPRESSION: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Erreur lors de la suppression: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        count = self.get_queryset().count()
        return Response({
            'count': count,
            'max_allowed': 10,
            'remaining': 10 - count
        })