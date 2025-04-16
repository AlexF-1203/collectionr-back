# test
import torch
from PIL import Image
import json
from pathlib import Path
import numpy as np
from transformers import CLIPProcessor, CLIPModel
import glob
from ultralytics import YOLO
import os
import cv2
import imagehash
import time
import matplotlib.pyplot as plt

class ImprovedCardIdentifier:
    def __init__(self, card_info_path, image_directory):
        # Charger le mapping des informations de cartes
        with open(card_info_path, 'r') as f:
            self.card_info = json.load(f)

        self.image_directory = Path(image_directory)

        # Modèle CLIP pour générer des embeddings d'images
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Utilisation de l'appareil: {self.device}")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # Stocker les caractéristiques de référence
        self.reference_cards = {}
        self._precompute_features()

    def _precompute_features(self):
        """Prétraitement: calculer toutes les caractéristiques pour les images de référence"""
        print("Calcul des caractéristiques pour les images de référence...")

        # Récupérer tous les fichiers d'images
        train_images = glob.glob(str(self.image_directory / "train" / "images" / "*.png"))
        val_images = glob.glob(str(self.image_directory / "val" / "images" / "*.png"))
        all_images = train_images + val_images

        for image_path in all_images:
            # Extraire uniquement le nom du fichier
            filename = Path(image_path).name

            # Vérifier si on a les infos pour cette image
            if filename in self.card_info:
                # Charger et traiter l'image pour CLIP
                pil_image = Image.open(image_path)

                # CLIP embedding
                inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    embedding = self.model.get_image_features(**inputs)
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                embedding_np = embedding.cpu().numpy()[0]

                # Autres caractéristiques
                additional_features = self._extract_features(image_path)

                # Stocker toutes les caractéristiques
                self.reference_cards[filename] = {
                    'embedding': embedding_np,
                    'phash': additional_features['phash'],
                    'histogram': additional_features['histogram'],
                    'descriptors': additional_features['descriptors'],
                    'info': self.card_info[filename]
                }

        print(f"Caractéristiques calculées pour {len(self.reference_cards)} cartes.")

    def _extract_features(self, image_path):
        """Extrait plusieurs types de caractéristiques d'une image"""
        # Ouvrir l'image avec PIL et OpenCV
        pil_image = Image.open(image_path)
        cv_image = cv2.imread(str(image_path))

        # 1. Hachage perceptuel (pour comparer la structure visuelle)
        phash = imagehash.phash(pil_image)

        # 2. Histogramme de couleurs
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        hist_flat = hist.flatten()

        # 3. Caractéristiques ORB (pour les points d'intérêt)
        orb = cv2.ORB_create(nfeatures=100)
        keypoints, descriptors = orb.detectAndCompute(cv_image, None)
        if descriptors is None:
            descriptors = np.zeros((1, 32), dtype=np.uint8)

        return {
            'phash': phash,
            'histogram': hist_flat,
            'descriptors': descriptors
        }

    def identify_card(self, image_path):
        """Identifier une carte en utilisant plusieurs méthodes combinées"""
        # Extraire les caractéristiques de l'image requête
        query_image = Image.open(image_path)

        # CLIP embedding
        inputs = self.processor(images=query_image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            query_embedding = self.model.get_image_features(**inputs)
        query_embedding = query_embedding / query_embedding.norm(dim=-1, keepdim=True)
        query_embedding_np = query_embedding.cpu().numpy()[0]

        # Autres caractéristiques
        query_features = self._extract_features(image_path)

        # Calculer les scores combinés pour chaque carte de référence
        best_match = None
        best_score = -float('inf')

        for filename, ref_card in self.reference_cards.items():
            # 1. Similarité CLIP (cosinus)
            clip_similarity = np.dot(ref_card['embedding'], query_embedding_np)

            # 2. Similarité de hachage perceptuel
            phash_similarity = 1.0 - (query_features['phash'] - ref_card['phash']) / 64.0

            # 3. Similarité d'histogramme
            hist_correlation = cv2.compareHist(
                query_features['histogram'].astype(np.float32),
                ref_card['histogram'].astype(np.float32),
                cv2.HISTCMP_CORREL
            )

            # 4. Correspondance de caractéristiques ORB
            orb_similarity = 0
            if query_features['descriptors'].shape[0] > 0 and ref_card['descriptors'].shape[0] > 0:
                try:
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    matches = bf.match(query_features['descriptors'], ref_card['descriptors'])
                    orb_similarity = len(matches) / max(
                        query_features['descriptors'].shape[0],
                        ref_card['descriptors'].shape[0]
                    )
                except:
                    # En cas d'erreur dans la correspondance de caractéristiques
                    orb_similarity = 0

            # Combiner les scores avec des poids différents
            combined_score = (
                0.6 * clip_similarity +  # CLIP est très bon pour les caractéristiques sémantiques
                0.2 * phash_similarity +  # phash est bon pour la structure visuelle
                0.1 * hist_correlation +  # histogramme est bon pour les distributions de couleurs
                0.1 * orb_similarity      # ORB est bon pour les caractéristiques locales
            )

            if combined_score > best_score:
                best_score = combined_score
                best_match = filename

        # Récupérer les informations de la carte
        if best_match:
            return {
                "card_info": self.reference_cards[best_match]['info'],
                "similarity_score": float(best_score),
                "matched_file": best_match
            }
        else:
            return {
                "card_info": {},
                "similarity_score": 0.0,
                "matched_file": None
            }

def verify_detection_quality(image_path, detection_box):
    """Vérifie si la détection est de bonne qualité ou pourrait être améliorée"""
    x1, y1, x2, y2 = detection_box

    # Charger l'image
    img = Image.open(image_path)
    width, height = img.size

    # Calculer les proportions du cadre de détection
    box_width = x2 - x1
    box_height = y2 - y1
    aspect_ratio = box_width / box_height if box_height > 0 else 0

    # L'aspect ratio d'une carte Pokémon est d'environ 2.5/3.5 = 0.714
    pokemon_card_ratio = 0.714
    ratio_error = abs(aspect_ratio - pokemon_card_ratio) / pokemon_card_ratio

    # Si le ratio est trop différent, ou si la boîte est trop petite
    if ratio_error > 0.2 or (box_width * box_height) < (width * height * 0.1):
        return False
    return True

def detect_cards_in_image(image_path, model_path=None):
    """Détecte les cartes dans une image avec un prétraitement amélioré"""
    # Trouver automatiquement le modèle
    if model_path is None or not os.path.exists(model_path):
        potential_paths = [
            "pokemon_detector.pt",  # Votre modèle personnalisé
            "runs/detect/train/weights/best.pt",
            "runs/train/weights/best.pt",
            "./best.pt",
            "./weights/best.pt",
            "last.pt",
            "/Users/enee/code/collectionr_python/backend/api/yolo11/yolo11m.pt"
        ]

        for path in potential_paths:
            if os.path.exists(path):
                model_path = path
                print(f"Modèle trouvé automatiquement à: {model_path}")
                break

        if model_path is None or not os.path.exists(model_path):
            # Si pas de modèle détecteur, retourner une détection par défaut
            # (utiliser toute l'image comme une seule carte)
            img = Image.open(image_path)
            width, height = img.size
            return [
                {
                    "box": [0, 0, width, height],
                    "confidence": 1.0,
                    "is_default": True
                }
            ]

    # Charger le modèle YOLO
    model = YOLO(model_path)

    # Prétraitement de l'image
    img = cv2.imread(str(image_path))

    # Améliorer le contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    if len(img.shape) > 2 and img.shape[2] == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Sauvegarder l'image améliorée temporairement
    temp_path = 'temp_enhanced.jpg'
    cv2.imwrite(temp_path, img)

    # Détection avec confiance minimale plus basse pour être plus sensible
    results = model(temp_path, conf=0.3)

    # Nettoyer le fichier temporaire
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # Si aucune détection, retourner l'image entière comme carte
    if not results or len(results) == 0 or len(results[0].boxes) == 0:
        img = Image.open(image_path)
        width, height = img.size
        return [
            {
                "box": [0, 0, width, height],
                "confidence": 1.0,
                "is_default": True
            }
        ]

    # Traiter les résultats de détection
    boxes = []
    result = results[0]

    if hasattr(result, 'boxes') and len(result.boxes) > 0:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = box.conf[0].cpu().numpy()
            boxes.append({
                "box": [int(x1), int(y1), int(x2), int(y2)],
                "confidence": float(confidence),
                "is_default": False
            })

    return boxes
def detect_and_identify_pokemon_cards(image_path, model_path=None, card_info_path=None, image_directory=None):
    """Détecte et identifie les cartes Pokémon dans une image avec vérification de qualité"""
    # Déterminer le chemin du répertoire actuel
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Utiliser des chemins par défaut relatifs au répertoire du script si non spécifiés
    if card_info_path is None:
        card_info_path = os.path.join(current_dir, "pokemon_dataset", "card_info.json")

    if image_directory is None:
        image_directory = os.path.join(current_dir, "pokemon_dataset")

    # Détecter les cartes
    print(f"Détection des cartes dans {image_path}...")
    detections = detect_cards_in_image(image_path, model_path)

    if not detections:
        print("Aucune carte détectée dans l'image.")
        return []

    # Initialiser l'identifieur de cartes
    print("Initialisation de l'identifieur de cartes amélioré...")
    identifier = ImprovedCardIdentifier(
        card_info_path=card_info_path,
        image_directory=image_directory
    )
    cards_found = []
    for i, detection in enumerate(detections):
        box = detection["box"]
        is_default = detection.get("is_default", False)

        # Si détection par défaut ou détection de bonne qualité
        if is_default or verify_detection_quality(image_path, box):
            print(f"Identification de la carte #{i+1}...")

            # Si détection par défaut, utiliser l'image entière
            if is_default:
                card_id = identifier.identify_card(image_path)
            else:
                # Extraire la partie de l'image correspondant à la détection
                img = Image.open(image_path)
                cropped = img.crop(box)

                # Convertir RGBA en RGB si nécessaire
                if cropped.mode == 'RGBA':
                    # Créer un fond blanc et composer avec l'image RGBA
                    background = Image.new('RGB', cropped.size, (255, 255, 255))
                    background.paste(cropped, mask=cropped.split()[3])  # 3 est le canal alpha
                    cropped = background
                elif cropped.mode != 'RGB':
                    # Convertir tout autre mode en RGB
                    cropped = cropped.convert('RGB')

                # Sauvegarder temporairement l'image recadrée
                temp_crop_path = f'temp_crop_{i}.jpg'
                cropped.save(temp_crop_path)

                # Identifier la carte
                card_id = identifier.identify_card(temp_crop_path)

                # Nettoyer
                if os.path.exists(temp_crop_path):
                    os.remove(temp_crop_path)


            # Ajouter aux résultats
            cards_found.append({
                "box": box,
                "card_info": card_id["card_info"],
                "similarity_score": card_id["similarity_score"],
                "matched_file": card_id["matched_file"],
                "is_default_detection": is_default
            })
        else:
            print(f"Détection #{i+1} ignorée car de faible qualité")

    return cards_found

# Fonction simplifiée pour tester votre modèle
def test_pokemon_detector(image_path, model_path="pokemon_detector.pt", card_info_path=None, image_directory=None):
    """Fonction pour tester le détecteur de cartes Pokémon avec un modèle personnalisé"""
    print(f"Test de détection sur {image_path} avec le modèle {model_path}")

    # Déterminer le chemin du répertoire actuel
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Utiliser des chemins par défaut relatifs au répertoire du script si non spécifiés
    if card_info_path is None:
        card_info_path = os.path.join(current_dir, "pokemon_dataset", "card_info.json")

    if image_directory is None:
        image_directory = os.path.join(current_dir, "pokemon_dataset")

    print(f"Utilisation du fichier d'informations: {card_info_path}")
    print(f"Utilisation du répertoire d'images: {image_directory}")

    # Vérifier l'existence des fichiers nécessaires
    if not os.path.exists(card_info_path):
        raise FileNotFoundError(f"Le fichier d'informations de cartes n'existe pas: {card_info_path}")

    if not os.path.exists(image_directory):
        raise FileNotFoundError(f"Le répertoire d'images n'existe pas: {image_directory}")

    # Détecter et identifier les cartes
    results = detect_and_identify_pokemon_cards(
        image_path,
        model_path,
        card_info_path=card_info_path,
        image_directory=image_directory
    )

    # Afficher les résultats
    print("\nRésultats:")
    if not results:
        print("Aucune carte Pokémon détectée.")
        return None
    else:
        for i, card in enumerate(results):
            print(f"Carte #{i+1}:")
            print(f"  Position: {card['box']}")
            print(f"  Nom: {card['card_info'].get('name', 'Inconnu')}")
            print(f"  Set: {card['card_info'].get('set_name', 'Inconnu')}")
            print(f"  Numéro: {card['card_info'].get('number', 'Inconnu')}")
            print(f"  Rareté: {card['card_info'].get('rarity', 'Inconnu')}")
            print(f"  Score de similarité: {card['similarity_score']:.4f}")
            print(f"  Fichier correspondant: {card['matched_file']}")
            print(f"  Détection par défaut: {'Oui' if card.get('is_default_detection', False) else 'Non'}")
            print()

    return results

# Exemple d'utilisation
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python identify.py <chemin_vers_image> [chemin_vers_modele]")
        sys.exit(1)

    # Chemin vers une image contenant une ou plusieurs cartes Pokémon
    test_image = sys.argv[1]

    # Spécifier le chemin du modèle s'il est fourni
    model_path = sys.argv[2] if len(sys.argv) > 2 else "pokemon_detector.pt"

    try:
        # Utiliser la fonction de test simplifiée
        test_pokemon_detector(test_image, model_path)
    except Exception as e:
        print(f"Erreur: {e}")
        print("\nVérifiez que:")
        print("1. Le chemin vers votre image est correct")
        print("2. Votre modèle pokemon_detector.pt existe dans le répertoire courant")
        print("3. Le fichier card_info.json existe dans le répertoire pokemon_dataset/")

        # Afficher les chemins pour aider au débogage
        current_dir = os.path.dirname(os.path.abspath(__file__))
        expected_card_info = os.path.join(current_dir, "pokemon_dataset", "card_info.json")
        expected_dataset = os.path.join(current_dir, "pokemon_dataset")

        print(f"\nChemins attendus:")
        print(f"Répertoire actuel: {current_dir}")
        print(f"Fichier d'infos: {expected_card_info}")
        print(f"Répertoire des images: {expected_dataset}")

        # Lister le contenu du répertoire pour le débogage
        print("\nContenu du répertoire actuel:")
        for item in os.listdir(current_dir):
            print(f"  - {item}")
