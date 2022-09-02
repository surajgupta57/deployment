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



def cond(obj):
    if obj:
        return obj.name
    else:
        return ""


def remove_space(strings):
    if(type(strings)!=str):
        strings  = strings.rstrip()
        strings = strings.lstrip()
        print(strings)
        return strings
    else:
        return " "
def check_nan(value):
    if not pd.isna(value):
        return value
    else:
        return

data=pd.read_csv("delhincr.csv")
for index,row in data.iterrows():
    print(row['school_name'],row['school_board'],row['school_format'])
    try:
        board=SchoolBoard.objects.get(name=row['school_board'])
        types=SchoolType.objects.get(name=row['school_category'])
        school_format = SchoolFormat.objects.get(title=row['school_format'])
        school_country = Country.objects.get(name=row['school_country'])
        school_state  = States.objects.get(name=row['school_state'])
        school_city  =  City.objects.get(name=row['school_city'])
        district    =   District.objects.get(name=row['district'])
        district_region,created = DistrictRegion.objects.get_or_create(name=row['district_region'],district=district)
        school= SchoolProfile.objects.create(user_id = 1, #defalut generic school user
                                                name=row['school_name'],
                                                email = row['email'],
                                                phone_no = row['phone_no'],
                                                website = row['website'],
                                                school_timings = row['school_timings'],
                                                academic_session = row['academic_session'],
                                                short_address = row['short_address'],
                                                street_address = row['street_address'],
                                                year_established = row['year_established'],
                                                ownership = "P",
                                                description = row['description'],
                                                student_teacher_ratio = row['student_teacher_ratio']
                                                )
        school.school_type = types
        school.school_format = school_format
        school.school_board = board
        school.district = district
        school.district_region = district_region
        school.school_city = school_city
        school.school_state= school_state
        school.school_country = school_country
        school.video_tour_link = check_nan(row['video_tour_link']) 
        # class_list=[i for i in row['class_relation'].split(",")]
        # for i in class_list:
        #     try:
        #         clss=SchoolClasses.objects.get(name=i)
        #         school.class_relation.add(clss)
        #     except SchoolClasses.DoesNotExist:
        #         pass
        # school.save()
    except SchoolBoard.DoesNotExist:
        pass
