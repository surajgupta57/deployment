import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from schools.models import SchoolProfile
import csv
import pandas as pd
data=pd.read_csv("paid_list_school.csv")
for index,row in data.iterrows():
    print(row['School_Id'], row['School Name'])
    try:
        school_profile=SchoolProfile.objects.get(id=row['School_Id'])
        school_profile.counselling_data_permission = True
        school_profile.save()
    except SchoolProfile.DoesNotExist:
        pass
