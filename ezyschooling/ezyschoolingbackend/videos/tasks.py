from celery import shared_task
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from notifications.models import Notification
from notifications.signals import notify

from accounts.models import User
from parents.models import ParentProfile
from videos.models import ExpertUserVideo, ExpertVideoComment

from .utils import fetch_youtube_views

logger = get_task_logger(__name__)


# @shared_task
@task(name="video_notification_create_task")
def video_notification_create_task(video_id, user_id):
    try:
        video = ExpertUserVideo.objects.get(pk=video_id, status="P")
        video_content_type = ContentType.objects.get_for_model(video)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only(
                    "id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=video.expert.user,
                    verb="liked your video",
                    target=video,
                )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            notify.send(
                user.expert_user,
                recipient=video.expert.user,
                verb="liked your video",
                target=video,
            )

    except ObjectDoesNotExist:
        logger.info(f"video did not found with id {video_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="video_notification_delete_task")
def video_notification_delete_task(video_id, user_id):
    try:
        video = ExpertUserVideo.objects.get(pk=video_id, status="P")
        video_content_type = ContentType.objects.get_for_model(video)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False
        if user.is_parent:
            parent = ParentProfile.objects.only(
                "id").get(id=user.current_parent)
            parent_content_type = ContentType.objects.get_for_model(parent)
            Notification.objects.filter(
                actor_content_type=parent_content_type,
                actor_object_id=parent.id,
                recipient=video.expert.user,
                target_content_type=video_content_type,
                target_object_id=video_id,
                action_object_content_type__isnull=True,
            ).delete()
        if user.is_expert:
            expert_content_type = ContentType.objects.get_for_model(
                user.expert_user)
            Notification.objects.filter(
                actor_content_type=expert_content_type,
                actor_object_id=user.expert_user.id,
                recipient=video.expert.user,
                target_content_type=video_content_type,
                target_object_id=video_id,
                action_object_content_type__isnull=True,
            ).delete()
    except ObjectDoesNotExist:
        logger.info(f"video did not found with id {video_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="video_comment_notification_create_task")
def video_comment_notification_create_task(comment_id, user_id):
    try:
        video_comment = ExpertVideoComment.objects.get(pk=comment_id)
        video_comment_content_type = ContentType.objects.get_for_model(
            video_comment)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user.is_parent:
            try:
                parent = ParentProfile.objects.only(
                    "id").get(id=user.current_parent)
                if video_comment.parent:
                    notify.send(
                        parent,
                        recipient=video_comment.parent.user,
                        verb="liked your comment",
                        target=video_comment,
                    )
                elif video_comment.expert:
                    notify.send(
                        parent,
                        recipient=video_comment.expert.user,
                        verb="liked your comment",
                        target=video_comment,
                    )
            except ObjectDoesNotExist:
                pass
        if user.is_expert:
            if video_comment.parent:
                notify.send(
                    user.expert_user,
                    recipient=video_comment.parent.user,
                    verb="liked your comment",
                    target=video_comment,
                )
            elif video_comment.expert:
                notify.send(
                    user.expert_user,
                    recipient=video_comment.expert.user,
                    verb="liked your comment",
                    target=video_comment,
                )

    except ObjectDoesNotExist:
        logger.info(f"Video Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


# @shared_task
@task(name="video_comment_notification_delete_task")
def video_comment_notification_delete_task(comment_id, user_id):
    try:
        video_comment = ExpertVideoComment.objects.get(pk=comment_id)
        video_comment_content_type = ContentType.objects.get_for_model(
            video_comment)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        recipient = None
        if video_comment.parent:
            recipient = video_comment.parent.user
        elif video_comment.expert:
            recipient = video_comment.expert.user

        if recipient:
            if user.is_parent:
                parent = ParentProfile.objects.only(
                    "id").get(id=user.current_parent)
                parent_content_type = ContentType.objects.get_for_model(parent)
                Notification.objects.filter(
                    actor_content_type=parent_content_type,
                    actor_object_id=parent.id,
                    recipient=recipient,
                    target_content_type=video_comment_content_type,
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
                    target_content_type=video_comment_content_type,
                    target_object_id=comment_id,
                    action_object_content_type__isnull=True,
                ).delete()

    except ObjectDoesNotExist:
        logger.info(f"Video Comment did not found with id {comment_id}")
        return False

    logger.info("Notification Successfully deleted")
    return True


@task(name="video_comment_create_notification_create_task")
def video_comment_create_notification_create_task(
    video_id, user_id, comment_id, user_type="parent"
):
    try:
        video = ExpertUserVideo.objects.get(pk=video_id, status="P")

        try:
            video_comment = ExpertVideoComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Video Comment did not found with id {comment_id}")
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if user_type == "parent":
            try:
                parent = ParentProfile.objects.only(
                    "id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=video.expert.user,
                    verb="commented on your video",
                    target=video,
                    action_object=video_comment,
                )
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            notify.send(
                user.expert_user,
                recipient=video.expert.user,
                verb="commented on your video",
                target=video,
                action_object=video_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Video did not found with id {video_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="video_comment_thread_create_notification_create_task")
def video_comment_thread_create_notification_create_task(
    video_id, user_id, comment_id, parent_comment_id=None, user_type="parent"
):

    try:
        video = ExpertUserVideo.objects.get(pk=video_id, status="P")

        try:
            video_comment = ExpertVideoComment.objects.get(pk=comment_id)
        except ObjectDoesNotExist:
            logger.info(f"Video Comment did not found with id {comment_id}")
            return False

        try:
            video_parent_comment = ExpertVideoComment.objects.get(
                pk=parent_comment_id)
        except ObjectDoesNotExist:
            logger.info(
                f"Video Parent Comment did not found with id {parent_comment_id}"
            )
            return False

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            logger.info(f"User did not found with id {user_id}")
            return False

        if video_parent_comment.parent:
            if video_parent_comment.parent == video_comment.parent:
                logger.info(f"Video and Video Comment Parent User are same")
                return False
            recipient = video_parent_comment.parent.user
        elif video_parent_comment.expert:
            if video_parent_comment.expert == video_comment.expert:
                logger.info(f"Video and Video Comment Expert User are same")
                return False
            recipient = video_parent_comment.expert.user

        if user_type == "parent":
            try:
                parent = ParentProfile.objects.only(
                    "id").get(id=user.current_parent)
                notify.send(
                    parent,
                    recipient=recipient,
                    verb="replied to your video comment",
                    target=video,
                    action_object=video_comment,
                )
            except ObjectDoesNotExist:
                pass

        elif user_type == "expert":
            notify.send(
                user.expert_user,
                recipient=recipient,
                verb="replied to your video comment",
                target=video,
                action_object=video_comment,
            )

    except ObjectDoesNotExist:
        logger.info(f"Video did not found with id {video_id}")
        return False

    logger.info("Notification Successfully sent")
    return True


@task(name="send_videos_tags_follower_notification_task")
def send_videos_tags_follower_notification_task(video_id):

    try:
        video = ExpertUserVideo.objects.get(pk=video_id, status="P")

        tag_follower_parent_id = video.tags.values_list("followers", flat=True)
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
                video.expert,
                recipient=users,
                verb="new video is posted in the topics you have followed",
                target=video,
            )
            logger.info("Notification Successfully sent")
            return True
        logger.info("No parent follow any tags in this video")
        return True

    except ObjectDoesNotExist:
        logger.info(f"Video did not found with id {video_id}")
        return False


@task(name="atomic_sync_youtube_views", queue="long-running")
def atomic_sync_youtube_views(video_id):
    video = ExpertUserVideo.objects.get(pk=video_id)
    view_count = fetch_youtube_views(video.url)
    video.youtube_views = view_count
    video.save()


@task(name="bulk_sync_youtube_views", queue="long-running")
def bulk_sync_youtube_views(offset=0, limit=100):
    videos = ExpertUserVideo.objects.get_published()
    for i in videos[offset:offset + limit]:
        atomic_sync_youtube_views.delay(i.id)
    if videos[offset + limit:].count() > 0:
        bulk_sync_youtube_views.apply_async(
            args=(offset + limit, limit), countdown=10)


@task(name="atomic_sync_video_views", queue="long-running")
def atomic_sync_video_views(video_id):
    video = ExpertUserVideo.objects.get(pk=video_id)
    video.views = video.visits.count()
    video.save()


@task(name="bulk_sync_video_views", queue="long-running")
def bulk_sync_video_views(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        videos = ExpertUserVideo.objects.filter(status=ExpertUserVideo.PUBLISHED)
        for i in videos[offset:offset + limit]:
            atomic_sync_video_views.delay(i.id)
        if videos[offset + limit:].count() > 0:
            bulk_sync_video_views.apply_async(
                args=(offset + limit, limit), countdown=10)
