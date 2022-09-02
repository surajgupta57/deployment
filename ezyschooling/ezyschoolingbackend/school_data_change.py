
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from schools.models import SchoolProfile
import pandas as pd

data=pd.read_csv("CollabRectification.csv")
for index,row in data.iterrows():
    print(row['School_ID'],row['Name'])
    try:
        school_obj = SchoolProfile.objects.get(id =row['School_ID'])
        school_obj.latitude = row["latitude"]
        school_obj.longitude = row['longitude']
        school_obj.short_address = row['short_address']
        school_obj.street_address = row['street_address']
        school_obj.academic_session = row['academic_session']
        school_obj.save()
        print("All the data save successfully in db")
    except SchoolProfile.DoesNotExist:
        pass
    break
