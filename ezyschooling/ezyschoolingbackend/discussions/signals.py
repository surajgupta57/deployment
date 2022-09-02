from django.db import transaction
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Discussion
from .tasks import send_discussions_tags_follower_notification_task


@receiver(m2m_changed, sender=Discussion.tags.through)
def send_discussion_tags_follower_notification(sender, instance, action, **kwargs):
    if action == "post_add":
        if instance.status == "P":
            transaction.on_commit(
                lambda: send_discussions_tags_follower_notification_task.delay(
                    instance.id
                )
            )
