from django.contrib.auth.models import AbstractUser
from django.db import models
from ..validators import validate_email_domain


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        validators=[validate_email_domain],
        error_messages={
            'Unique': "Un utilisateur avec cet email existe déjà"
        }
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user'
        
    def __str__(self):
        return self.username