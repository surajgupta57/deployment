import json

import requests
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)


@task(name="subscribe_anonymous_user")
def subscribe_anonymous_user(email):
    url = "https://ezyschooling.freshmarketer.com/mas/api/v1/contacts"

    data = {
    "status": "subscribed",
    "email": email,
    "lists": [
            settings.FRESHMARKETER_LIST_ID
        ]
    }

    headers = {
        "fm-token": settings.FRESHMARKETER_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    requests.put(url, headers=headers, data=json.dumps(data))


@task(name="subscribe_registered_user")
def subscribe_registered_user(email):
    url = "https://ezyschooling.freshmarketer.com/mas/api/v1/contacts"

    data = {
    "status": "subscribed",
    "email": email,
    "lists": [
            settings.FRESHMARKETER_LIST_ID
        ]
    }

    headers = {
        "fm-token": settings.FRESHMARKETER_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    requests.put(url, headers=headers, data=json.dumps(data))


@task(name="unsubscribe_user")
def unsubscribe_user(email):
    url = "https://ezyschooling.freshmarketer.com/mas/api/v1/contacts"

    headers = {
        "fm-token": settings.FRESHMARKETER_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.get(f"{url}/{email}", headers=headers)

    data = r.json()
    contact_id = data["contact"]["id"]

    list_id = settings.FRESHMARKETER_LIST_ID

    unsubscribe_url = f"https://ezyschooling.freshmarketer.com/mas/api/v1/lists/{list_id}/subscribers/{contact_id}/unsubscribe"

    requests.patch(unsubscribe_url, headers=headers)
