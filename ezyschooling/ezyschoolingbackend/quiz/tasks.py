

from celery.decorators import task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db.models import Q
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from newsletters.models import Subscription

from .models import Quiz, QuizTakers

User = get_user_model()

logger = get_task_logger(__name__)

@task(name="send_quiz_email", queue="long-running")
def send_quiz_email(subject, preview, quizzes, email):
    quizzes = Quiz.objects.filter(pk__in=quizzes)
    message = render_to_string("quiz/quiz_alert_mail.html",{
                    "quizzes": quizzes,
                    "preview_text": preview
                })
    mail = EmailMessage(
        subject=subject,
        body = message,
        from_email = settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=['query@ezyschooling.com'],
        headers={"X-SES-CONFIGURATION-SET":"Email-Tracking"}
       )
    mail.content_subtype = "html"
    mail.send()



@task(name="send_bulk_quiz_email", queue="long-running")
def send_bulk_quiz_email(subject, preview, quizzes, offset=0, limit=100):

    subscribers = Subscription.objects.filter(
        group=Subscription.QUIZ, active=True).order_by("-id")

    for i in subscribers[offset:offset + limit]:
        send_quiz_email.delay(subject, preview, quizzes, i.get_email())
        logger.info(
           f"Sending quiz list email to recipient: {i.get_email()}")
    if subscribers[offset+limit:].count() > 0:
        send_bulk_quiz_email.apply_async(args=(subject, preview, quizzes, offset + limit, limit), countdown=10)
