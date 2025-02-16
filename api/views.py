from rest_framework import viewsets, permissions
from .serializers import UserSerializer
from rest_framework.permissions import IsAdminUser
from .models import User

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
