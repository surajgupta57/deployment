from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signals import request_finished
from datetime import datetime
from .models import ParentProfile,ParentTracker,ParentAddress
from django.utils import timezone
import pytz
from accounts.api.v1.views import login_signal


@receiver(post_save, sender=ParentProfile)
def create_user_profile(sender, instance, created, **kwargs):
    instance.user.name = instance.name
    instance.user.save(update_fields=["name"])

@receiver(login_signal)
def ParentTrackRecord(**kwargs):
    if kwargs['user']:
        today = now = datetime.now()
        data=ParentProfile.objects.filter(user=kwargs['user']).first()
        address=ParentAddress.objects.filter(parent=data).first()
        if data:
            existance=ParentTracker.objects.filter(parent__user=kwargs['user'],timestamp__date=datetime.date(today)).first()
            if existance is None:
                ParentTracker.objects.create(parent=data,address=address)
            else:
                tracked_data_list=[i.pk for i in ParentTracker.objects.filter(parent__user=kwargs['user'])]
                ParentTracker.objects.filter(pk__in=tracked_data_list).update(parent=data,address=address)
