from django.db import models
from django.conf import settings

class News(models.Model):
    """
    Modèle pour les actualités
    """

    title = models.CharField(max_length=100)
    content = models.TextField()
    main_image = models.ImageField(upload_to='news/main_image/')
    created_at = models.DateTimeField(auto_now_add=True)
