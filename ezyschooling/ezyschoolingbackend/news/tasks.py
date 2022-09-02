from django.conf import settings
from django.db.models import Count, F
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMessage

from news.models import News
from newsletters.models import Subscription

User = get_user_model()

logger = get_task_logger(__name__)


@task(name="send_news_alert_mail", queue="long-running")
def send_news_alert_mail(news_id):
    news = News.objects.filter(pk=news_id, status=News.PUBLISHED)

    subscribers = Subscription.objects.filter(
        group=Subscription.NEWS, frequency=Subscription.DAILY, active=True)

    if news.exists():
        news = news.first()
        message = render_to_string(
            "news/single_news_email_alert.html",
            {"news": news}
        )

        for i in subscribers:
            send_mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                subject=news.mini_title,
                message="",
                html_message=message,
                recipient_list=[i.get_email()]
            )
            logger.info(
                f"Sending message {news.mini_title} to recipients: {i.get_email()}")


@task(name="send_weekly_news_email", queue="long-running")
def send_weekly_news_email(subject, preview, news, email):
    news_items = News.objects.filter(pk__in=news)
    message = render_to_string("news/multi_news_email_alert.html", {
        "news": news_items,
        "preview": preview
    })
    mail = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=['query@ezyschooling.com'],
        headers={"X-SES-CONFIGURATION-SET": "Email-Tracking"}
    )
    mail.content_subtype = "html"
    mail.send()


@task(name="send_weekly_news_bulk_email", queue="long-running")
def send_weekly_news_bulk_email(subject, preview, news, offset=0, limit=100):
    subscribers = Subscription.objects.filter(
        group=Subscription.NEWS, frequency=Subscription.WEEKLY, active=True).order_by("-id")

    for i in subscribers[offset:offset + limit]:
        send_weekly_news_email.delay(subject, preview, news, i.get_email())
        logger.info(
            f"Sending message Weekly News Roundup to recipient: {i.get_email()}")
    if subscribers[offset+limit:].count() > 0:
        send_weekly_news_bulk_email.apply_async(
            args=(subject, preview, news, offset + limit, limit), countdown=10)


@task(name="atomic_sync_news_views", queue="long-running")
def atomic_sync_news_views(news_id):
    news = News.objects.get(pk=news_id)
    if news.visits.count() > news.views:
        new_views = news.visits.count() - news.views
    else:
        new_views = 0
    news.views = news.views + new_views
    # news.views = news.visits.count()
    news.save()


@task(name="bulk_sync_news_views", queue="long-running")
def bulk_sync_news_views(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        news = News.objects.filter(status=News.PUBLISHED)
        for i in news[offset:offset + limit]:
            atomic_sync_news_views.delay(i.id)
        if news[offset + limit:].count() > 0:
            bulk_sync_news_views.apply_async(
                args=(offset + limit, limit), countdown=10)
