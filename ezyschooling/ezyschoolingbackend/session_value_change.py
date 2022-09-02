import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from admission_forms.models import *
from schools.models import *
from childs.models import *
from payments.models import *
from datetime import datetime
from dateutil import parser
import pandas as pd
from datetime import date
from articles.models import *
from analatics.models import *
import csv
from accounts.models import *

common_registration_form = CommonRegistrationForm.objects.all()
common_registration_form_after = CommonRegistrationFormAfterPayment.objects.all()
child_cart = ChildSchoolCart.objects.all()
age_criteria = AgeCriteria.objects.all()
fee_structure = FeeStructure.objects.all()
admission_open_class = AdmmissionOpenClasses.objects.all()

print("Common Registration Form")
for item in common_registration_form:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("CRF- Done")
        item.save()

print("Common Registration Form After Payment")
for item in common_registration_form_after:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("CRFAP- Done")
        item.save()

print("School Child Cart Item")
for item in child_cart:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("Child Cart- Done")
        item.save()

print("Age Criteria")
for item in age_criteria:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("Age Criteria- Done")
        item.save()

print("Fee Structure")
for item in fee_structure:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("Fee Structure- Done")
        item.save()

print("Admission Open Classes")
for item in admission_open_class:
    if item.session == "2021-2022":
        pass
    else:
        item.session = "2021-2022"
        print(item.id)
        print("Admission Open- Done")
        item.save()