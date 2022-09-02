import datetime

import pytz
from django.utils import timezone

from backend.logger import info_logger,error_logger

def custom_create_token(token_model, user, serializer):
    info_logger(f" Generating Token for user id {user.id}")
    token = token_model.objects.create(user=user)
    utc_now = timezone.now()
    utc_now = utc_now.replace(tzinfo=pytz.utc)
    token.created = utc_now
    token.save()
    return token
