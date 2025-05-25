from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission
from api.models import News
from api.serializers import NewsSerializer

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Lecture autorisée à tous (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True
        # Création, modification, suppression => admin uniquement
        return request.user and request.user.is_staff

class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
