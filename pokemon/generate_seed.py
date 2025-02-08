from card_manager import PokemonCardManager
import os
from typing import List

def main():
    # Définition des sets à extraire
    TARGET_SETS = ['swsh45sv', 'swsh9']  # Shining Fates et Brilliant Stars
    
    # Création du gestionnaire
    manager = PokemonCardManager()
    
    # Génération des données
    print("Génération des données seed...")
    manager.generate_seed_data(TARGET_SETS)
    
    # Export des données
    output_dir = 'seeds'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, 'pokemon_cards_seed.json')
    manager.export_to_json(output_file)
    print(f"Données exportées vers {output_file}")

if __name__ == '__main__':
    main() 