from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Favorites
from api.serializers import FavoritesSerializer
from django.db.models import Count
from django.core.exceptions import ValidationError

class FavoritesViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les cartes favorites d'un utilisateur.
    """
    serializer_class = FavoritesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Retourne seulement les favoris de l'utilisateur connecté.
        """
        return Favorites.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Ajoute une carte aux favoris en vérifiant la limite de 10.
        """
        try:
            serializer.save()
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """
        Retourne le nombre de favoris de l'utilisateur et la limite maximum.
        """
        count = self.get_queryset().count()
        return Response({
            'count': count,
            'max_allowed': 10,
            'remaining': 10 - count
        })