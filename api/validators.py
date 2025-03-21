from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not any(char.islower() for char in password):
            raise ValidationError(_("Le mot de passe doit contenir au moins une minuscule"))
        if not any(char.isupper() for char in password):
            raise ValidationError(_("Le mot de passe doit contenir au moins une majuscule"))
        if not any(char.isdigit() for char in password):
            raise ValidationError(_("Le mot de passe doit contenir au moins un chiffre"))
        if not any(char in '!@#$%^&*()_+-=[]{};:\'",.<>/?`~' for char in password):
            raise ValidationError(_("Le mot de passe doit contenir au moins un caractère spécial"))

    def get_help_text(self):
        return _("""
            Votre mot de passe doit contenir :
            - Au moins 12 caractères
            - Une minuscule et une majuscule
            - Un chiffre
            - Un caractère spécial
        """) 

def validate_email_domain(email_value):
    validate_email(email_value)
    
    if '@' in email_value:
        domain_part = email_value.split('@')[1]
        if '.' not in domain_part:
            raise ValidationError("L'adresse email doit avoir un domaine valide.")

        blocked_domains = ['yopmail.com', 'tempmail.com', 'guerrillamail.com']
        if domain_part.lower() in blocked_domains:
            raise ValidationError("Les adresses email temporaires ne sont pas autorisées.")

        username = email_value.split('@')[0]
        if len(username) > 64:
            raise ValidationError("Le nom d'utilisateur ne doit pas dépasser 64 caractères.")