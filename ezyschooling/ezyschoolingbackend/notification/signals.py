from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import DeviceRegistrationToken,PushNotificationData
import requests
import json
from django.conf import settings

WebPushKey = settings.FIREBASE_WEBPUSH_KEY
def send_bulk_notification(title, message, image, clickAction,serverToken,queryset,type):
    icon = 'https://lh6.googleusercontent.com/-YWPkJeyKm_w/AAAAAAAAAAI/AAAAAAAAAAA/eOAsdFzO_ow/s40-c-k-mo/photo.jpg'
    for i in queryset:
        id_list = []
        if type == 'mobile':
            id_list.append(i.mobile_registration_id)
        elif type == 'desktop':
            id_list.append(i.pc_registration_id)
        elif type == 'all':
            if i.mobile_registration_id:
                id_list.append(i.mobile_registration_id)
            if i.pc_registration_id:
                id_list.append(i.pc_registration_id)
        for id in id_list:
            headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'key=' + serverToken,
                }

            body = {
                    'notification': {'title': title,
                                    'body': message,
                                    "image": image ,
                                    "icon" :icon,
                                    "click_action":clickAction,},
                    'to':
                        id,
                        'priority': 'high',
                    }
            response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
            result = response.json()
        id_list = []

@receiver(post_save, sender=PushNotificationData)
def send_notifications(sender, instance,  **kwargs):
    title, body_message, image, click_action, for_mobile, for_pc, city = instance.title, instance.message, instance.image_url, instance.click_action, instance.for_mobile_users, instance.for_desktop_users, instance.city
    serverToken = WebPushKey
    if city and city.name =="Boarding Schools":
        if for_mobile:
            queryset = DeviceRegistrationToken.objects.filter(is_boarding_school=True,mobile_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"mobile")
        elif for_pc:
            queryset = DeviceRegistrationToken.objects.filter(is_boarding_school=True,pc_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"desktop")
        else:
            queryset = DeviceRegistrationToken.objects.filter(is_boarding_school=True)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"all")

    elif city and city.name =="Online Schools":
        if for_mobile:
            queryset = DeviceRegistrationToken.objects.filter(is_online_school=True,mobile_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"mobile")
        elif for_pc:
            queryset = DeviceRegistrationToken.objects.filter(is_online_school=True,pc_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"desktop")
        else:
            queryset = DeviceRegistrationToken.objects.filter(is_online_school=True)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"all")
    elif city:
        if for_mobile:
            queryset = DeviceRegistrationToken.objects.filter(city__id=city.id,mobile_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"mobile")
        elif for_pc:
            queryset = DeviceRegistrationToken.objects.filter(city__id=city.id,pc_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"desktop")
        else:
            queryset = DeviceRegistrationToken.objects.filter(city__id=city.id)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"all")
    else:
        if for_mobile:
            queryset = DeviceRegistrationToken.objects.filter(mobile_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"mobile")
        elif for_pc:
            queryset = DeviceRegistrationToken.objects.filter(pc_registration_id__isnull=False)
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"desktop")
        else:
            queryset = DeviceRegistrationToken.objects.all()
            send_bulk_notification(title, body_message, image, click_action,serverToken,queryset,"all")
