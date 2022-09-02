from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from .models import Subscription


# Update subscription and unsubscription time
@receiver(pre_save, sender=Subscription)
def update_timestamps(sender, instance, **kwargs):
    if instance.id is not None:
        previous = Subscription.objects.get(id=instance.id)
        if (previous.active != instance.active) and (instance.active == False):
            instance.unsubscribed_date = now()
        elif (previous.active != instance.active) and (instance.active == True):
            instance.subscribed_date = now()
