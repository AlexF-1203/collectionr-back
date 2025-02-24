from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Set, User
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_collections(sender, instance, created, **kwargs):
    """
    Signal qui attribue automatiquement TOUS les sets à un nouvel utilisateur.
    """
    if created:
        logger.info(f"Création des collections pour le nouvel utilisateur: {instance.username}")
        
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if admin_user and Set.objects.filter(user=admin_user).exists():
                with transaction.atomic():
                    admin_sets = Set.objects.filter(user=admin_user)
                    logger.info(f"Copie de {admin_sets.count()} sets depuis l'administrateur")
                    
                    for admin_set in admin_sets:
                        Set.objects.create(
                            user=instance,
                            title=admin_set.title,
                            code=admin_set.code,
                            tcg=admin_set.tcg,
                            release_date=admin_set.release_date,
                            total_cards=admin_set.total_cards,
                            image_url=admin_set.image_url
                        )
                        
                logger.info(f"Tous les sets ({admin_sets.count()}) ont été copiés avec succès pour {instance.username}")
            else:
                from django.core.management import call_command
                logger.info(f"Utilisation du script d'importation pour créer les sets de {instance.username}")
                
                call_command('create_user_collections', user=instance.username, verbosity=0)
                logger.info(f"Commande d'importation exécutée pour {instance.username}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des collections pour {instance.username}: {str(e)}")