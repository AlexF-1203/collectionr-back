import os
import sys
import django
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import base64

from transformers import CLIPProcessor, CLIPModel
import torch
import cv2
import imagehash
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from api.models import Card

BATCH_SIZE = 16
MAX_WORKERS = 4
PREFETCH_BUFFER = 50

class OptimizedFeatureExtractor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Utilisation de: {self.device}")

        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.orb = cv2.ORB_create(nfeatures=100)

    def serialize_numpy_array(self, arr):
        return base64.b64encode(arr.tobytes()).decode('utf-8')

    def serialize_list(self, lst):
        return json.dumps(lst)

    def download_image(self, url, timeout=10):
        try:
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"Erreur téléchargement {url}: {e}")
            return None

    def extract_features_single(self, image):
        try:
            image_np = np.array(image)
            cv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            phash = str(imagehash.phash(image))

            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            hist_flat = hist.flatten().tolist()

            _, descriptors = self.orb.detectAndCompute(cv_image, None)
            if descriptors is None:
                descriptors = np.zeros((1, 32), dtype=np.uint8)

            return {
                'phash': phash,
                'histogram': hist_flat,
                'descriptors': descriptors.tobytes()
            }
        except Exception as e:
            print(f"Erreur extraction features: {e}")
            return None

    def extract_clip_embeddings_batch(self, images):
        try:
            valid_images = [img for img in images if img is not None]
            if not valid_images:
                return [None] * len(images)

            inputs = self.clip_processor(images=valid_images, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                embeddings = self.clip_model.get_image_features(**inputs)

            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            embeddings_np = embeddings.cpu().numpy()

            result = []
            valid_idx = 0
            for img in images:
                if img is not None:
                    result.append(embeddings_np[valid_idx])
                    valid_idx += 1
                else:
                    result.append(None)

            return result
        except Exception as e:
            print(f"Erreur batch CLIP: {e}")
            return [None] * len(images)

    def process_cards_parallel(self, cards):
        results = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            print("Téléchargement des images...")
            download_futures = {
                executor.submit(self.download_image, card.image_url): card
                for card in cards
            }

            images_data = []
            for future in tqdm(as_completed(download_futures), total=len(cards)):
                card = download_futures[future]
                try:
                    image = future.result()
                    images_data.append((card, image))
                except Exception as e:
                    print(f"Erreur pour {card}: {e}")
                    images_data.append((card, None))

        print("Extraction des features CV...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            cv_futures = {
                executor.submit(self.extract_features_single, image): (card, image)
                for card, image in images_data
            }

            for future in tqdm(as_completed(cv_futures), total=len(images_data)):
                card, image = cv_futures[future]
                try:
                    features = future.result()
                    results.append((card, image, features))
                except Exception as e:
                    print(f"Erreur features pour {card}: {e}")
                    results.append((card, image, None))

        return results

    def save_cards_safely(self, cards_data):
        saved_count = 0

        for card, clip_embedding, features in tqdm(cards_data, desc="Sauvegarde"):
            try:
                if clip_embedding is not None and features is not None:

                    if isinstance(clip_embedding, np.ndarray):
                        clip_embedding_list = clip_embedding.tolist()
                    else:
                        clip_embedding_list = clip_embedding

                    if not isinstance(clip_embedding_list, list) or not all(isinstance(x, (int, float)) for x in clip_embedding_list):
                        print(f"Erreur: embedding CLIP invalide pour {card}")
                        continue

                    histogram = features['histogram']
                    if not isinstance(histogram, list) or not all(isinstance(x, (int, float)) for x in histogram):
                        print(f"Erreur: histogramme invalide pour {card}")
                        continue

                    phash = features['phash']
                    if not isinstance(phash, str):
                        print(f"Erreur: phash invalide pour {card}")
                        continue

                    descriptors = features['descriptors']
                    if not isinstance(descriptors, bytes):
                        print(f"Erreur: descripteurs invalides pour {card}")
                        continue

                    card.clip_embedding = clip_embedding_list
                    card.phash = phash
                    card.histogram = histogram
                    card.descriptors = descriptors

                    try:
                        card.save(update_fields=['clip_embedding', 'phash', 'histogram', 'descriptors'])
                        saved_count += 1
                    except Exception as save_error:
                        print(f"Erreur lors de la sauvegarde de {card}: {save_error}")
                        try:
                            card.clip_embedding = clip_embedding_list
                            card.save(update_fields=['clip_embedding'])
                            print(f"  - clip_embedding OK pour {card}")
                        except Exception as e:
                            print(f"  - Erreur clip_embedding: {e}")

                        try:
                            card.phash = phash
                            card.save(update_fields=['phash'])
                            print(f"  - phash OK pour {card}")
                        except Exception as e:
                            print(f"  - Erreur phash: {e}")

                        try:
                            card.histogram = histogram
                            card.save(update_fields=['histogram'])
                            print(f"  - histogram OK pour {card}")
                        except Exception as e:
                            print(f"  - Erreur histogram: {e}")

                        try:
                            card.descriptors = descriptors
                            card.save(update_fields=['descriptors'])
                            print(f"  - descriptors OK pour {card}")
                        except Exception as e:
                            print(f"  - Erreur descriptors: {e}")
                else:
                    print(f"Données manquantes pour {card}")

            except Exception as e:
                print(f"Erreur générale pour {card}: {e}")
                continue

        return saved_count

    def process_all_cards(self):
        cards = list(Card.objects.all())
        total_cards = len(cards)
        print(f"Traitement de {total_cards} cartes")

        chunk_size = PREFETCH_BUFFER
        total_saved = 0

        for i in range(0, total_cards, chunk_size):
            chunk = cards[i:i + chunk_size]
            print(f"\nChunk {i//chunk_size + 1}/{(total_cards + chunk_size - 1)//chunk_size}")

            results = self.process_cards_parallel(chunk)

            print("Extraction embeddings CLIP...")
            images = [image for _, image, _ in results]

            clip_embeddings = []
            for j in range(0, len(images), BATCH_SIZE):
                batch_images = images[j:j + BATCH_SIZE]
                batch_embeddings = self.extract_clip_embeddings_batch(batch_images)
                clip_embeddings.extend(batch_embeddings)

            cards_to_save = []
            for (card, image, features), clip_embedding in zip(results, clip_embeddings):
                if features is not None and clip_embedding is not None:
                    cards_to_save.append((card, clip_embedding, features))

            print("Sauvegarde en base...")
            saved_count = self.save_cards_safely(cards_to_save)
            total_saved += saved_count

            print(f"Chunk terminé: {saved_count}/{len(chunk)} cartes sauvegardées")

        print(f"\nTraitement terminé! Total: {total_saved}/{total_cards} cartes sauvegardées")

if __name__ == "__main__":
    extractor = OptimizedFeatureExtractor()
    extractor.process_all_cards()
