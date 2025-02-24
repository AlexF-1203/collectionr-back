from django.core.management.base import BaseCommand
from api.models import User, Set
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Crée des collections pour les utilisateurs en copiant TOUS les sets disponibles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username spécifique pour lequel créer des collections'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Créer des collections même si l\'utilisateur en a déjà'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        force = options.get('force', False)
        verbosity = options.get('verbosity', 1)
        
        if username:
            users = User.objects.filter(username=username)
            if not users.exists():
                if verbosity > 0:
                    self.stderr.write(self.style.ERROR(f'Utilisateur "{username}" non trouvé'))
                return
        else:
            users = User.objects.all()
            
        if verbosity > 0:
            self.stdout.write(f"Création de collections pour {users.count()} utilisateurs...")
        
        admin_user = User.objects.filter(is_superuser=True).first()
        admin_sets = []
        if admin_user:
            admin_sets = Set.objects.filter(user=admin_user)
            if admin_sets.exists() and verbosity > 0:
                self.stdout.write(f"Utilisation de {admin_sets.count()} sets depuis l'administrateur.")
        
        if not admin_sets.exists():
            max_sets_user = None
            max_sets_count = 0
            
            for user in User.objects.all():
                sets_count = Set.objects.filter(user=user).count()
                if sets_count > max_sets_count:
                    max_sets_count = sets_count
                    max_sets_user = user
            
            if max_sets_user and max_sets_count > 0:
                admin_sets = Set.objects.filter(user=max_sets_user)
                if verbosity > 0:
                    self.stdout.write(f"Utilisation de {admin_sets.count()} sets depuis l'utilisateur {max_sets_user.username}.")
        
        if not admin_sets.exists():
            if verbosity > 0:
                self.stdout.write("Aucun set trouvé. Importation depuis l'API Pokemon TCG...")
            try:
                from django.core.management import call_command
                temp_user = users.first()
                call_command('import_pokemon_sets', user=temp_user.id, verbosity=0)
                admin_sets = Set.objects.filter(user=temp_user)
                if verbosity > 0:
                    self.stdout.write(f"Importés {admin_sets.count()} sets depuis l'API.")
            except Exception as e:
                if verbosity > 0:
                    self.stderr.write(f"Erreur lors de l'importation: {str(e)}")
        
        if not admin_sets.exists():
            if verbosity > 0:
                self.stderr.write(self.style.ERROR("Aucun set trouvé à attribuer. Arrêt."))
            return
        
        with transaction.atomic():
            for user in users:
                user_sets_count = Set.objects.filter(user=user).count()
                if user_sets_count > 0 and not force:
                    if verbosity > 0:
                        self.stdout.write(f"{user.username} a déjà {user_sets_count} sets. Utilisez --force pour recréer.")
                    continue
                    
                if verbosity > 0:
                    self.stdout.write(f"Création de {admin_sets.count()} collections pour {user.username}...")
                
                for source_set in admin_sets:
                    if Set.objects.filter(user=user, code=source_set.code).exists():
                        if force:
                            existing_set = Set.objects.get(user=user, code=source_set.code)
                            existing_set.title = source_set.title
                            existing_set.tcg = source_set.tcg
                            existing_set.release_date = source_set.release_date
                            existing_set.total_cards = source_set.total_cards
                            existing_set.image_url = source_set.image_url
                            existing_set.save()
                            if verbosity > 0:
                                self.stdout.write(f"✓ Set '{source_set.title}' mis à jour pour {user.username}")
                        continue
                        
                    Set.objects.create(
                        user=user,
                        title=source_set.title,
                        code=source_set.code,
                        tcg=source_set.tcg,
                        release_date=source_set.release_date,
                        total_cards=source_set.total_cards,
                        image_url=source_set.image_url
                    )
                    if verbosity > 0:
                        self.stdout.write(f"✓ Set '{source_set.title}' attribué à {user.username}")
            
        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS('Création des collections terminée avec succès!'))