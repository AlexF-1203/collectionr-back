from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .set import Set
from .user import User

class UserSet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    set = models.ForeignKey(Set, on_delete=models.CASCADE)
    card_count = models.IntegerField(default=0)
    total_cards = models.IntegerField(default=0)
    completion = models.DecimalField(default=0.00, decimal_places=2, max_digits=5)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'set')
