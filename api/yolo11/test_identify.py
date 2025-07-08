import sys
import os
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from identify import CardIdentifierFromDB
from PIL import Image

img = Image.open("api/yolo11/test_image/TEST_3.png").convert("RGB")

identifier = CardIdentifierFromDB()
res = identifier.identify_card(img)
print(res)
