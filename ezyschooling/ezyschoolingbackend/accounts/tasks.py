from celery import shared_task
from celery.decorators import task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
import os
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

@periodic_task(run_every=crontab(minute=0, hour=0)) # Execute daily at midnight.
def send_log_error_mail():
    file_path = os.path.join(settings.BASE_DIR,'google-oauth.log')
    data_file = open(file_path, 'r')
    data = data_file.readlines()
    message = render_to_string("account/log_file_mail.html", {"data": data})
    send_mail(
        subject="Log file",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=['himalaya.ezyschooling@gmail.com'],
    )
    file = open(file_path, 'w')
    file.write('')
    file.close()
