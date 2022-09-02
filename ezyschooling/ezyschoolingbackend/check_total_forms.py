import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from admission_forms.models import SchoolApplication
from schools.models import SchoolClasses
import pandas as pd
import json
data_out = []

UploadLocation = 'script_data/' + '-' + 'KG-NurseryClass.txt'

class_nur = SchoolClasses.objects.get(id=12)
class_kg = SchoolClasses.objects.get(id=13)

kg_forms = SchoolApplication.objects.filter(apply_for=class_kg,registration_data__session='2022-2023')
nur_forms = SchoolApplication.objects.filter(apply_for=class_nur,registration_data__session='2022-2023')

def get_phone_number(common_registration):
    numbers = []
    if common_registration.father:
        if common_registration.father.phone:
            numbers.append(common_registration.father.phone)
    if common_registration.mother:
        if common_registration.mother.phone:
            numbers.append(common_registration.mother.phone)
    if common_registration.guardian:
        if common_registration.guardian.phone:
            numbers.append(common_registration.guardian.phone)

    return numbers


for form_data in kg_forms:
    school_name = form_data.school.name
    child_name = form_data.child.name
    user_email = form_data.user.email
    data_out.append({
        'School Name' : school_name,
        'UID' : form_data.uid,
        'Child Name' :child_name,
        'Parent Contact' : get_phone_number(form_data.form),
        'Parent Email' : user_email,
        'Applied For': 'KG',
        'submission Date' : str(form_data.timestamp)
    })

for form_data in nur_forms:
    school_name = form_data.school.name
    child_name = form_data.child.name
    user_email = form_data.user.email
    data_out.append({
        'School Name' : school_name,
        'UID' : form_data.uid,
        'Child Name' :child_name,
        'Parent Contact' : get_phone_number(form_data.form),
        'Parent Email' : user_email,
        'Applied For': 'Nursery',
        'submission Date' : str(form_data.timestamp)
    })

with open(UploadLocation, 'w') as outfile:
    json.dump(data_out, outfile)
