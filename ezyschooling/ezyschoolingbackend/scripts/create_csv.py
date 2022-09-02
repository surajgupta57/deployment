import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from accounts.models import *
from admission_forms.models import *
from schools.models import *
from childs.models import *
from payments.models import *
from datetime import datetime
from dateutil import parser
import pandas as pd
from datetime import date
import csv

today = date.today()


# SchoolEnquirys=SchoolEnquiry.objects.filter(school__collab=True,school__region__name__in=['Noida','Gurgaon','Faridabad','Ghaziabad','Greater Noida West','Greater Noida'])
# with open('schoolenquiry.csv','w') as f1:
#     writer=csv.writer(f1)
#     writer.writerow(['collab','school','query','parentname','email','phonenoe','time'])
#     for i in SchoolEnquirys:
#         try:
#             row=[i.school.collab,
#                 i.school.name,
#                 i.query,
#                 i.parent_name,
#                 i.email,
#                 i.phone_no,
#                 i.timestamp,
#                 ]
#             writer.writerow(row)
#         except AdmmissionOpenClasses.DoesNotExist:
#             pass
# from django.db.models import Q
# user=User.objects.all().filter(is_parent=True).order_by("-id")
# user_id=[i.id for i in user]
# print(len(user_id))
# form=CommonRegistrationForm.objects.all().filter(user__in=[-3,-5])
# print(form.count())


data=User.objects.all().filter(is_parent=True).prefetch_related('user_admission_forms','forms','parent_profile','user_childs','user_enquiry').order_by("-id")

# print(data[0].__dict__)




def get_father_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.father):
               return i.father.name
            return ""
    else:
        return ""

def get_father_email(data):
    if(data.exists()):
        for i in data:
            if(i.father):
               return i.father.email
            return ""
    else:
        return ""


def get_father_phone(data):
    if(data.exists()):
        for i in data:
            if(i.father):
               return i.father.phone
            return ""
    else:
        return ""


def get_mother_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.mother):
               return i.mother.name
            return ""
    else:
        return ""

def get_mother_email(data):
    if(data.exists()):
        for i in data:
            if(i.mother):
               return i.mother.email
            return ""
    else:
        return ""


def get_mother_phone(data):
    if(data.exists()):
        for i in data:
            if(i.mother):
               return i.mother.phone
            return ""
    else:
        return ""

def get_guardian_name(data):
    if(data.exists()):
        for i in data:
            form={}
            if(i.guardian):
               return i.guardian.name
            return ""
    else:
        return ""

def get_guardian_email(data):
    if(data.exists()):
        for i in data:
            if(i.guardian):
               return i.guardian.email
            return ""
    else:
        return ""


def get_guardian_phone(data):
    if(data.exists()):
        for i in data:
            if(i.guardian):
               return i.guardian.phone
            return ""
    else:
        return ""


def get_applied_schools(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['child']=i.child.name
            form['Uid']=i.uid
            form['school_applied']=i.school.name
            form['applied_for']=i.apply_for.name
            list.append(form)
        return list
    else:
        return ""

def get_enquiry(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['query']=i.query
            form['phone']=i.phone_no
            form['email']=i.email
            form['school_applied']=i.school.name
            list.append(form)
        return list
    else:
        return ""


def get_common_form(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['short_address']=i.short_address
            form['street_address']=i.street_address
            form['pincode']=i.pincode
            form['state']= i.state
            list.append(form)
        return list
    else:
        return ""


def get_user_childs(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['name']=i.name
            form['class_applying_for']=i.class_applying_for.name
            form['dob']=i.date_of_birth
            list.append(form)
        return list
    else:
        return ""



for i in range(0,10):
    print(data[i].name,
    data[i].email,
    [j.phone for j in data[i].parent_profile.all()],
    get_father_name(data[i].user_admission_forms.all()),
    get_father_email(data[i].user_admission_forms.all()),
    get_father_phone(data[i].user_admission_forms.all()),
    get_mother_name(data[i].user_admission_forms.all()),
    get_mother_email(data[i].user_admission_forms.all()),
    get_mother_phone(data[i].user_admission_forms.all()),
    get_guardian_name(data[i].user_admission_forms.all()),
    get_guardian_email(data[i].user_admission_forms.all()),
    get_guardian_phone(data[i].user_admission_forms.all()),
    get_applied_schools(data[i].forms.all()),
    get_common_form(data[i].user_admission_forms.all()),
    get_user_childs(data[i].user_childs.all()),
    get_enquiry(data[i].user_enquiry.all()),
    )
