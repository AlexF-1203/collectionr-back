from django.db import models
from django.conf import settings
from .card import Card


class Collection(models.Model):
    """
    Modèle représentant la collection de cartes d'un utilisateur.
    """
    CONDITION_CHOICES = [
        ('MINT', 'Mint'),
        ('NM', 'Near Mint'),
        ('EX', 'Excellent'),
        ('GD', 'Good'),
        ('LP', 'Lightly Played'),
        ('PL', 'Played'),
        ('POOR', 'Poor'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    acquired_date = models.DateField(auto_now_add=True)
    # is_foil = models.BooleanField(default=False)
    # notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-acquired_date']

    def __str__(self):
        return f"{self.user.username}'s {self.card.name} x{self.quantity}"