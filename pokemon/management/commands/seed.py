from django.core.management.base import BaseCommand
from pokemon.card_manager import PokemonCardManager
from api.models import Card
from django.utils.dateparse import parse_date
from django.utils import timezone
from djmoney.money import Money
import json
import os
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Seeds the database with Pokémon cards from the TCG API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sets',
            nargs='+',
            type=str,
            help='List of set IDs to fetch (e.g. swsh45sv swsh9)',
            default=['swsh45sv', 'swsh9']
        )
        parser.add_argument(
            '--json-only',
            action='store_true',
            help='Only generate JSON file without seeding database'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing cards before seeding'
        )

    def handle(self, *args, **options):
        # Récupération des arguments
        target_sets = options['sets']
        json_only = options['json_only']
        clear = options['clear']

        # Création du gestionnaire
        manager = PokemonCardManager()
        
        # Nettoyage des cartes existantes si demandé
        if clear and not json_only:
            self.stdout.write(self.style.WARNING('Suppression des cartes existantes...'))
            count = Card.objects.all().count()
            Card.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✓ {count} cartes supprimées'))

        # Génération des données
        self.stdout.write(self.style.NOTICE('Génération des données seed...'))
        manager.generate_seed_data(target_sets)
        
        # Export des données en JSON
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'seeds')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, 'pokemon_cards_seed.json')
        manager.export_to_json(output_file)
        self.stdout.write(self.style.SUCCESS(f'✓ Données exportées vers {output_file}'))
        
        
        if not json_only:
            self.stdout.write(self.style.NOTICE('Importation des cartes dans la base de données...'))
            cards_created = self._seed_database(manager.cards_data)
            self.stdout.write(self.style.SUCCESS(f'✓ {cards_created} cartes importées dans la base de données'))

    def _seed_database(self, cards_data):
        """
        Importe les cartes dans la base de données
        """
        count = 0
        rarity_mapping = {
            'Common': 'COMMON',
            'Uncommon': 'UNCOMMON',
            'Rare': 'RARE',
            'Rare Holo': 'HOLORARE',
            'Rare Ultra': 'ULTRARARE',
            'Rare Secret': 'SECRETRARE',
            'Amazing Rare': 'ULTRARARE',
            'Promo': 'UNCOMMON',
            'Classic Collection': 'SECRETRARE',
            'Radiant Rare': 'ULTRARARE',
            'Illustration Rare': 'HOLORARE',
            'Special Illustration Rare': 'ULTRARARE',
            'Hyper Rare': 'SECRETRARE',
            'Trainer Gallery Rare Holo': 'HOLORARE',
            'Trainer Gallery Rare Ultra': 'ULTRARARE',
            'V': 'ULTRARARE',
            'VMAX': 'ULTRARARE',
            'VSTAR': 'ULTRARARE',
        }
        
        # Date de référence pour les release_date (1 an en arrière)
        base_date = timezone.now() - timedelta(days=365)
        
        for card_data in cards_data:
            try:
                # On vérifie si la carte existe déjà (par set et numéro)
                if card_data.get('set') and card_data.get('number'):
                    # Convertir la rareté au format du modèle si possible
                    original_rarity = card_data.get('rarity', 'Common')
                    rarity = rarity_mapping.get(original_rarity, 'COMMON')
                    
                    # Générer une date de sortie aléatoire si elle n'est pas présente
                    if card_data.get('release_date'):
                        try:
                            release_date = datetime.strptime(card_data['release_date'], '%Y/%m/%d').date()
                        except (ValueError, TypeError):
                            release_date = base_date + timedelta(days=random.randint(0, 365))
                    else:
                        release_date = base_date + timedelta(days=random.randint(0, 365))
                    
                    # Générer un prix aléatoire basé sur la rareté
                    price_mapping = {
                        'COMMON': (0.1, 1.0),
                        'UNCOMMON': (0.5, 2.5),
                        'RARE': (1.0, 5.0),
                        'HOLORARE': (3.0, 15.0),
                        'ULTRARARE': (10.0, 50.0),
                        'SECRETRARE': (20.0, 100.0)
                    }
                    price_range = price_mapping.get(rarity, (0.1, 1.0))
                    price = round(random.uniform(*price_range), 2)
                    
                    # Vérifier si des prix sont disponibles dans les données de la carte
                    if 'prices' in card_data and card_data['prices']:
                        # Utiliser le premier prix disponible
                        for price_type, price_info in card_data['prices'].items():
                            if isinstance(price_info, dict) and 'market' in price_info:
                                price = price_info['market']
                                break
                            elif isinstance(price_info, dict) and 'mid' in price_info:
                                price = price_info['mid']
                                break
                    
                    # Créer ou mettre à jour la carte
                    set_name = card_data.get('set_name', card_data.get('set', 'Unknown'))
                    card, created = Card.objects.update_or_create(
                        set_name=set_name,
                        number=card_data.get('number', '0'),
                        defaults={
                            'name': card_data.get('name', 'Unknown Card'),
                            'rarity': rarity,
                            'image_url': card_data.get('images', {}).get('large', ''),
                            'price': Money(price, 'USD'),
                            'description': f"Pokemon card from {set_name} set",
                            'release_date': release_date
                        }
                    )
                    
                    if created:
                        count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de l\'importation de la carte: {str(e)}'))
        
        return count