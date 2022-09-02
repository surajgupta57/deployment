import base64

import pyotp
import requests
from django.conf import settings
from django.utils import timezone

from phones.models import PhoneNumber


def generate_otp(secret):
    totp = pyotp.TOTP(secret, interval=settings.OTP_VALIDITY_TIME)
    return totp.now()


def verify_otp(secret, code):
    totp = pyotp.TOTP(secret, interval=settings.OTP_VALIDITY_TIME)
    return totp.verify(code)


def generate_secret(time, key):
    timestamp = time.astimezone(timezone.get_current_timezone())
    data = f"{str(timestamp)}-{key}"
    data = data.encode("utf-8")
    return base64.b32encode(data)


def send_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID":"1207162247127424387"
    }
    requests.get(url, params=data)


def send_verification_code(phone_id):
    phone = PhoneNumber.objects.get(pk=phone_id)
    secret = generate_secret(phone.created_at, settings.SECRET_KEY)
    code = generate_otp(secret)
    validity = settings.OTP_VALIDITY_TIME // 60
    message = f"""
    Your OTP for mobile verification is {code}.
    OTP is valid for {validity} minutes and should not be shared with anyone.
    - Ezyschooling Team
    """
    send_sms(phone.number, message)


def check_verification_code(phone_id, code):
    phone = PhoneNumber.objects.get(pk=phone_id)
    secret = generate_secret(phone.created_at, settings.SECRET_KEY)
    return verify_otp(secret, code)
