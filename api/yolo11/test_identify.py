import sys
import os
import django

# 1. Ajouter le chemin du dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 2. Spécifier les settings Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # ou le nom exact de ton dossier settings.py

# 3. Lancer Django
django.setup()

from identify import CardIdentifierFromDB
from PIL import Image

# 4. Charger une image
img = Image.open("api/yolo11/test_image/TEST_3.png").convert("RGB")

# 5. Identifier
identifier = CardIdentifierFromDB()
res = identifier.identify_card(img)
print(res)
