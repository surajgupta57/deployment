import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from schools.models import *
import pandas as pd

all_schools = SchoolProfile.objects.all().filter(collab=True).filter(school_city__name='Delhi')

for school_pro in all_schools:
    print(school_pro.name)
    print(school_pro.convenience_fee)
    school_pro.convenience_fee = 0
    school_pro.save()
