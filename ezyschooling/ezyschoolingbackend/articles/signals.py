from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver

from .models import ExpertArticle, ExpertArticleComment
from .tasks import send_article_tags_follower_notification_task


@receiver(m2m_changed, sender=ExpertArticle.tags.through)
def send_article_tags_follower_notification(sender, instance, action, **kwargs):
    if action == "post_add":
        if instance.status == "P":
            transaction.on_commit(
                lambda: send_article_tags_follower_notification_task.delay(instance.id))


@receiver([post_save, post_delete], sender=ExpertArticleComment)
def update_article_comment_counts(sender, instance, **kwargs):
    instance.article.comment_counts = instance.article.article_comments.count()
    instance.article.save()


@receiver(m2m_changed, sender=ExpertArticle.likes.through)
def update_article_like_counts(sender, instance, action, **kwargs):
    if action in ["post_add", "post_delete"]:
        if hasattr(instance, "like_counts") and hasattr(instance, "likes"):
            instance.like_counts = instance.likes.count()
            instance.save()
