import json

from celery.decorators import task
from celery.utils.log import get_task_logger
from django.contrib.contenttypes.models import ContentType

from accounts.models import User
from admission_informations.models import (AdmissionInformationArticle,
                                           AdmissionInformationNews,
                                           AdmissionInformationUserVideo)
from articles.models import ExpertArticle
from categories.models import Board, ExpertUserVideoCategory, SubCategory
from discussions.models import Discussion
from experts.models import ExpertUserProfile
from miscs.models import TalentHuntSubmission
from news.models import News
from quiz.models import Quiz
from schools.models import SchoolProfile, SchoolView
from tags.models import CustomTag
from videos.models import ExpertUserVideo

from .models import ClickLogEntry, PageVisited

logger = get_task_logger(__name__)


@task(name="save_request")
def save_request(
    path,
    client_ip,
    user_id,
    is_mobile,
    is_tablet,
    is_touch_capable,
    is_pc,
    is_bot,
    browser_family,
    browser_version,
    browser_version_string,
    os_family,
    os_version,
    os_version_string,
    device_family,
    object_slug,
    object_type,
):
    print("Not Storing")

    content_type = None
    object_id = None

    if object_type == "news":
        try:
            instance = News.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)
    elif object_type == "articles":
        try:
            instance = ExpertArticle.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)
    elif object_type == "videos":
        try:
            instance = ExpertUserVideo.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)
    elif object_type == "discussions":
        try:
            instance = Discussion.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)
    elif object_type == "schoolprofile":
        try:
            instance = SchoolProfile.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
            if user_id is not None:
                user = User.objects.get(id=user_id)
                if user.is_parent:
                    school_view, _ = SchoolView.objects.get_or_create(
                        school=instance, user_id=user_id)
                    school_view.count += 1
                    school_view.save()
        except Exception as e:
            logger.info(e)
    elif object_type == "talenthuntsubmission":
        try:
            instance = TalentHuntSubmission.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)
    elif object_type == "quiz":
        try:
            instance = Quiz.objects.get(slug=object_slug)
            object_id = instance.id
            content_type = ContentType.objects.get_for_model(instance)
        except Exception as e:
            logger.info(e)

    page = PageVisited(
        path=path,
        client_ip=client_ip,
        content_type=content_type,
        object_id=object_id,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_touch_capable=is_touch_capable,
        is_pc=is_pc,
        is_bot=is_bot,
        browser_family=browser_family,
        browser_version=browser_version,
        browser_version_string=browser_version_string,
        os_family=os_family,
        os_version=os_version,
        os_version_string=os_version_string,
        device_family=device_family,
    )

    if user_id is not None:
        page.user_id = user_id

    page.save()

    logger.info("Request Successfully saved")
    return 1


@task(name="click_action_task")
def click_action_task(
    path,
    client_ip,
    user_id,
    is_mobile,
    is_tablet,
    is_touch_capable,
    is_pc,
    is_bot,
    browser_family,
    browser_version,
    browser_version_string,
    os_family,
    os_version,
    os_version_string,
    device_family,
    action_flag,
    action_message,
    object_type,
    next_page_path,
    object_slug=None,
    object_id=None,
):

    content_type = None

    if object_type == "news":
        try:
            if not object_id and object_slug:
                instance = News.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(News)
        except Exception as e:
            logger.info(e)
    elif object_type == "articles":
        try:
            if not object_id and object_slug:
                instance = ExpertArticle.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(ExpertArticle)
        except Exception as e:
            logger.info(e)
    elif object_type == "videos":
        try:
            if not object_id and object_slug:
                instance = ExpertUserVideo.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(ExpertUserVideo)
        except Exception as e:
            logger.info(e)
    elif object_type == "discussions":
        try:
            if not object_id and object_slug:
                instance = Discussion.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(Discussion)
        except Exception as e:
            logger.info(e)
    elif object_type == "boards":
        try:
            if not object_id and object_slug:
                instance = Board.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(Board)
        except Exception as e:
            logger.info(e)
    elif object_type == "sub_category":
        try:
            if not object_id and object_slug:
                instance = SubCategory.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(SubCategory)
        except Exception as e:
            logger.info(e)
    elif object_type == "expert_video_category":
        try:
            if not object_id and object_slug:
                instance = ExpertUserVideoCategory.objects.get(
                    slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(
                ExpertUserVideoCategory)
        except Exception as e:
            logger.info(e)
    elif object_type == "tags":
        try:
            if not object_id and object_slug:
                instance = CustomTag.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(CustomTag)
        except Exception as e:
            logger.info(e)
    elif object_type == "expert_user":
        try:
            if not object_id and object_slug:
                instance = ExpertUserProfile.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(ExpertUserProfile)
        except Exception as e:
            logger.info(e)
    elif object_type == "quiz":
        try:
            if not object_id and object_slug:
                instance = Quiz.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(Quiz)
        except Exception as e:
            logger.info(e)
    elif object_type == "schools":
        try:
            if not object_id and object_slug:
                instance = SchoolProfile.objects.get(slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(SchoolProfile)
        except Exception as e:
            logger.info(e)
    elif object_type == "admission_information_article":
        try:
            if not object_id and object_slug:
                instance = AdmissionInformationArticle.objects.get(
                    slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(
                AdmissionInformationArticle)
        except Exception as e:
            logger.info(e)
    elif object_type == "admission_information_video":
        try:
            if not object_id and object_slug:
                instance = AdmissionInformationUserVideo.objects.get(
                    slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(
                AdmissionInformationUserVideo)
        except Exception as e:
            logger.info(e)
    elif object_type == "admission_information_news":
        try:
            if not object_id and object_slug:
                instance = AdmissionInformationNews.objects.get(
                    slug=object_slug)
                object_id = instance.id
            content_type = ContentType.objects.get_for_model(
                AdmissionInformationNews)
        except Exception as e:
            logger.info(e)

    page = ClickLogEntry(
        path=path,
        client_ip=client_ip,
        content_type=content_type,
        object_id=object_id,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        is_touch_capable=is_touch_capable,
        is_pc=is_pc,
        is_bot=is_bot,
        browser_family=browser_family,
        browser_version=browser_version,
        browser_version_string=browser_version_string,
        os_family=os_family,
        os_version=os_version,
        os_version_string=os_version_string,
        device_family=device_family,
        next_page_path=next_page_path,
        action_message=action_message,
        action_flag=action_flag,
    )

    if user_id is not None:
        page.user_id = user_id

    page.save()

    logger.info("Click Log Successfully saved")
    return 1
