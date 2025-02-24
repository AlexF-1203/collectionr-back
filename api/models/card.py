from django.db import models
from djmoney.models.fields import MoneyField


class Card(models.Model):
    """
    Modèle représentant une carte Pokémon.
    """
    RARITY_CHOICES = [
        ('COMMON', 'Common'),
        ('UNCOMMON', 'Uncommon'),
        ('RARE', 'Rare'),
        ('HOLORARE', 'Holo Rare'),
        ('ULTRARARE', 'Ultra Rare'),
        ('SECRETRARE', 'Secret Rare'),
    ]

    name = models.CharField(max_length=100)
    set_name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)
    image_url = models.URLField()
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    description = models.TextField(blank=True)
    release_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['set_name', 'number']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.set_name} #{self.number})"