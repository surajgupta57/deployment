from celery import shared_task
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from notifications.models import Notification
from notifications.signals import notify

from accounts.models import User
from articles.models import ExpertArticle, ExpertArticleComment
from parents.models import ParentProfile

#logger = get_task_logger(__name__)

from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.conf import settings
logger = get_task_logger(__name__)

@task(name="send_article_comment_notify_mail")
def send_article_comment_notify_mail(attendee_id,url):
    attendee = User.objects.get(pk=attendee_id)
    message = render_to_string("discussion/discussion.html",{"name":attendee.first_name,"url":"https://ezyschooling.com"+str(url)})
    send_mail(
        subject="Ezyschooling Notification",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=[attendee.email],
        fail_silently=False,
    )

# @shared_task
@task(name="article_notification_create_task")
def article_notification_create_task(article_id, user_id):
    try:
        article = ExpertArticle.objects.get(pk=article_id, status="P")
        article_content_type = ContentType.objects.get_for_model(article)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=article.created_by.user,
                    verb="liked your article",
                    target=article,
                )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            notify.send(
                user.expert_user,
                recipient=article.created_by.user,
                verb="liked your article",
                target=article,
            )

    except ObjectDoesNotExist:
        logger.info(f"Article did not found with id {article_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="article_notification_delete_task")
def article_notification_delete_task(article_id, user_id):
    try:
        article = ExpertArticle.objects.get(pk=article_id, status="P")
        article_content_type = ContentType.objects.get_for_model(article)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False
        if user.is_parent:
            parent = ParentProfile.objects.only("id").get(id=user.current_parent)
            parent_content_type = ContentType.objects.get_for_model(parent)
            Notification.objects.filter(
                actor_content_type=parent_content_type,
                actor_object_id=parent.id,
                recipient=article.created_by.user,
                target_content_type=article_content_type,
                target_object_id=article_id,
                action_object_content_type__isnull=True,
            ).delete()
        if user.is_expert:
            expert_content_type = ContentType.objects.get_for_model(user.expert_user)
            Notification.objects.filter(
                actor_content_type=expert_content_type,
                actor_object_id=user.expert_user.id,
                recipient=article.created_by.user,
                target_content_type=article_content_type,
                target_object_id=article_id,
                action_object_content_type__isnull=True,
            ).delete()
    except ObjectDoesNotExist:
        logger.info(f"Article Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="article_comment_notification_create_task")
def article_comment_notification_create_task(comment_id, user_id):
    try:
        article_comment = ExpertArticleComment.objects.get(pk=comment_id)
        article_comment_content_type = ContentType.objects.get_for_model(
            article_comment
        )

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                if article_comment.parent:
                    notify.send(
                        parent,
                        recipient=article_comment.parent.user,
                        verb="liked your comment",
                        target=article_comment,
                    )
                elif article_comment.expert:
                    notify.send(
                        parent,
                        recipient=article_comment.expert.user,
                        verb="liked your comment",
                        target=article_comment,
                    )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            if article_comment.parent:
                notify.send(
                    user.expert_user,
                    recipient=article_comment.parent.user,
                    verb="liked your comment",
                    target=article_comment,
                )
            elif article_comment.expert:
                notify.send(
                    user.expert_user,
                    recipient=article_comment.expert.user,
                    verb="liked your comment",
                    target=article_comment,
                )

    except ObjectDoesNotExist:
        logger.info(f"Article Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="article_comment_notification_delete_task")
def article_comment_notification_delete_task(comment_id, user_id):
    try:
        article_comment = ExpertArticleComment.objects.get(pk=comment_id)
        article_comment_content_type = ContentType.objects.get_for_model(
            article_comment
        )

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        recipient = None
        if article_comment.parent:
            recipient = article_comment.parent.user
        elif article_comment.expert:
            recipient = article_comment.expert.user

        if recipient:
            if user.is_parent:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                parent_content_type = ContentType.objects.get_for_model(parent)
                Notification.objects.filter(
                    actor_content_type=parent_content_type,
                    actor_object_id=parent.id,
                    recipient=recipient,
                    target_content_type=article_comment_content_type,
                    target_object_id=comment_id,
                    action_object_content_type__isnull=True,
                ).delete()

            if user.is_expert:
                expert_content_type = ContentType.objects.get_for_model(
                    user.expert_user
                )
                Notification.objects.filter(
                    actor_content_type=expert_content_type,
                    actor_object_id=user.expert_user.id,
                    recipient=recipient,
                    target_content_type=article_comment_content_type,
                    target_object_id=comment_id,
                    action_object_content_type__isnull=True,
                ).delete()

    except ObjectDoesNotExist:
        logger.info(f"Article Comment Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="article_comment_create_notification_create_task")
def article_comment_create_notification_create_task(
    article_id, user_id, comment_id, user_type="parent"
):
    try:
        article = ExpertArticle.objects.get(pk=article_id, status="P")

        try:
            article_comment = ExpertArticleComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Article Comment did not found with id {comment_id}")
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user_type == "parent":
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=article.created_by.user,
                    verb="commented on your article",
                    target=article,
                    action_object=article_comment,
                )
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            notify.send(
                user.expert_user,
                recipient=article.created_by.user,
                verb="commented on your article",
                target=article,
                action_object=article_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Article did not found with id {article_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="article_comment_thread_create_notification_create_task")
def article_comment_thread_create_notification_create_task(
    article_id, user_id, comment_id, parent_comment_id=None, user_type="parent"
):

    try:
        article = ExpertArticle.objects.get(pk=article_id, status="P")

        try:
            article_comment = ExpertArticleComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Article Comment did not found with id {comment_id}")
            return False

        try:
            article_parent_comment = ExpertArticleComment.objects.get(
                pk=parent_comment_id
            )
        except ObjectDoesNotExist:
            logger.info(
                f"Article Parent Comment did not found with id {parent_comment_id}"
            )
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if article_parent_comment.parent:
            if article_parent_comment.parent == article_comment.parent:
                logger.info(f"Article and Article Comment Parent User are same")
                return False
            recipient = article_parent_comment.parent.user
        elif article_parent_comment.expert:
            if article_parent_comment.expert == article_comment.expert:
                logger.info(f"Article and Article Comment Expert User are same")
                return False
            recipient = article_parent_comment.expert.user

        if user_type == "parent":
            try:
                send_article_comment_notify_mail(article_parent_comment.parent.user.id,article.get_absolute_url())
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=recipient,
                    verb="replied to your article comment",
                    target=article,
                    action_object=article_comment,
                )
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            notify.send(
                user.expert_user,
                recipient=recipient,
                verb="replied to your article comment",
                target=article,
                action_object=article_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Article did not found with id {article_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="send_article_tags_follower_notification_task")
def send_article_tags_follower_notification_task(article_id):

    try:
        article = ExpertArticle.objects.get(pk=article_id, status="P")

        tag_follower_parent_id = article.tags.values_list("followers", flat=True)
        parents_users_id = ParentProfile.objects.filter(
            id__in=tag_follower_parent_id
        ).values_list("user_id", flat=True)
        users = User.objects.filter(id__in=parents_users_id)
        if (
            ParentProfile.objects.filter(id__in=tag_follower_parent_id)
            .values_list("user_id", flat=True)
            .exists()
        ):
            notify.send(
                article.created_by,
                recipient=users,
                verb="new article is posted in the topics you have followed",
                target=article,
            )
            logger.info("Notification Successfully sent")
            return True
        logger.info("No parent follow any tags in this article")
        return True

    except ObjectDoesNotExist:
        logger.info(f"Article did not found with id {article_id}")
        return False


@task(name="atomic_sync_articles_views", queue="long-running")
def atomic_sync_articles_views(article_id):
    article = ExpertArticle.objects.get(pk=article_id)
    if article.visits.count() > article.views:
        new_views = article.visits.count() - article.views
    else:
        new_views = 0
    article.views = article.views + new_views
    # article.views = article.visits.count()
    article.save()


@task(name="bulk_sync_article_views", queue="long-running")
def bulk_sync_article_views(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        articles = ExpertArticle.objects.get_published().only("views")
        for i in articles[offset:offset + limit]:
            atomic_sync_articles_views.delay(i.id)
        if articles[offset + limit:].count() > 0:
            bulk_sync_article_views.apply_async(
                args=(offset + limit, limit), countdown=10)
