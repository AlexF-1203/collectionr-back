from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Set, Card
from api.serializers import SetSerializer, CardSerializer


class SetViewSet(viewsets.ModelViewSet):
    serializer_class = SetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Set.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def cards(self, request, pk=None):
        set_obj = self.get_object()
        cards = Card.objects.filter(set_name=set_obj.code)
        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def available(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)