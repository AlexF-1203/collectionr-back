from django.db import models
from django.contrib.auth.models import User
from djmoney.models.fields import MoneyField

class Card(models.Model):
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

class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=20, choices=[
        ('MINT', 'Mint'),
        ('NM', 'Near Mint'),
        ('EX', 'Excellent'),
        ('GD', 'Good'),
        ('LP', 'Lightly Played'),
        ('PL', 'Played'),
        ('POOR', 'Poor'),
    ])
    is_foil = models.BooleanField(default=False)
    acquired_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-acquired_date']

    def __str__(self):
        return f"{self.user.username}'s {self.card.name} x{self.quantity}"
