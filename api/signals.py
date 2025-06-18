from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Collection, UserSet
from django.db.models import Count
from api.models import Set

@receiver([post_save, post_delete], sender=Collection)
def update_user_set(sender, instance, **kwargs):
    user = instance.user
    card = instance.card
    set_obj = card.set

    total_owned = Collection.objects.filter(user=user, card__set=set_obj).count()
    total_cards_in_set = Set.objects.filter(code=set_obj.code).aggregate(total=Count('card'))['total']

    if total_owned == 0:
        UserSet.objects.filter(user=user, set=set_obj).delete()
    else:
        userset, created = UserSet.objects.get_or_create(user=user, set=set_obj)
        userset.card_count = total_owned
        userset.total_cards = total_cards_in_set
        userset.completion = (total_owned / total_cards_in_set) * 100 if total_cards_in_set > 0 else 0
        userset.save()
