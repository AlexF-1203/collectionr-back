from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    # Ajoutez des champs personnalisés si nécessaire
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # test
    class Meta:
        db_table = 'auth_user'
