import threading
from django.core.cache import cache
import time
import io
import logging
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.yolo11.identify import CardIdentifierFromDB

logger = logging.getLogger(__name__)

_identifier_instance = None
_initialization_lock = threading.Lock()
_is_initializing = False

def initialize_model():
    global _identifier_instance, _is_initializing
    with _initialization_lock:
        if _identifier_instance is None and not _is_initializing:
            try:
                _is_initializing = True
                logger.info("🤖 Chargement du modèle CLIP à la demande...")
                _identifier_instance = CardIdentifierFromDB()
                logger.info("✅ Modèle CLIP chargé avec succès !")
            except Exception as e:
                logger.error(f"❌ Erreur lors du chargement du modèle: {str(e)}")
                _identifier_instance = None
            finally:
                _is_initializing = False

def get_identifier():
    global _identifier_instance
    if _identifier_instance is None:
        initialize_model()
    if _identifier_instance is None:
        raise Exception("Le modèle CLIP n'a pas pu être initialisé")
    return _identifier_instance

def is_model_ready():
    return _identifier_instance is not None

def is_model_initializing():
    return _is_initializing

class CardIdentificationView(APIView):
    def post(self, request):
        start_time = time.time()
        try:
            if 'image' not in request.FILES:
                return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
            image_file = request.FILES['image']
            logger.info(f"📸 Traitement de l'image: {image_file.name}")

            step_start = time.time()
            try:
                image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
                image_load_time = time.time() - step_start
                logger.info(f"✅ Image chargée en {image_load_time:.2f}s")
            except Exception as e:
                logger.error(f"❌ Erreur chargement image: {str(e)}")
                return Response({"error": f"Invalid image file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            step_start = time.time()
            try:
                if is_model_initializing():
                    return Response({
                        "status": "initializing",
                        "message": "Le modèle d'identification est en cours d'initialisation. Veuillez patienter...",
                        "retry_in": 5
                    }, status=status.HTTP_202_ACCEPTED)

                identifier = get_identifier()
                model_init_time = time.time() - step_start
                logger.info(f"✅ Modèle récupéré en {model_init_time:.2f}s")
            except Exception as e:
                logger.error(f"❌ Erreur récupération modèle: {str(e)}")
                return Response({"error": f"Model not available: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            step_start = time.time()
            try:
                logger.info("🔍 Début de l'identification...")
                result = identifier.identify_card(image)
                identification_time = time.time() - step_start
                logger.info(f"✅ Identification terminée en {identification_time:.2f}s")
            except Exception as e:
                logger.error(f"❌ Erreur identification: {str(e)}")
                return Response({"error": f"Identification failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            total_time = time.time() - start_time

            result['performance'] = {
                'total_time': round(total_time, 2),
                'image_load_time': round(image_load_time, 2),
                'model_init_time': round(model_init_time, 2),
                'identification_time': round(identification_time, 2)
            }
            logger.info(f"🎉 Succès total en {total_time:.2f}s")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"💥 Erreur inattendue: {str(e)}")
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModelStatusView(APIView):
    def get(self, request):
        return Response({
            'model_ready': is_model_ready(),
            'model_initializing': is_model_initializing(),
            'status': 'ready' if is_model_ready() else 'initializing' if is_model_initializing() else 'not_loaded'
        })
