"""
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

from api.models import Card, CardPrice, Set as DjangoSet
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

def import_cards_to_db(cards_data, clear_existing=True):
    rarity_mapping = {
        'Common': 'COMMON',
        'Uncommon': 'UNCOMMON',
        'Rare': 'RARE',
        'Rare Holo': 'HOLORARE',
        'Rare Holo GX': 'HOLORAREGX',
        'Rare Holo EX': 'HOLORAREEX',
        'Rare Holo LV.X': 'HOLORARELVX',
        'Rare Holo Star': 'HOLORARESTARRARE',
        'Rare BREAK': 'BREAKRARE',
        'Rare Prime': 'PRIMERARE',
        'Rare Prism Star': 'PRISMRARE',
        'Rare Rainbow': 'RAINBOWRARE',
        'Rare Shining': 'SHININGRARE',
        'Rare Shiny': 'SHINYRARE',
        'Rare Shiny GX': 'SHINYRAREGX',
        'Rare Ultra': 'ULTRARARE',
        'Rare ACE': 'ACERARE',
        'Rare Secret': 'SECRETRARE',
        'Rare Holo V': 'HOLORAREV',
        'Rare Holo VMAX': 'HOLORAREVMAX',
        'Rare Holo VSTAR': 'HOLORAREVSTAR',
        'Rare Illustration Rare': 'ILLUSTRATIONRARE',
        'Rare Special Illustration Rare': 'SPECIALILLUSTRATIONRARE',
        'Rare Double Rare': 'DOUBLERARE',
        'Rare Triple Rare': 'TRIPLERAARE',
        'Promo': 'PROMO',
        'LEGEND': 'LEGENDRARE',
        'None': 'UNKNOWN'
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
            number = card_data.get('number', '0')
            original_rarity = card_data.get('rarity', 'Common')
            rarity = rarity_mapping.get(original_rarity, 'COMMON')
            image_url = card_data.get('images', {}).get('large', '')

            set_id = card_data.get('set_id')
            set_title = card_data.get('set_name', set_id)
            release_date = card_data.get('release_date')

            try:
                release_date = datetime.strptime(release_date, '%Y/%m/%d').date()
            except:
                release_date = base_date + timedelta(days=random.randint(0, 365))

            set_obj, _ = DjangoSet.objects.get_or_create(
                code=set_id,
                defaults={
                    'title': set_title,
                    'tcg': 'pokemon',
                    'release_date': release_date,
                    'total_cards': 0,
                    'image_url': '',
                    'symbol_url': ''
                }
            )

            # ===> Estimation du prix
            price = 0.99
            if 'prices' in card_data and card_data['prices']:
                prices = card_data['prices']
                for tier in ['normal', 'holofoil']:
                    if tier in prices and isinstance(prices[tier], dict):
                        if 'market' in prices[tier]:
                            price = float(prices[tier]['market'])
                            break
                        elif 'mid' in prices[tier]:
                            price = float(prices[tier]['mid'])
                            break
                if price <= 0:
                    price = round(random.uniform(0.1, 5.0), 2)

            card, created = Card.objects.update_or_create(
                set=set_obj,
                number=number,
                defaults={
                    'name': name,
                    'rarity': rarity,
                    'image_url': image_url,
                    'price': Money(price, 'USD'),
                    'description': f"Pokemon card from {set_title} set",
                    'release_date': release_date
                }
            )

            # ===> CardMarket Prices
            cardmarket_data = card_data.get('cardmarket', {})
            if cardmarket_data and 'prices' in cardmarket_data:
                prices = cardmarket_data['prices']
                avg1 = round(float(prices.get('avg1', 0) or 0), 2)
                avg7 = round(float(prices.get('avg7', 0) or 0), 2)
                avg30 = round(float(prices.get('avg30', 0) or 0), 2)
            else:
                base_price = price
                variation_percent = 0.15
                avg1 = round(base_price * (1 + random.uniform(-variation_percent / 3, variation_percent / 3)), 2)
                avg7 = round(base_price * (1 + random.uniform(-variation_percent / 2, variation_percent / 2)), 2)
                avg30 = round(base_price * (1 + random.uniform(-variation_percent, variation_percent)), 2)

            CardPrice.objects.update_or_create(
                card=card,
                defaults={
                    'avg1': avg1,
                    'avg7': avg7,
                    'avg30': avg30,
                    'daily_price': {}
                }
            )

            if created:
                created_count += 1
                print(f"✓ Créée: {name} ({set_title} #{number})")
            else:
                updated_count += 1
                print(f"✓ Mise à jour: {name} ({set_title} #{number})")

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
