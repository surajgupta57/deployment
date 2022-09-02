from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import News
from .tasks import send_news_alert_mail

User = get_user_model()

# For creating email tasks for a news which was previously a draft and is published later
@receiver(pre_save, sender=News)
def before_publish_news(sender, instance, **kwargs):
    if instance.id is None:
        pass
    else:
        previous = News.objects.get(id=instance.id)
        if (previous.status != instance.status) and (instance.status == News.PUBLISHED):
            send_news_alert_mail(instance.id)


# For creating email tasks for a news which was published instantly after being created
@receiver(post_save, sender=News)
def publish_news(sender, instance, created, **kwargs):
    if created:
        if instance.status == News.PUBLISHED:
            send_news_alert_mail(instance.id)
