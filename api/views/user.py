from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAdminUser
from api.models import User
from api.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les utilisateurs.
    Différentes permissions selon l'action.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Permissions basées sur l'action:
        - list, retrieve, destroy: admin seulement
        - create: tout le monde (inscription)
        - autres: utilisateur authentifié
        """
        if self.action in ['list', 'retrieve', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action == 'create':  # Pour l'inscription
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAuthenticated]  # Pour les autres actions
        return super().get_permissions()