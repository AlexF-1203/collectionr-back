from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import User, Collection, Card, Favorites, Set, UserSet
from api.serializers import UserSerializer, SetSerializer
from django.db.models import Sum, Count
import logging
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les utilisateurs.
    Différentes permissions selon l'action.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    permission_classes = [AllowAny]

    def get_permissions(self):
        """
        Permissions basées sur l'action:
        - list, retrieve, destroy: admin seulement
        - create: tout le monde (inscription)
        - autres: utilisateur authentifié
        """
        logger.info(f"Action demandée: {self.action}")

        if self.action in ['list', 'retrieve', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action == 'create':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]

        logger.info(f"Permissions appliquées: {self.permission_classes}")
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Créer un nouvel utilisateur et journaliser l'opération
        """
        logger.info(f"Tentative de création d'utilisateur avec les données: {request.data}")
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return Response(
                {"detail": f"Erreur lors de la création de l'utilisateur: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        user = request.user

        if request.method == 'GET':
            return Response({
                'id': user.id,
                'profilePicture': user.profile_picture.url if user.profile_picture else None,
                'username': user.username,
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
            })

        elif request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        print("FILES:", request.FILES)
        print("DATA:", request.data)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile_data(self, request):
        """
        Récupère les données détaillées du profil utilisateur (collections, favoris, etc.)
        """
        user = request.user

        try:
            total_cards = Collection.objects.filter(user=user).aggregate(
                Sum('quantity')
            ).get('quantity__sum', 0) or 0

            sets_count = Collection.objects.filter(user=user).values('card__set').distinct().count()

            favorite_cards = []
            favorites = Favorites.objects.filter(user=user).order_by('-created_at')

            for favorite in favorites:
                card = favorite.card
                favorite_cards.append({
                    'id': card.id,
                    'name': card.name,
                    'set': {
                        'code': card.set.code,
                        'title': card.set.title,
                    },
                    'image': card.image_url,
                    'tcg': 'pokemon',
                    'currentPrice': float(card.price.amount),
                    'priceChange': 0,
                    'setCompletion': 0,
                    'collectionName': card.set.title,
                    'createdAt': favorite.created_at.isoformat(),
                    'favoriteId': favorite.id
                })

            recent_cards = []
            recent_collections = Collection.objects.filter(user=user).order_by('-acquired_date')[:5]

            for collection in recent_collections:
                card = collection.card
                recent_cards.append({
                    'id': card.id,
                    'name': card.name,
                    'set': {
                        'code': card.set.code,
                        'title': card.set.title,
                    },
                    'image': card.image_url,
                    'tcg': 'pokemon',
                    'currentPrice': float(card.price.amount),
                    'priceChange': 0,
                    'isFavorite': Favorites.objects.filter(user=user, card=card).exists(),
                    'setCompletion': 0,
                    'collectionName': card.set.title,
                    'acquiredDate': collection.acquired_date.isoformat()
                })

            # Sets via UserSet
            collections = {'pokemon': []}
            logger.info(f"Récupération des UserSet pour l'utilisateur {user.username}")

            user_sets = UserSet.objects.filter(user=user).select_related('set')
            logger.info(f"Nombre de UserSet trouvés: {user_sets.count()}")

            for user_set in user_sets:
                set_obj = user_set.set
                collections['pokemon'].append({
                    'id': set_obj.id,
                    'title': set_obj.title,
                    'ownedCards': user_set.card_count,
                    'totalCards': user_set.total_cards,
                    'progress': int(user_set.completion),
                    'imageUrl': set_obj.image_url,
                    'releaseDate': set_obj.release_date.strftime('%Y-%m-%d') if set_obj.release_date else ''
                })

            # Valeur totale de la collection
            collection_value = Collection.objects.filter(user=user).aggregate(
                value=Sum('card__price')
            ).get('value', 0) or 0

            # Progression de la collection en % sur toutes les cartes
            total_cards_available = Card.objects.count()
            collection_progress = int((total_cards / total_cards_available) * 100) if total_cards_available > 0 else 0

            # Format simplifié des sets (si nécessaire côté front)
            sets = [{
                'id': user_set.set.id,
                'title': user_set.set.title,
                'code': user_set.set.code,
                'tcg': user_set.set.tcg,
                'releaseDate': user_set.set.release_date.strftime('%Y-%m-%d') if user_set.set.release_date else '',
                'totalCards': user_set.total_cards,
                'imageUrl': user_set.set.image_url,
                'ownedCards': user_set.card_count,
                'progress': int(user_set.completion),
            } for user_set in user_sets]

            return Response({
                'totalCards': total_cards,
                'cardsBySets': sets_count,
                'favoriteCards': favorite_cards,
                'recentCards': recent_cards,
                'collections': collections,
                'sets': sets,
                'collectionValue': float(collection_value),
                'collectionProgress': collection_progress
            })

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de profil: {str(e)}")
            return Response(
                {"error": "Une erreur est survenue lors de la récupération des données"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.set_cookie(
                'access_token',
                response.data['access'],
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60*15
            )
            response.set_cookie(
                'refresh_token',
                response.data['refresh'],
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60*60*24
            )
            del response.data['access']
            del response.data['refresh']
        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            response.set_cookie(
                'access_token',
                response.data['access'],
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60*15
            )

            del response.data['access']

        return response

class LogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Déconnexion réussie"})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
