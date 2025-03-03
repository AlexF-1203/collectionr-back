"""
Script pour importer des cartes Pokémon directement dans la DB.
Utilisation: python import_pokemon_cards.py
"""
import os
import sys
import json
import django
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Card, CardPrice
from django.utils import timezone
from djmoney.money import Money

from pokemontcgsdk import Card as PokemonCard, Set, RestClient

API_KEY = os.getenv('POKEMON_TCG_API_KEY')
if not API_KEY:
    print("Attention: La clé API Pokémon TCG n'est pas configurée.")
    print("Vous pouvez l'obtenir sur https://dev.pokemontcg.io/ et la définir avec:")
    print("export POKEMON_TCG_API_KEY=votre_clé_api")
RestClient.configure(API_KEY)

def get_cards_from_set(set_id):
    """
    Récupère toutes les cartes d'un set spécifique
    Args:
        set_id: Identifiant du set (ex: 'swsh45sv')
    Returns:
        list: Liste des cartes formatées
    """
    cards = []
    try:
        print(f"Récupération des cartes du set {set_id}...")
        pokemon_cards = PokemonCard.where(q=f'set.id:{set_id}')
        
        for card in pokemon_cards:
            card_data = {
                'id': card.id,
                'name': card.name,
                'set_name': card.set.name,
                'set_id': card.set.id,
                'number': card.number,
                'rarity': getattr(card, 'rarity', 'Common'),
                'images': {
                    'small': card.images.small,
                    'large': card.images.large
                }
            }
            
            # Récupération des prix TCGPlayer
            if hasattr(card, 'tcgplayer') and hasattr(card.tcgplayer, 'prices'):
                prices_dict = {}
                for price_type, price_obj in card.tcgplayer.prices.__dict__.items():
                    if price_obj is not None:
                        if hasattr(price_obj, '__dict__'):
                            formatted_price_dict = {}
                            for key, value in price_obj.__dict__.items():
                                if isinstance(value, (int, float)):
                                    formatted_price_dict[key] = round(float(value), 2)
                                else:
                                    formatted_price_dict[key] = value
                            prices_dict[price_type] = formatted_price_dict
                        else:
                            if isinstance(price_obj, (int, float)):
                                prices_dict[price_type] = round(float(price_obj), 2)
                            else:
                                prices_dict[price_type] = price_obj
                card_data['prices'] = prices_dict

            # Récupération des données cardmarket
            if hasattr(card, 'cardmarket') and hasattr(card.cardmarket, 'prices'):
                cardmarket_prices = {}
                for price_key, price_value in card.cardmarket.prices.__dict__.items():
                    if price_value is not None:
                        if isinstance(price_value, (int, float)):
                            cardmarket_prices[price_key] = round(float(price_value), 2)
                        else:
                            cardmarket_prices[price_key] = price_value

                card_data['cardmarket'] = {
                    'url': card.cardmarket.url,
                    'updatedAt': card.cardmarket.updatedAt,
                    'prices': cardmarket_prices
                }
            
            if hasattr(card.set, 'releaseDate'):
                card_data['release_date'] = card.set.releaseDate
            
            cards.append(card_data)
        
        print(f"✓ {len(cards)} cartes récupérées du set {set_id}")
        return cards
    
    except Exception as e:
        print(f"Erreur lors de la récupération du set {set_id}: {str(e)}")
        return []

