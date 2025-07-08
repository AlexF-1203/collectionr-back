# api/yolo11/quantized_identifier.py
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from api.models import Card
import logging
import faiss
from typing import Dict, List, Tuple
import struct

logger = logging.getLogger(__name__)

class CardIdentifierFromDB:
    def __init__(self, quantization_bits: int = 8):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.embedding_dim = self.model.config.projection_dim

        # Paramètres de quantisation
        self.quantization_bits = quantization_bits
        self.quantization_levels = 2 ** quantization_bits
        self.scale = None
        self.zero_point = None

        # Stockage quantisé
        self.quantized_embeddings = None
        self.metadata = []

        # Index FAISS avec quantisation
        self.index = None

        self._load_and_quantize_embeddings()

    def _quantize_embeddings(self, embeddings: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """Quantise les embeddings float32 vers int8/int16"""
        # Calcul des paramètres de quantisation
        min_val = embeddings.min()
        max_val = embeddings.max()

        # Scale et zero_point pour la quantisation
        scale = (max_val - min_val) / (self.quantization_levels - 1)
        zero_point = int(round(-min_val / scale))

        # Quantisation
        quantized = np.clip(
            np.round(embeddings / scale + zero_point),
            0,
            self.quantization_levels - 1
        )

        if self.quantization_bits == 8:
            quantized = quantized.astype(np.uint8)
        else:  # 16 bits
            quantized = quantized.astype(np.uint16)

        return quantized, scale, zero_point

    def _dequantize_embeddings(self, quantized: np.ndarray) -> np.ndarray:
        """Dé-quantise les embeddings vers float32"""
        return ((quantized.astype(np.float32) - self.zero_point) * self.scale)

    def _load_and_quantize_embeddings(self):
        """Charge et quantise tous les embeddings"""
        cards = list(Card.objects.exclude(clip_embedding=None))
        self.metadata = []
        all_embeddings = []

        for card in cards:
            try:
                emb = np.array(card.clip_embedding, dtype=np.float32)
                emb /= np.linalg.norm(emb)  # Normalisation
                all_embeddings.append(emb)
                self.metadata.append({
                    "id": card.id,
                    "name": card.name,
                    "number": card.number,
                    "rarity": card.rarity,
                    "price": str(card.price),
                    "set_name": card.set.title if card.set else None
                })
            except Exception as e:
                logger.warning(f"⚠️ Erreur embedding carte ID {card.id}: {e}")

        if all_embeddings:
            embeddings_array = np.stack(all_embeddings).astype("float32")

            # Quantisation
            self.quantized_embeddings, self.scale, self.zero_point = self._quantize_embeddings(embeddings_array)

            # Calcul de la réduction mémoire
            original_size = embeddings_array.nbytes
            quantized_size = self.quantized_embeddings.nbytes
            reduction = (1 - quantized_size / original_size) * 100

            logger.info(f"✅ Quantisation terminée: {original_size} → {quantized_size} bytes ({reduction:.1f}% de réduction)")

            # Création de l'index FAISS avec embeddings dé-quantisés
            if faiss:
                dequantized = self._dequantize_embeddings(self.quantized_embeddings)
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                self.index.add(dequantized)
                logger.info(f"✅ Index FAISS créé avec {len(self.quantized_embeddings)} embeddings quantisés")

    def identify_card(self, image: Image.Image) -> Dict:
        """Identification avec embeddings quantisés"""
        # Extraction embedding query
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            query_embedding = self.model.get_image_features(**inputs)
        query_embedding = query_embedding / query_embedding.norm(dim=-1, keepdim=True)
        query_vec = query_embedding.cpu().numpy().astype("float32")

        if self.index is not None:
            # Recherche FAISS
            scores, indices = self.index.search(query_vec, k=1)
            idx = indices[0][0]
            similarity = scores[0][0]
        else:
            # Recherche manuelle avec dé-quantisation à la volée
            dequantized = self._dequantize_embeddings(self.quantized_embeddings)
            similarities = np.dot(query_vec, dequantized.T)[0]
            idx = np.argmax(similarities)
            similarity = similarities[idx]

        matched = self.metadata[idx]

        return {
            "card_info": matched,
            "similarity_score": float(similarity),
            "matched_card_id": matched["id"],
            "quantization_bits": self.quantization_bits
        }

# Version avec Product Quantization (PQ) pour compression avancée
class ProductQuantizedIdentifier:
    def __init__(self, pq_m: int = 64, pq_bits: int = 8):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.embedding_dim = self.model.config.projection_dim

        # Paramètres Product Quantization
        self.pq_m = pq_m  # Nombre de sous-vecteurs
        self.pq_bits = pq_bits  # Bits par sous-vecteur

        self.metadata = []
        self.index = None

        self._load_with_pq()

    def _load_with_pq(self):
        """Charge les embeddings avec Product Quantization"""
        cards = list(Card.objects.exclude(clip_embedding=None))
        self.metadata = []
        all_embeddings = []

        for card in cards:
            try:
                emb = np.array(card.clip_embedding, dtype=np.float32)
                emb /= np.linalg.norm(emb)
                all_embeddings.append(emb)
                self.metadata.append({
                    "id": card.id,
                    "name": card.name,
                    "number": card.number,
                    "rarity": card.rarity,
                    "price": str(card.price),
                    "set_name": card.set.title if card.set else None
                })
            except Exception as e:
                logger.warning(f"⚠️ Erreur embedding carte ID {card.id}: {e}")

        if all_embeddings and faiss:
            embeddings_array = np.stack(all_embeddings).astype("float32")

            # Création de l'index Product Quantization
            self.index = faiss.IndexPQ(self.embedding_dim, self.pq_m, self.pq_bits)

            # Entraînement du quantizer
            logger.info("🔄 Entraînement du Product Quantizer...")
            self.index.train(embeddings_array)

            # Ajout des embeddings
            self.index.add(embeddings_array)

            # Calcul de la compression
            original_size = embeddings_array.nbytes
            compressed_size = len(embeddings_array) * self.pq_m * self.pq_bits // 8
            compression_ratio = original_size / compressed_size

            logger.info(f"✅ Product Quantization terminée: compression {compression_ratio:.1f}x")

    def identify_card(self, image: Image.Image) -> Dict:
        """Identification avec Product Quantization"""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            query_embedding = self.model.get_image_features(**inputs)
        query_embedding = query_embedding / query_embedding.norm(dim=-1, keepdim=True)
        query_vec = query_embedding.cpu().numpy().astype("float32")

        scores, indices = self.index.search(query_vec, k=1)
        idx = indices[0][0]
        similarity = scores[0][0]

        matched = self.metadata[idx]

        return {
            "card_info": matched,
            "similarity_score": float(similarity),
            "matched_card_id": matched["id"],
            "compression_method": "product_quantization"
        }

# Utility pour analyser la compression
def analyze_compression_trade_offs():
    """Analyse les compromis entre compression et précision"""
    import time

    # Test différents niveaux de quantisation
    methods = [
        ("float32", None),
        ("int8", QuantizedCardIdentifier(8)),
        ("int16", QuantizedCardIdentifier(16)),
        ("product_quantization", ProductQuantizedIdentifier())
    ]

    # Image de test
    test_image = Image.new('RGB', (224, 224), color='red')

    results = {}

    for method_name, identifier in methods:
        if identifier is None:
            continue

        start_time = time.time()
        result = identifier.identify_card(test_image)
        end_time = time.time()

        results[method_name] = {
            "inference_time": end_time - start_time,
            "similarity_score": result.get("similarity_score", 0),
            "memory_usage": "calculated_separately"
        }

    return results
