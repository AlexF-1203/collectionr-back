import os
import sys
import json
import django
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Set
from django.utils import timezone

from pokemontcgsdk import Set as PokemonSet, RestClient

API_KEY = os.getenv('POKEMON_TCG_API_KEY')
if not API_KEY:
    print("Attention: La clé API Pokémon TCG n'est pas configurée.")
    print("Vous pouvez l'obtenir sur https://dev.pokemontcg.io/ et la définir avec:")
    print("export POKEMON_TCG_API_KEY=votre_clé_api")

RestClient.configure(API_KEY)

def get_pokemon_sets():
    sets = []
    try:
        print("Récupération des sets Pokémon...")
        pokemon_sets = PokemonSet.all()

        for set_data in pokemon_sets:
            set_info = {
                'title': set_data.name,
                'code': set_data.id,
                'tcg': 'pokemon',
                'release_date': set_data.releaseDate if hasattr(set_data, 'releaseDate') else None,
                'total_cards': set_data.total if hasattr(set_data, 'total') else 0,
                'image_url': set_data.images.logo if hasattr(set_data, 'images') and hasattr(set_data.images, 'logo') else '',
                'symbol_url': set_data.images.symbol if hasattr(set_data, 'images') and hasattr(set_data.images, 'symbol') else ''
            }
            sets.append(set_info)

        print(f"✓ {len(sets)} sets Pokémon récupérés")
        return sets

    except Exception as e:
        print(f"Erreur lors de la récupération des sets: {str(e)}")
        return []

def import_sets_to_db(sets_data, clear_existing=False):
    if clear_existing:
        print("Suppression de tous les sets existants...")
        count = Set.objects.all().count()
        Set.objects.all().delete()
        print(f"✓ {count} sets supprimés")

    created_count = 0
    updated_count = 0
    error_count = 0

    for set_data in sets_data:
        try:
            title = set_data.get('title', 'Unknown Set')
            code = set_data.get('code', '')
            tcg = set_data.get('tcg', 'pokemon')
            total_cards = set_data.get('total_cards', 0)
            image_url = set_data.get('image_url', '')
            symbol_url = set_data.get('symbol_url', '')

            release_date = None
            if 'release_date' in set_data and set_data['release_date']:
                try:
                    release_date = datetime.strptime(set_data['release_date'], '%Y/%m/%d').date()
                except (ValueError, TypeError):
                    release_date = timezone.now().date()
            else:
                release_date = timezone.now().date()

            set_obj, created = Set.objects.update_or_create(
                code=code,
                defaults={
                    'title': title,
                    'tcg': tcg,
                    'release_date': release_date,
                    'total_cards': total_cards,
                    'image_url': image_url,
                    'symbol_url': symbol_url
                }
            )

            if created:
                created_count += 1
                print(f"✓ Créé: {title} ({code})")
            else:
                updated_count += 1
                print(f"✓ Mis à jour: {title} ({code})")

        except Exception as e:
            error_count += 1
            print(f"✕ Erreur pour le set {set_data.get('title', 'Unknown')}: {str(e)}")

    print(f"\nRésumé de l'importation:")
    print(f"✓ {created_count} sets créés")
    print(f"✓ {updated_count} sets mis à jour")
    if error_count > 0:
        print(f"✕ {error_count} erreurs rencontrées")

def main():
    parser = argparse.ArgumentParser(description='Importe les sets Pokémon dans la base de données')
    parser.add_argument('--clear', action='store_true', help='Supprimer les sets existants avant l\'import')
    parser.add_argument('--json', type=str, help='Chemin du fichier JSON à utiliser au lieu de l\'API')

    args = parser.parse_args()

    if args.json:
        try:
            with open(args.json, 'r', encoding='utf-8') as f:
                sets_data = json.load(f)
            print(f"Chargement de {len(sets_data)} sets depuis {args.json}")
        except Exception as e:
            print(f"Erreur lors du chargement du fichier JSON: {str(e)}")
            return
    else:
        sets_data = get_pokemon_sets()

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seeds')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, 'pokemon_sets_seed.json')
    print(f"Sauvegarde des données en JSON dans {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sets_data, f, indent=2)

    print(f"✓ Données JSON sauvegardées")

    import_sets_to_db(sets_data, args.clear)

if __name__ == "__main__":
    main()
