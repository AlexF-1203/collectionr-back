from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Card, Collection, User
from .serializers import CardSerializer, CollectionSerializer, UserSerializer

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def search(self, request):
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

class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def stats(self, request):
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

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action == 'create':  # Pour l'inscription
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAuthenticated]  # Pour les autres actions
        return super().get_permissions()
