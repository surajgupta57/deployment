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
import csv



# data = SchoolProfile.objects.all().order_by("-zipcode")

# with open('locations.csv','w') as f1:
#       writer=csv.writer(f1)
#       writer.writerow(['schoolid','school name','school email','school phone','short address','street address','city','district/region','state','pincode'])
#       for i in data:
#             writer.writerow([i.id,i.name,i.email,i.phone_no,i.short_address,i.street_address,i.city,[i.region.name if i.region else 'N/A'],[i.state.name if i.state else 'N/A'],i.zipcode])

data = Area.objects.all().order_by("id")
with open('Area_locations.csv','w') as f1:
      writer=csv.writer(f1)
      writer.writerow(['id','name',' district_region_name','district name','city name','state name'])
      for i in data:
            writer.writerow([i.id,i.name,i.district_region.name,i.district.name,i.city.name,i.state.name])


data1 = DistrictRegion.objects.all().order_by("id")
with open('DistrictRegion_locations.csv','w') as f1:
      writer=csv.writer(f1)
      writer.writerow(['id',"name",'district name','city name','state name'])
      for i in data1 :
            writer.writerow([i.id,i.name,i.district.name,i.city.name,i.state.name])

data3 = District.objects.all().order_by("id")
with open('District_locations.csv','w') as f1:
      writer=csv.writer(f1)
      writer.writerow(['id',"name",'city name','state name'])
      for i in data1 :
            writer.writerow([i.id,i.name,i.city.name,i.state.name])


data4 = City.objects.all().order_by("id")
with open('city_locations.csv','w') as f1:
      writer=csv.writer(f1)
      writer.writerow(['id',"name",'city name','state name'])
      for i in data1 :
            writer.writerow([i.id,i.name,i.state.name])
