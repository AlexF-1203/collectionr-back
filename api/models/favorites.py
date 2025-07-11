from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .card import Card

class Favorites(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'card']
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'

    def __str__(self):
        return f"{self.user.username}'s favorite: {self.card.name}"

    def clean(self):
        if not self.pk:
            favorite_count = Favorites.objects.filter(user=self.user).count()
            if favorite_count >= 10:
                raise ValidationError("Vous ne pouvez pas avoir plus de 10 cartes favorites.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