def import_cards_to_db(cards_data, clear_existing=False):
    """
    Importe les cartes dans la base de données
    Args:
        cards_data: Liste des données de cartes
        clear_existing: Supprimer les cartes existantes
    """
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
    
    if clear_existing:
        print("Suppression des cartes existantes...")
        count = Card.objects.all().count()
        Card.objects.all().delete()
        print(f"✓ {count} cartes supprimées")
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    base_date = timezone.now().date() - timedelta(days=365)
    
    print("Importation des cartes dans la base de données...")
    for card_data in cards_data:
        try:
            name = card_data.get('name', 'Unknown Card')
            set_name = card_data.get('set_name', card_data.get('set_id', 'Unknown Set'))
            number = card_data.get('number', '0')
            
            original_rarity = card_data.get('rarity', 'Common')
            rarity = rarity_mapping.get(original_rarity, 'COMMON')
            
            image_url = card_data.get('images', {}).get('large', '')
        
            if 'release_date' in card_data and card_data['release_date']:
                try:
                    release_date = datetime.strptime(card_data['release_date'], '%Y/%m/%d').date()
                except (ValueError, TypeError):
                    release_date = base_date + timedelta(days=random.randint(0, 365))
            else:
                release_date = base_date + timedelta(days=random.randint(0, 365))
            
            price = 0.99  
            if 'prices' in card_data and card_data['prices']:
                if 'normal' in card_data['prices'] and card_data['prices']['normal']:
                    price_info = card_data['prices']['normal']
                    if isinstance(price_info, dict) and 'market' in price_info:
                        price = float(price_info['market'])
                    elif isinstance(price_info, dict) and 'mid' in price_info:
                        price = float(price_info['mid'])
                
                elif 'holofoil' in card_data['prices'] and card_data['prices']['holofoil']:
                    price_info = card_data['prices']['holofoil']
                    if isinstance(price_info, dict) and 'market' in price_info:
                        price = float(price_info['market'])
                    elif isinstance(price_info, dict) and 'mid' in price_info:
                        price = float(price_info['mid'])

                else:
                    for price_type, price_info in card_data['prices'].items():
                        if isinstance(price_info, dict) and 'market' in price_info:
                            price = float(price_info['market'])
                            break
                        elif isinstance(price_info, dict) and 'mid' in price_info:
                            price = float(price_info['mid'])
                            break

            if not price or price <= 0:
                price_range = {
                    'COMMON': (0.1, 1.0),
                    'UNCOMMON': (0.5, 2.5),
                    'RARE': (1.0, 5.0),
                    'HOLORARE': (3.0, 15.0),
                    'ULTRARARE': (10.0, 50.0),
                    'SECRETRARE': (20.0, 100.0)
                }.get(rarity, (0.1, 1.0))
                price = round(random.uniform(*price_range), 2)
            
            card, created = Card.objects.update_or_create(
                set_name=set_name,
                number=number,
                defaults={
                    'name': name,
                    'rarity': rarity,
                    'image_url': image_url,
                    'price': Money(price, 'USD'),
                    'description': f"Pokemon card from {set_name} set",
                    'release_date': release_date
                }
            )
            
            # Récupération des prix avg1, avg7, avg30 depuis cardmarket
            cardmarket_data = card_data.get('cardmarket', {})
            if cardmarket_data and 'prices' in cardmarket_data:
                prices = cardmarket_data['prices']
                avg1 = round(float(prices.get('avg1', 0) or 0), 2)
                avg7 = round(float(prices.get('avg7', 0) or 0), 2)
                avg30 = round(float(prices.get('avg30', 0) or 0), 2)
                print(f"Prix trouvés pour {name}: avg1={avg1:.2f}, avg7={avg7:.2f}, avg30={avg30:.2f}")
            else:
                print(f"Pas de données cardmarket pour {name}, utilisation de variations sur le prix de base")
                base_price = price
                variation_percent = 0.15
                avg1 = round(base_price * (1 + random.uniform(-variation_percent/3, variation_percent/3)), 2)
                avg7 = round(base_price * (1 + random.uniform(-variation_percent/2, variation_percent/2)), 2)
                avg30 = round(base_price * (1 + random.uniform(-variation_percent, variation_percent)), 2)

            # Créer ou mettre à jour CardPrice avec les valeurs trouvées
            card_price, price_created = CardPrice.objects.update_or_create(
                card=card,
                defaults={
                    'avg1': avg1,
                    'avg7': avg7,
                    'avg30': avg30,
                    'daily_price': {}  # Sera calculé automatiquement par calculate_daily_price
                }
            )

            if price_created:
                print(f"✓ Prix créé pour: {name} ({set_name} #{number})")
            else:
                print(f"✓ Prix mis à jour pour: {name} ({set_name} #{number})")

            if created:
                created_count += 1
                print(f"✓ Créée: {name} ({set_name} #{number})")
            else:
                updated_count += 1
                print(f"✓ Mise à jour: {name} ({set_name} #{number})")
                
        except Exception as e:
            error_count += 1
            print(f"✕ Erreur: {str(e)}")
    
    print(f"\nRésumé de l'importation:")
    print(f"✓ {created_count} cartes créées")
    print(f"✓ {updated_count} cartes mises à jour")
    if error_count > 0:
        print(f"✕ {error_count} erreurs rencontrées")
    

def main():
    TARGET_SETS = ['swsh45sv', 'swsh9', 'sm12']
    
    all_cards = []
    for set_id in TARGET_SETS:
        cards = get_cards_from_set(set_id)
        all_cards.extend(cards)
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seeds')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, 'pokemon_cards_seed.json')
    print(f"Sauvegarde des données en JSON dans {output_file}...")
    
    json_data = []
    for card in all_cards:
        json_data.append(card)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"✓ Données JSON sauvegardées")

    import_cards_to_db(all_cards, clear_existing=False)

if __name__ == "__main__":
    main()