from django.db import models
from django.conf import settings


class Set(models.Model):
    """
    Modèle représentant un set de cartes Pokémon.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    tcg = models.CharField(max_length=100)
    release_date = models.DateField()
    total_cards = models.PositiveIntegerField()
    image_url = models.URLField()
    release_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date']
        unique_together = ['user', 'code']

    def __str__(self):
        return f"{self.title} ({self.code})"