from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Card
from api.serializers import CardSerializer


class CardViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les cartes.
    Permet également la recherche de cartes par nom, set et rareté.
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Point de terminaison pour rechercher des cartes avec des filtres.
        """
        query = request.query_params.get('q', '')
        set_name = request.query_params.get('set', '')
        rarity = request.query_params.get('rarity', '')

        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(name__icontains=query)
        if set_name:
            queryset = queryset.filter(set_name__icontains=set_name)
        if rarity:
            queryset = queryset.filter(rarity=rarity)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)