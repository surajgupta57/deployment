from celery import shared_task
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from notifications.models import Notification
from notifications.signals import notify

from accounts.models import User
from discussions.models import Discussion, DiscussionComment
from parents.models import ParentProfile
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.conf import settings


logger = get_task_logger(__name__)

@task(name="send_discussion_mail")
def send_discussion_mail(attendee_id,url):
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
@task(name="discussion_like_notification_create_task")
def discussion_like_notification_create_task(discussion_id, user_id):
    try:
        discussion = Discussion.objects.get(pk=discussion_id, status="P")
        discussion_content_type = ContentType.objects.get_for_model(discussion)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if discussion.parent:
            recipient = discussion.parent.user
        elif discussion.expert:
            recipient = discussion.expert.user

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                if discussion.parent:
                    notify.send(
                        parent,
                        recipient=recipient,
                        verb="liked your discussion",
                        target=discussion,
                    )
                elif discussion.expert:
                    notify.send(
                        parent,
                        recipient=recipient,
                        verb="liked your discussion",
                        target=discussion,
                    )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            if discussion.parent:
                notify.send(
                    user.expert_user,
                    recipient=recipient,
                    verb="liked your discussion",
                    target=discussion,
                )
            elif discussion.expert:
                notify.send(
                    user.expert_user,
                    recipient=recipient,
                    verb="liked your discussion",
                    target=discussion,
                )

    except ObjectDoesNotExist:
        logger.info(f"discussion did not found with id {discussion_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="discussion_unlike_notification_delete_task")
def discussion_unlike_notification_delete_task(discussion_id, user_id):
    try:
        discussion = Discussion.objects.get(pk=discussion_id, status="P")
        discussion_content_type = ContentType.objects.get_for_model(discussion)

        if discussion.parent:
            recipient = discussion.parent.user
        elif discussion.expert:
            recipient = discussion.expert.user

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
                recipient=recipient,
                target_content_type=discussion_content_type,
                target_object_id=discussion_id,
                action_object_content_type__isnull=True,
            ).delete()
        if user.is_expert:
            expert_content_type = ContentType.objects.get_for_model(user.expert_user)
            Notification.objects.filter(
                actor_content_type=expert_content_type,
                actor_object_id=user.expert_user.id,
                recipient=recipient,
                target_content_type=discussion_content_type,
                target_object_id=discussion_id,
                action_object_content_type__isnull=True,
            ).delete()
    except ObjectDoesNotExist:
        logger.info(f"discussion did not found with id {discussion_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="discussion_comment_notification_create_task")
def discussion_comment_notification_create_task(comment_id, user_id):
    try:
        discussion_comment = DiscussionComment.objects.get(pk=comment_id)
        discussion_comment_content_type = ContentType.objects.get_for_model(
            discussion_comment
        )

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                if discussion_comment.parent:
                    notify.send(
                        parent,
                        recipient=discussion_comment.parent.user,
                        verb="liked your comment",
                        target=discussion_comment,
                    )
                elif discussion_comment.expert:
                    notify.send(
                        parent,
                        recipient=discussion_comment.expert.user,
                        verb="liked your comment",
                        target=discussion_comment,
                    )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            if discussion_comment.parent:
                notify.send(
                    user.expert_user,
                    recipient=discussion_comment.parent.user,
                    verb="liked your comment",
                    target=discussion_comment,
                )
            elif discussion_comment.expert:
                notify.send(
                    user.expert_user,
                    recipient=discussion_comment.expert.user,
                    verb="liked your comment",
                    target=discussion_comment,
                )

    except ObjectDoesNotExist:
        logger.info(f"Discussion Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="discussion_comment_notification_delete_task")
def discussion_comment_notification_delete_task(comment_id, user_id):
    try:
        discussion_comment = DiscussionComment.objects.get(pk=comment_id)
        discussion_comment_content_type = ContentType.objects.get_for_model(
            discussion_comment
        )

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        recipient = None
        if discussion_comment.parent:
            recipient = discussion_comment.parent.user
        elif discussion_comment.expert:
            recipient = discussion_comment.expert.user

        if recipient:
            if user.is_parent:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                parent_content_type = ContentType.objects.get_for_model(parent)
                Notification.objects.filter(
                    actor_content_type=parent_content_type,
                    actor_object_id=parent.id,
                    recipient=recipient,
                    target_content_type=discussion_comment_content_type,
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
                    target_content_type=discussion_comment_content_type,
                    target_object_id=comment_id,
                    action_object_content_type__isnull=True,
                ).delete()

    except ObjectDoesNotExist:
        logger.info(f"Discussion Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="discussion_comment_create_notification_create_task")
def discussion_comment_create_notification_create_task(
    discussion_id, user_id, comment_id, user_type="parent"
):
    try:
        discussion = Discussion.objects.get(pk=discussion_id, status="P")

        try:
            discussion_comment = DiscussionComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Discussion Comment did not found with id {comment_id}")
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if discussion.parent:
            if discussion.parent == discussion_comment.parent:
                logger.info(f"Discussion and Discussion Comment Parent User are same")
                return False
            recipient = discussion.parent.user
        elif discussion.expert:
            if discussion.expert == discussion_comment.expert:
                logger.info(f"Discussion and Discussion Comment Expert User are same")
                return False
            recipient = discussion.expert.user

        if user_type == "parent":
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=recipient,
                    verb="commented on your discussion",
                    target=discussion,
                    action_object=discussion_comment,
                )
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            notify.send(
                user.expert_user,
                recipient=recipient,
                verb="commented on your discussion",
                target=discussion,
                action_object=discussion_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Discussion did not found with id {discussion_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="discussion_comment_thread_create_notification_create_task")
def discussion_comment_thread_create_notification_create_task(
    discussion_id, user_id, comment_id, parent_comment_id=None, user_type="parent"
):

    try:
        discussion = Discussion.objects.get(pk=discussion_id, status="P")

        try:
            discussion_comment = DiscussionComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Discussion Comment did not found with id {comment_id}")
            return False

        try:
            discussion_parent_comment = DiscussionComment.objects.get(
                pk=parent_comment_id
            )
        except ObjectDoesNotExist:
            logger.info(
                f"Discussion Parent Comment did not found with id {parent_comment_id}"
            )
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if discussion_parent_comment.parent:
            if discussion_parent_comment.parent == discussion_comment.parent:
                logger.info(f"Discussion and Discussion Comment Parent User are same")
                return False
            recipient = discussion_parent_comment.parent.user
        elif discussion_parent_comment.expert:
            if discussion_parent_comment.expert == discussion_comment.expert:
                logger.info(f"Discussion and Discussion Comment Expert User are same")
                return False
            recipient = discussion_parent_comment.expert.user

        if user_type == "parent":
            try:
                parent = ParentProfile.objects.only("id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=recipient,
                    verb="replied to your discussion comment",
                    target=discussion,
                    action_object=discussion_comment,
                )
                send_discussion_mail(discussion_parent_comment.parent.user.id,discussion.get_absolute_url())
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            send_discussion_mail(discussion_parent_comment.parent.user.id,discussion.get_absolute_url())
            notify.send(
                user.expert_user,
                recipient=recipient,
                verb="replied to your discussion comment",
                target=discussion,
                action_object=discussion_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Discussion did not found with id {discussion_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="send_videos_tags_follower_notification_task")
def send_discussions_tags_follower_notification_task(discussion_id):

    try:
        discussion = Discussion.objects.get(pk=discussion_id, status="P")

        tag_follower_parent_id = discussion.tags.values_list("followers", flat=True)
        parents_users_id = ParentProfile.objects.filter(
            id__in=tag_follower_parent_id
        ).values_list("user_id", flat=True)
        users = User.objects.filter(id__in=parents_users_id)
        if (
            ParentProfile.objects.filter(id__in=tag_follower_parent_id)
            .values_list("user_id", flat=True)
            .exists()
        ):
            if discussion.parent:
                notify.send(
                    discussion.parent,
                    recipient=users,
                    verb="new discussion is posted in the topics you have followed",
                    target=discussion,
                )
                logger.info("Notification Successfully sent")
                return True
            elif discussion.expert:
                notify.send(
                    discussion.expert,
                    recipient=users,
                    verb="new discussion is posted in the topics you have followed",
                    target=discussion,
                )
                logger.info("Notification Successfully sent")
                return True
            else:
                logger.info("Creator is anonymus, so no notifications are sent")
                return False
        logger.info("No parent follow any tags in this discussion")
        return True

    except ObjectDoesNotExist:
        logger.info(f"Discussion did not found with id {discussion_id}")
        return False


@task(name="atomic_sync_discussion_views", queue="long-running")
def atomic_sync_discussion_views(discussion_id):
    discussion = Discussion.objects.get(pk=discussion_id)
    discussion.views = discussion.visits.count()
    discussion.save()


@task(name="bulk_sync_discussion_views", queue="long-running")
def bulk_sync_discussion_views(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        discussions = Discussion.objects.get_published()
        for i in discussions[offset:offset + limit]:
            atomic_sync_discussion_views.delay(i.id)
        if discussions[offset + limit:].count() > 0:
            bulk_sync_discussion_views.apply_async(
                args=(offset + limit, limit), countdown=10)
