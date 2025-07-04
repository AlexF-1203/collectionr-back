# identify.py
from cards.models import Card
import numpy as np
import imagehash
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import cv2
import io

class CardIdentifierFromDB:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # Charger toutes les cartes avec des embeddings
        self.cards = list(Card.objects.exclude(clip_embedding=None))

        # Normaliser les vecteurs en batch
        self.embeddings = np.stack([c.clip_embedding for c in self.cards])
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / norms

    def identify_card(self, image: Image.Image):
        # Prétraitement
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            query_embedding = self.model.get_image_features(**inputs)
        query_embedding = query_embedding / query_embedding.norm(dim=-1, keepdim=True)
        query_vec = query_embedding.cpu().numpy()[0]

        # Similarité cosinus avec toutes les cartes
        similarities = self.embeddings @ query_vec
        best_idx = np.argmax(similarities)
        best_card = self.cards[best_idx]

        return {
            "card_info": {
                "name": best_card.name,
                "set_name": best_card.set_name,
                "number": best_card.number,
                "rarity": best_card.rarity,
                "price": str(best_card.price)
            },
            "similarity_score": float(similarities[best_idx]),
            "matched_card_id": best_card.id
        }
