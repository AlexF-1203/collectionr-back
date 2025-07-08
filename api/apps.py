from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        logger.info("✅ Application API prête (modèle CLIP en attente)")
