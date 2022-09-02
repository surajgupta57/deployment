import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
import requests
is_Subscriber = False
from parents.models import *


phone_number =''
for i in ParentProfile.objects.filter(user = 63910):
    ParentProfile = ParentProfile.objects.filter(user = i.user).first()
    if ParentProfile and ParentProfile.phone :
        number = ParentProfile.phone 
    else:
        ParentAddress = ParentAddress.objects.filter(parent = i).first()
        number = ParentAddress.phone_no if ParentAddress and ParentAddress.phone_no else ''

phone_number = number

print(phone_number)
# data = {
#     'user_id' : 2000209370,
#     'password':'E5LEuU83',
#     'phone_number': 9882411282
# }
# user_id= 2000209370
# password ='E5LEuU83'
# phone_number = 9882411282
# if is_Subscriber ==True:
#     response = requests.post(f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_IN&format=json&userid={user_id}&password={password}&phone_number={phone_number}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
#     result = response.json()
#     print(result)
# else :
#     print("i")