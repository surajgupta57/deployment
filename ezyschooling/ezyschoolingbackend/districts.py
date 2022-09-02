import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from django.conf import settings
import requests

hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD
school="asdasdasd"
phone_no="8408858818"
msg_template = f"Dear Parent\nYou shortlisted some schools yesterday on Ezyschooling but have not yet completed the application process.\n\n75000+ parents have already applied through Ezyschooling!\nSubmit your application form before the seats get filled in your dream schools: https://ezyschooling.com/admissions/selected/schools \n\nIf you have any doubts, feel free to contact us on 91-8766340464.\n\nRegards\nEzyschooling"
endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
if len(phone_no) ==10:
    phone_no = "91"+phone_no
print(phone_no)
request_body = {
    'method': 'SendMessage',
    'format': 'json',
    'send_to': phone_no,
    'v': '1.1',
    'auth_scheme': 'plain',
    'isHSM': True,
    'msg_type': 'HSM',
    'msg': msg_template,
    'userid': hsm_user_id,
    'password': hsm_user_password}
print(request_body)
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = requests.post(endpoint, headers=headers, data=request_body)
print(data)
