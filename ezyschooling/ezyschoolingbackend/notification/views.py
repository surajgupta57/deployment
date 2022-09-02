import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import site
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from webpush import send_group_notification, send_user_notification
from webpush.models import PushInformation
from .models import PushNotificationData, DeviceRegistrationToken
from accounts.models import User
from django.shortcuts import redirect, render
from .forms import WebPushDashboardForm, NewWebPushDashboardForm
from schools.models import City

def webpush_dashboard(request):
    if request.method == "POST":
        form = WebPushDashboardForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            payload = {
                "title": data["title"],
                "body": data["body"],
                "url": data["url"]
            }
            if data.get("icon", None):
                payload["icon"] = data["icon"]
            if data.get("image", None):
                payload["image"] = data["image"]
            send_group_notification(
                group_name="ezyschooling",
                payload=payload,
                ttl=1000)
            messages.success(
                request, f"Notification sent to all subscribers successfully.")
    else:
        form = WebPushDashboardForm()
    context = {
        "form": form,
        'opts': PushInformation._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'notification/webpush_dashboard.html', context)

def new_webpush_dashboard(request):
    if request.method == "POST":
        form = NewWebPushDashboardForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if int(data['city'][0]) == 0:
                city_obj = None
            else:
                city_obj = City.objects.get(id=data['city'])
            if data['online_or_boarding'] == 'all':
                pass
            elif data['online_or_boarding'] == 'boarding':
                city_obj = City.objects.get(name="Boarding Schools")
            elif data['online_or_boarding'] == 'online':
                city_obj = City.objects.get(name="Online Schools")
            payload = {
                "title": data["title"],
                "message": data["message"],
                "click_action": data["click_action"],
                "for_mobile_users": data["for_mobile_users"],
                "for_desktop_users": data["for_desktop_users"],
                "city":city_obj,
            }

            if data.get("image_url"):
                payload["image_url"] = data["image_url"]
            else:
                payload["image_url"] = None

            if not city_obj:
                new_notification = PushNotificationData.objects.create(title=payload['title'],message=payload['message'],image_url=payload['image_url'],click_action=payload['click_action'],for_mobile_users=payload['for_mobile_users'],for_desktop_users=payload['for_desktop_users'])
            else:
                new_notification = PushNotificationData.objects.create(title=payload['title'],message=payload['message'],image_url=payload['image_url'],click_action=payload['click_action'],for_mobile_users=payload['for_mobile_users'],for_desktop_users=payload['for_desktop_users'],city=payload['city'])
            messages.success(
                request, f"Notification sent to all subscribers successfully.")
            # return redirect('/notification/webpush-dashboard/sent/')
    else:
        form = NewWebPushDashboardForm()
    context = {
        "form": form,
        'opts': DeviceRegistrationToken._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'notification/new/webpush_dashboard.html', context)

def sent(request):
    context = {
        'opts': DeviceRegistrationToken._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'notification/new/thanks.html', context)
