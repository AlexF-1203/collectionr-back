from pokemontcgsdk import Card, Set, RestClient
from typing import List, Dict
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de l'API
API_KEY = os.getenv('POKEMON_TCG_API_KEY')
if not API_KEY:
    raise ValueError("La clé API Pokémon TCG n'est pas configurée. Veuillez définir POKEMON_TCG_API_KEY dans votre fichier .env")

RestClient.configure(API_KEY)

class PokemonCardManager:
    def __init__(self):
        self.cards_data = []
        
    def extract_card_info(self, card_id: str) -> Dict:
        """
        Extrait les informations d'une carte spécifique
        Args:
            card_id: Identifiant de la carte (ex: 'swsh45sv-SV110')
        Returns:
            Dict: Informations formatées de la carte
        """
        try:
            card = Card.find(card_id)
            return {
                'id': card.id,
                'set': card.set.id,
                'name': card.name,
                'supertype': card.supertype,
                'subtypes': card.subtypes,
                'types': card.types,
                'number': card.number,
                'rarity': card.rarity,
                'images': {
                    'small': card.images.small,
                    'large': card.images.large
                }
            }
        except Exception as e:
            print(f"Erreur lors de l'extraction de la carte {card_id}: {str(e)}")
            return None

    def get_set_cards(self, set_id: str) -> List[Dict]:
        """
        Récupère toutes les cartes d'un set spécifique
        Args:
            set_id: Identifiant du set (ex: 'swsh45sv')
        Returns:
            List[Dict]: Liste des cartes du set
        """
        try:
            cards = Card.where(q=f'set.id:{set_id}')
            return [self.extract_card_info(card.id) for card in cards]
        except Exception as e:
            print(f"Erreur lors de la récupération du set {set_id}: {str(e)}")
            return []

    def generate_seed_data(self, set_ids: List[str]) -> None:
        """
        Génère les données seed pour les sets spécifiés
        Args:
            set_ids: Liste des identifiants de sets
        """
        for set_id in set_ids:
            cards = self.get_set_cards(set_id)
            self.cards_data.extend(cards)

    def export_to_json(self, filename: str = None) -> None:
        """
        Exporte les données vers un fichier JSON
        Args:
            filename: Nom du fichier de sortie
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'pokemon_cards_seed_{timestamp}.json'
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.cards_data, f, indent=2) 