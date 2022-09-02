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
    if (type(strings) != str):
        strings = strings.rstrip()
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


df = pd.read_csv("central_east_delhi_and_shahdhara.csv")
row_iter = df.iterrows()

objs = [
    SchoolProfile(
        # user_id=1,  # defalut user for development database
        user_id = 38741, #defalut generic school user for production database

        name=row['school_name'],
        email=row['email'],
        phone_no=row['phone_no'],
        website=row['website'],
        school_timings=row['school_timings'],
        academic_session=row['academic_session'],
        short_address=row['short_address'],
        street_address=row['street_address'],
        year_established=row['year_established'],
        ownership="P",
        description=row['description'],
        student_teacher_ratio=['student_teacher_ratio']

    )
    for index, row in row_iter

]

SchoolProfile.objects.bulk_create(objs)