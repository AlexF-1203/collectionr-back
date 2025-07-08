from django.db import models
from django.conf import settings


class Set(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=20, unique=True)
    tcg = models.CharField(max_length=100)
    release_date = models.DateField()
    total_cards = models.PositiveIntegerField()
    symbol_url = models.URLField(blank=True, null=True)
    image_url = models.URLField()
    release_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date']
        unique_together = ['code']

    def __str__(self):
        return f"{self.title} ({self.code})"
