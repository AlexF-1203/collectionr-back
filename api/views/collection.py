from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from api.models import Collection
from api.serializers import CollectionSerializer


class CollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer la collection de cartes d'un utilisateur.
    Inclut des statistiques sur la collection.
    """
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retourne seulement les collections de l'utilisateur connecté.
        """
        return Collection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Création d'une nouvelle entrée dans la collection.
        """
        serializer.save()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Fournit des statistiques sur la collection de l'utilisateur.
        """
        total_cards = self.get_queryset().aggregate(
            total=Sum('quantity')
        )['total'] or 0

        cards_by_rarity = self.get_queryset().values(
            'card__rarity'
        ).annotate(
            count=Sum('quantity')
        ).order_by('card__rarity')

        return Response({
            'total_cards': total_cards,
            'by_rarity': {
                item['card__rarity']: item['count']
                for item in cards_by_rarity
            }
        })