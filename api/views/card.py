from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from api.models import Card
from api.serializers import CardSerializer

class CardPagination(PageNumberPagination):
    page_size = 30 
    page_size_query_param = 'limit'
    max_page_size = 100

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CardPagination

    def get_queryset(self):
        queryset = Card.objects.select_related("set").prefetch_related("prices").all()

        query = self.request.query_params.get('q', '')
        set_name = self.request.query_params.get('set', '')
        rarity = self.request.query_params.get('rarity', '')

        if query:
            queryset = queryset.filter(name__icontains=query)
        if set_name:
            queryset = queryset.filter(set__title__icontains=set_name)
        if rarity:
            queryset = queryset.filter(rarity=rarity)

        return queryset

    @action(detail=False, methods=["get"], url_path="search", pagination_class=CardPagination)
    def search(self, request):
        query = request.query_params.get('q', '')
        set_name = request.query_params.get('set', '')
        rarity = request.query_params.get('rarity', '')

        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(name__icontains=query)
        if set_name:
            queryset = queryset.filter(set__title__icontains=set_name)
        if rarity:
            queryset = queryset.filter(rarity=rarity)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="rarities")
    def get_rarities(self, request):
        rarities = Card.objects.values_list('rarity', flat=True).distinct().exclude(rarity__isnull=True).order_by('rarity')
        return Response(list(rarities))

    @action(detail=False, methods=["get"], url_path="sets")
    def get_sets(self, request):
        sets = Card.objects.select_related('set').values(
            'set__id', 'set__title'
        ).distinct().exclude(
            set__isnull=True
        ).order_by('set__title')

        result = [{'id': s['set__id'], 'title': s['set__title']} for s in sets]
        return Response(result)
