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


def get_count(count):
    if count > 0:
        return True
    else:
        return False

def get_official_count(official):
    if official > 0:
        return True
    else:
        return False

for i in States.objects.all():
    print("states")
    count = SchoolProfile.objects.filter(school_state = i).count()
    official = SchoolProfile.objects.filter(collab=True).filter(school_state = i).count()
    # i.params = {'School Present':get_count(count),'Count':count}
    i.params = {'School Present':get_count(count),'Count':count, 'Official Present':get_official_count(official), 'official_count':official}
    i.save()

for i in City.objects.all():
    print("city")
    count = SchoolProfile.objects.filter(school_city = i).count()
    official = SchoolProfile.objects.filter(collab=True).filter(school_city = i).count()
    # i.params = {'School Present':get_count(count),'Count':count}
    i.params = {'School Present':get_count(count),'Count':count, 'Official Present':get_official_count(official), 'official_count':official}
    i.save()

for i in District.objects.all():
    print("District")
    count = SchoolProfile.objects.filter(district= i).count()
    official = SchoolProfile.objects.filter(collab=True).filter(district= i).count()
    # i.params = {'School Present':get_count(count),'Count':count}
    i.params = {'School Present':get_count(count),'Count':count, 'Official Present':get_official_count(official), 'official_count':official}
    i.save()

for i in DistrictRegion.objects.all():
    print("rEEGION")
    count = SchoolProfile.objects.filter(district_region = i).count()
    official = SchoolProfile.objects.filter(collab=True).filter(district_region = i).count()
    # i.params = {'School Present':get_count(count),'Count':count}
    i.params = {'School Present':get_count(count),'Count':count, 'Official Present':get_official_count(official), 'official_count':official}
    i.save()
