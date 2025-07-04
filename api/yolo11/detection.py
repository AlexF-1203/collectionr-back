from PIL import Image
import os
import cv2
from ultralytics import YOLO
from .identify import CardIdentifierFromDB

def verify_detection_quality(image_path, detection_box):
    x1, y1, x2, y2 = detection_box
    img = Image.open(image_path)
    width, height = img.size
    box_width = x2 - x1
    box_height = y2 - y1
    aspect_ratio = box_width / box_height if box_height > 0 else 0
    pokemon_card_ratio = 0.714
    ratio_error = abs(aspect_ratio - pokemon_card_ratio) / pokemon_card_ratio
    return not (ratio_error > 0.2 or (box_width * box_height) < (width * height * 0.1))

def detect_cards_in_image(image_path, model_path="pokemon_detector.pt"):
    model = YOLO(model_path)
    img = cv2.imread(str(image_path))
    results = model(img, conf=0.3)
    detections = []
    if not results or len(results) == 0 or len(results[0].boxes) == 0:
        width, height = Image.open(image_path).size
        return [{"box": [0, 0, width, height], "confidence": 1.0, "is_default": True}]
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = box.conf[0].cpu().numpy()
        detections.append({
            "box": [int(x1), int(y1), int(x2), int(y2)],
            "confidence": float(conf),
            "is_default": False
        })
    return detections

def detect_and_identify_pokemon_cards(image_path, model_path="pokemon_detector.pt"):
    print(f"Détection des cartes dans {image_path}...")
    detections = detect_cards_in_image(image_path, model_path)
    identifier = CardIdentifierFromDB()

    cards_found = []
    for i, detection in enumerate(detections):
        box = detection["box"]
        is_default = detection.get("is_default", False)
        if is_default or verify_detection_quality(image_path, box):
            img = Image.open(image_path)
            cropped = img.crop(box)
            if cropped.mode != 'RGB':
                cropped = cropped.convert('RGB')
            card_id = identifier.identify_card(cropped)
            cards_found.append({
                "box": box,
                "card_info": card_id["card_info"],
                "similarity_score": card_id["similarity_score"],
                "matched_card_id": card_id["matched_card_id"],
                "is_default_detection": is_default
            })
        else:
            print(f"Détection #{i+1} ignorée car de faible qualité")
    return cards_found
