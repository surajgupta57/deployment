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

all_admission_open_classes = AdmmissionOpenClasses.objects.all()

for item in all_admission_open_classes:
    if item.admission_open == "CLOSE":
        item.delete()
        print("Done")
