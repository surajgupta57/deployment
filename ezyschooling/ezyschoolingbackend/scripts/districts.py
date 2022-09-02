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

# list = ['West Delhi','Central Delhi','East Delhi','North Delhi','North East Delhi','North West Delhi'
# ,'Shahdara','South Delhi','South East Delhi','South West Delhi','West Delhi']


# for i in list:
#     District.objects.create(name=i,state_id=1,city_id=1,country_id=1)


# data=pd.read_csv('./List Of North Delhi District.xlsx - Sheet1.csv')

# for id ,rows in data.iterrows():
#     print(rows['Areas'],rows['Pincode'])
#     region ,cond = DistrictRegion.objects.get_or_create(name=rows['Areas'],district_id=4,state_id=1,city_id=1,country_id=1)
#     pincode ,cond= Pincode.objects.get_or_create(pincode=rows['Pincode'],type='District regions')
#     # print(pincode)
#     region.pincode.add(pincode)
#     region.save()



def remove_space(str):
     str  = str.rstrip()
     str = str.lstrip()
     return str


# data=pd.read_csv('./location/LocationSet2 - Sheet1.csv')

# for id ,row in data.iterrows():
#      print(row['country'],row['state'],row['city'],row['district'],row['district_region'],row['area'],row['pincode'])
#     # print(type(row['country']),type(row['state']),type(row['city']),type(row['district']),type(row['district_region']),type(row['area']),type(row['pincode']))
#      countryobj,con_created=Country.objects.get_or_create(name=remove_space(row['country']))
#      stateobj,state_created = States.objects.get_or_create(name=remove_space(row['state']),country=countryobj)
#      cityobj,city_created = City.objects.get_or_create(name=remove_space(row['city']),country=countryobj,states=stateobj)
#      districtobj,dist_created= District.objects.get_or_create(name=remove_space(row['district']),city=cityobj,country=countryobj,state=stateobj)
#      district_region,dis_region_created = DistrictRegion.objects.get_or_create(name=remove_space(row['district_region']),district=districtobj,city=cityobj,country=countryobj,state=stateobj)
#      pincode,pincode_Created = Pincode.objects.get_or_create(pincode=row['pincode'])
#      district_region.pincode.add(pincode)
#      district_region.save()
#      if (pd.isnull(row['area']) == False):
#          area,area_created =Area.objects.get_or_create(name=remove_space(row['area']),district_region=district_region,district=districtobj,city=cityobj,country=countryobj,state=stateobj)
#          area.pincode.add(pincode)
#          area.save()

# """
data = pd.read_csv('./location/Schools 1243.csv')

for id,row in data.iterrows():
    print(row['School_id'],row['Country_id'],row['State_id'],row['City_id'],row['District_id'],row['District_region_id'],row['Area_id'],row['Pincode'])
    try :
        schoolprofile = SchoolProfile.objects.get(id=row['School_id'])
        if (pd.isnull(row['Country_id']) == False):
            country = Country.objects.get(id=row['Country_id'])
            schoolprofile.school_country  = country
        if (pd.isnull(row['State_id']) == False):    
            state = States.objects.get(id=row['State_id'])
            schoolprofile.school_state = state
        if (pd.isnull(row['City_id']) == False):
            city = City.objects.get(id=row['City_id'])
            schoolprofile.school_city = city
        if (pd.isnull(row['District_id']) == False):
            district = District.objects.get(id=row['District_id'])
            schoolprofile.district = district
        if (pd.isnull(row['District_region_id']) == False):
            district_region = DistrictRegion.objects.get(id=row['District_region_id'])
            schoolprofile.district_region = district_region
        schoolprofile.save()
    except SchoolProfile.DoesNotExist:
        print(row['School_id'])

