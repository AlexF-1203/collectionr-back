# Ce fichier est maintenu pour la compatibilité avec le code existant
# Il importe tous les modèles depuis le package models

from .models.user import User
from .models.card import Card
from .models.collection import Collection
from .models.set import Set
from .models.favorites import Favorites

__all__ = ['User', 'Card', 'Collection', 'Set', 'Favorites']