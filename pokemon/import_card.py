"""
Script pour importer manuellement les cartes Pokémon depuis le fichier JSON vers la base de données
Utilisation: python import_cards.py [--clear] [--file FILEPATH]
"""

import os
import sys
import json
import django
import argparse
from datetime import datetime, timedelta
import random

# Configurer Django pour être utilisé en dehors d'un projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importer les modèles après avoir configuré Django
from api.models import Card
from djmoney.money import Money
from django.utils import timezone

def main():
    parser = argparse.ArgumentParser(description='Importe les cartes Pokémon dans la base de données')
    parser.add_argument('--clear', action='store_true', help='Supprimer les cartes existantes avant l\'import')
    parser.add_argument('--file', type=str, help='Chemin vers le fichier JSON', 
                       default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seeds', 'pokemon_cards_seed.json'))
    
    args = parser.parse_args()
    
    # Supprimer les cartes existantes si demandé
    if args.clear:
        print('Suppression des cartes existantes...')
        count = Card.objects.all().count()
        Card.objects.all().delete()
        print(f'✓ {count} cartes supprimées')
    
    # Charger les données depuis le fichier JSON
    print(f'Chargement des données depuis {args.file}...')
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            cards_data = json.load(f)
    except Exception as e:
        print(f'Erreur lors du chargement du fichier: {str(e)}')
        return
    
    # Mapping de la rareté
    rarity_mapping = {
        'Common': 'COMMON',
        'Uncommon': 'UNCOMMON',
        'Rare': 'RARE',
        'Rare Holo': 'HOLORARE',
        'Rare Ultra': 'ULTRARARE',
        'Rare Secret': 'SECRETRARE',
        # Ajoutez d'autres mappings si nécessaire
    }
    
    # Date de référence pour les release_date (1 an en arrière)
    base_date = timezone.now() - timedelta(days=365)
    
    # Importation des cartes
    print('Importation des cartes dans la base de données...')
    count = 0
    errors = 0
    
    for card_data in cards_data:
        try:
            # On vérifie si la carte existe déjà (par set et numéro)
            if card_data.get('set') and card_data.get('number'):
                # Convertir la rareté au format du modèle si possible
                rarity = rarity_mapping.get(card_data.get('rarity', ''), 'COMMON')
                
                # Générer une date de sortie aléatoire si elle n'est pas présente
                if card_data.get('release_date'):
                    try:
                        release_date = datetime.strptime(card_data['release_date'], '%Y/%m/%d').date()
                    except:
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
            print(f'Erreur lors de l\'importation de la carte: {str(e)}')
            errors += 1
    
    print(f'✓ {count} cartes importées dans la base de données')
    if errors > 0:
        print(f'⚠ {errors} erreurs rencontrées')

if __name__ == '__main__':
    main()