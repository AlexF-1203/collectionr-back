from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import User, Collection, Card, Favorites, Set
from api.serializers import UserSerializer, SetSerializer
from django.db.models import Sum, Count
import logging

logger = logging.getLogger(__name__)

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
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Récupère les informations de profil de l'utilisateur connecté
        """
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'profilePicture': user.profile_picture.url if user.profile_picture else None
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile_data(self, request):
        """
        Récupère les données détaillées du profil utilisateur (collections, favoris, etc.)
        """
        user = request.user
        
        try:
            # Calcul des cartes totales dans la collection
            total_cards = Collection.objects.filter(user=user).aggregate(
                Sum('quantity')
            ).get('quantity__sum', 0) or 0
            
            # Récupérer le nombre de sets
            sets_count = Collection.objects.filter(user=user).values('card__set_name').distinct().count()
            
            # Récupérer les favoris
            favorite_cards = []
            favorites = Favorites.objects.filter(user=user).order_by('-created_at')
            
            for favorite in favorites:
                card = favorite.card
                favorite_cards.append({
                    'id': card.id,
                    'name': card.name,
                    'set': card.set_name,
                    'image': card.image_url,
                    'tcg': 'pokemon',  # Ajouter la détection automatique si nécessaire
                    'currentPrice': float(card.price.amount),
                    'priceChange': 0,  # À implémenter pour calculer le changement de prix
                    'setCompletion': 0,  # À implémenter pour calculer le taux de complétion
                    'collectionName': card.set_name,
                    'createdAt': favorite.created_at.isoformat()
                })
            
            # Récupérer l'activité récente (dernières cartes ajoutées)
            recent_cards = []
            recent_collections = Collection.objects.filter(user=user).order_by('-acquired_date')[:5]
            
            for collection in recent_collections:
                card = collection.card
                recent_cards.append({
                    'id': card.id,
                    'name': card.name,
                    'set': card.set_name,
                    'image': card.image_url,
                    'tcg': 'pokemon',  # Ajouter la détection automatique si nécessaire
                    'currentPrice': float(card.price.amount),
                    'priceChange': 0,  # À implémenter pour calculer le changement de prix
                    'isFavorite': Favorites.objects.filter(user=user, card=card).exists(),
                    'setCompletion': 0,  # À implémenter pour calculer le taux de complétion
                    'collectionName': card.set_name,
                    'acquiredDate': collection.acquired_date.isoformat()
                })
            
            # Récupérer les collections (sets)
            collections = {
                'pokemon': [],
                'yugioh': []
            }
            
            logger.info(f"Récupération des sets pour l'utilisateur {user.username}")
            
            # Récupérer les sets directement depuis le modèle Set
            user_sets = Set.objects.filter(user=user)
            logger.info(f"Nombre de sets trouvés dans le modèle Set: {user_sets.count()}")
            
            # Convertir les sets en format attendu par le frontend
            for set_obj in user_sets:
                # Calculer le nombre de cartes possédées dans ce set
                owned_cards = Collection.objects.filter(
                    user=user, 
                    card__set_name=set_obj.code
                ).count()
                
                # Calculer le nombre total de cartes dans ce set
                total_in_set = Card.objects.filter(set_name=set_obj.code).count()
                
                # Calculer le pourcentage de complétion
                progress = int((owned_cards / total_in_set) * 100) if total_in_set > 0 else 0
                
                logger.info(f"Set trouvé (modèle Set): {set_obj.title}, cartes: {owned_cards}/{total_in_set}")
                
                collections['pokemon'].append({
                    'id': set_obj.id,
                    'title': set_obj.title,
                    'ownedCards': owned_cards,
                    'totalCards': total_in_set,
                    'progress': progress,
                    'imageUrl': set_obj.image_url,
                    'releaseDate': set_obj.release_date.strftime('%Y-%m-%d') if set_obj.release_date else ''
                })
            
            # Si aucun set n'a été trouvé, essayer l'ancienne méthode
            if not collections['pokemon']:
                logger.info("Aucun set trouvé dans le modèle Set, utilisation de la méthode alternative")
                
                pokemon_sets = Collection.objects.filter(user=user).values('card__set_name').annotate(
                    cards_count=Count('card', distinct=True)
                )
                
                logger.info(f"Nombre de sets trouvés via collections: {pokemon_sets.count()}")
                
                for pokemon_set in pokemon_sets:
                    set_name = pokemon_set['card__set_name']
                    owned_cards = pokemon_set['cards_count']
                    total_in_set = Card.objects.filter(set_name=set_name).count()
                    progress = int((owned_cards / total_in_set) * 100) if total_in_set > 0 else 0
                    
                    set_card = Card.objects.filter(set_name=set_name).first()
                    
                    logger.info(f"Set trouvé via collections: {set_name}, cartes: {owned_cards}/{total_in_set}")
                    
                    collections['pokemon'].append({
                        'title': set_name,
                        'ownedCards': owned_cards,
                        'totalCards': total_in_set,
                        'progress': progress,
                        'imageUrl': set_card.image_url if set_card else '',
                        'releaseDate': set_card.release_date.strftime('%Y-%m-%d') if set_card and set_card.release_date else ''
                    })
            
            collection_value = Collection.objects.filter(user=user).aggregate(
                value=Sum('card__price')
            ).get('value', 0) or 0
            
            total_cards_available = Card.objects.count()
            collection_progress = int((total_cards / total_cards_available) * 100) if total_cards_available > 0 else 0
            
            # Ajouter les sets directement dans la réponse
            sets = []
            for set_obj in user_sets:
                sets.append({
                    'id': set_obj.id,
                    'title': set_obj.title,
                    'code': set_obj.code,
                    'tcg': set_obj.tcg,
                    'releaseDate': set_obj.release_date.strftime('%Y-%m-%d') if set_obj.release_date else '',
                    'totalCards': set_obj.total_cards,
                    'imageUrl': set_obj.image_url
                })
            
            return Response({
                'totalCards': total_cards,
                'cardsBySets': sets_count,
                'favoriteCards': favorite_cards,
                'recentCards': recent_cards,
                'collections': collections,
                'sets': sets,  # Ajouter les sets directement
                'collectionValue': float(collection_value),
                'collectionProgress': collection_progress
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de profil: {str(e)}")
            return Response(
                {"error": "Une erreur est survenue lors de la récupération des données"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )