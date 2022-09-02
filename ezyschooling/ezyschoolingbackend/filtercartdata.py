import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from admission_forms.models import *
from schools.models import *
from childs.models import *
from payments.models import *
from accounts.models import *
from datetime import datetime
from dateutil import parser
import pandas as pd
from datetime import date
import csv

# today = date.today()
# # SchoolApplication
# childdata=ChildSchoolCart.objects.filter(timestamp__year=2021,timestamp__month=3,timestamp__day__in=[15,16,34]).order_by('timestamp')
#childdata=ChildSchoolCart.objects.filter(timestamp__year=2021,school__region__name__in=['Noida','Gurgaon','Faridabad','Ghaziabad','Greater Noida West','Greater Noida']).order_by('timestamp')
#SchoolEnquiry=SchoolEnquiry.objects.filter(school=i.school,user=i.child.user)
# with open('blankfieldsinfo_ALL.csv','w') as f1:
#     writer=csv.writer(f1)
#     writer.writerow(['useremail','childid','chilsd.name','school.name','blankcommonform%','blankchildform%','blankfatherform%','blankmotherform%','blacnkguardianform%'])
#     for i in childdata:
#         if i.form:
#             formdata=i.form.__dict__
#             blank_formdata_fields=[]
#             for j in formdata.keys():
#                     if(formdata[j]== None or formdata[j]=='' or formdata[j]=='null' ):
#                         # print(j,formdata[j])
#                         blank_formdata_fields.append(j)
#             blankcommon=str(len(blank_formdata_fields))+"/"+str(len(formdata))
        

#         if i.child:
#             childdata= i.child.__dict__
#             blank_childdata_fields=[]
#             for j in childdata.keys():
#                 if(childdata[j]== None or childdata[j]=='' or childdata[j]=='null'):
#                     # print(j,childdata[j])
#                     blank_childdata_fields.append(j)
#             blankchild=str(len(blank_childdata_fields))+"/"+str(len(formdata))


#         if i.form.father:
#             fatherdata= i.form.father.__dict__
#             blank_fatherdata_fields=[]
#             for j in fatherdata.keys():
#                     if(fatherdata[j]== None or fatherdata[j]=='' or fatherdata[j]=='null'):
#                         # print(j,fatherdata[j])
#                         blank_fatherdata_fields.append(j)
#             blankfather = str(len(blank_fatherdata_fields))+"/"+str(len(formdata))
        

#         if i.form.mother:
#             motherdata= i.form.mother.__dict__
#             blank_motherdata_fields=[]
#             for j in motherdata.keys():
#                 if(motherdata[j]== None or motherdata[j]=='' or  motherdata[j]=='null'):
#                     # print(j,motherdata[j])
#                     blank_motherdata_fields.append(j)
#             blankmother = str(len(blank_motherdata_fields))+"/"+str(len(formdata))


#         if i.form.guardian:
#             guardiandata= i.form.guardian.__dict__
#             blank_guardiandata_fields=[]
#             for j in guardiandata.keys():
#                 if(guardiandata[j]== None or guardiandata[j]=='' or guardiandata[j]=='null'):
#                     # print(j,guardiandata[j])
#                     blank_guardiandata_fields.append(j)
#             blankguardian = str(len(blank_guardiandata_fields))+"/"+str(len(formdata))

#         if (not i.form.father):
#             blankfather = 'N/A' 
#             blank_fatherdata_fields='N/A'
#         if ( not i.form.mother):
#             blankmother= 'N/A'
#             blank_motherdata_fields='N/A'
#         if ( not i.form.guardian):
#             blankguardian = 'N/A' 
#             blank_guardiandata_fields='N/A'
#         writer.writerow([i.child.user.email,i.child.id,i.child.name,i.school.name,blankcommon,blankchild,blankfather,blankmother,blankguardian])


#     writer.writerow(['collab','classapplyfor','fatherphone','fathername','motherphone','mothername','guardianphone','guardianame','useremail','userphone','time','schoolname'])
#     for i in childdata:    
#         row=[i.school.collab,
#                 i.child.class_applying_for,
#                 i.form.father.phone if (i.form.father) else 'N/A',
#                 i.form.mother.phone if (i.form.mother) else 'N/A',
#                 i.form.guardian.phone if(i.form.guardian) else 'N/A',
#                 i.form.father.name if (i.form.father) else 'N/A',
#                 i.form.mother.name if (i.form.mother) else 'N/A',
#                 i.form.guardian.name if(i.form.guardian) else 'N/A',
#                 i.form.user.email,
#                 i.form.phone_no,
#                 i.timestamp,
#                 i.school.name.title(),
#             ]
#         writer.writerow(row)
      
       
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
            if((i.short_address != None) or (i.street_address != None) or (i.city != None) or (i.pincode != None) or (i.state !=None)):
                address=i.short_address+" "+i.street_address+" "+i.city+" "+str(i.pincode)+" "+i.state
                if address not in list:
                    list.append(address)
        return '  ||'.join(list)
    else:
        return ""


def get_user_childs(data):
    if(data.exists()):
        list=[]
        for i in data:
            form={}
            form['name']=i.name
            if(i.class_applying_for):
                form['class_applying_for']=i.class_applying_for.name
            else:
                form['class_applying_for']='N/A'
            form['age']=i.age_str
            if form not in list:
                list.append(form)
        return list
    else:
        return ""

def get_phoneno(data):
    if(data.exists()):
        phone_list=[]
        for i in data:
            if(i.phone != None):
                if(i.phone not in phone_list):
                    phone_list.append(i.phone)
            else:
                pass
        return ','.join(map(str, phone_list))
    else:
        return "" 


def get_cart_details(data):
    if (data.exists()):
        cart_list=[]
        for i in data:
            string = """
                     {username} have added {schoolname} in cart applying for {child_name} and for {applying_for}
                     """
            string = string.format(username=i.user.first_name,
                                schoolname=i.school.name,
                                child_name=i.child.name,
                                applying_for=i.child.class_applying_for.name)
            cart_list.append(string)
        return ','.join(cart_list)
    else:
        return ""

def get_street_address(data):
    if(data.exists()):
        return data[0].street_address
    else:
        return ""

def get_parent_city(data):
    if(data.exists()):
        return data[0].city
    else:
        return ""

def get_parent_state(data):
    if(data.exists()):
        return data[0].state
    else:
        return ""

def get_parent_mothly_budget(data):
    if(data.exists()):
        return data[0].monthly_budget
    else:
        return ""


def get_parent_pincode(data):
    if(data.exists()):
        return data[0].pincode
    else:
        return ""

def get_parent_country(data):
    if(data.exists()):
        return data[0].country
    else:
        return ""



data=User.objects.all().filter(is_parent=True).prefetch_related('user_admission_forms','forms','parent_profile','user_childs','user_enquiry','child_cart_user','parent_address_user').order_by("-id")
with open('alldata.csv','w') as f1:
    writer=csv.writer(f1)
    fieldnames=[
        'Date Join',
        'User',
        'Email',
        'Phone',
        'Street Address',
        'City',
        'State',
        'Pincode',
        'Country',
        'Monthly Budget',
        'Father Name',
        'Father Email',
        'Father Phone',
        'Mother Name',
        'Mother Email',
        'Mother Phone',
        'Guardian Name',
        'Guardian Email',
        'Guardian Phone',
        'Applied School list',
        'Address List',
        'Childs List',
        'Enquiry List',
        'Cart Items Details'
    ]
    writer.writerow(fieldnames)
    for i in data:
        print(i)
        writer.writerow([
        i.date_joined.strftime("%d-%m-%Y"),
        i.name,
        i.email,
        get_phoneno(i.parent_profile.all()),
        get_street_address(i.parent_address_user.all()),
        get_parent_city(i.parent_address_user.all()),
        get_parent_state(i.parent_address_user.all()),
        get_parent_pincode(i.parent_address_user.all()),
        get_parent_country(i.parent_address_user.all()),
        get_parent_mothly_budget(i.parent_address_user.all()),
        get_father_name(i.user_admission_forms.all()),
        get_father_email(i.user_admission_forms.all()),
        get_father_phone(i.user_admission_forms.all()),
        get_mother_name(i.user_admission_forms.all()),
        get_mother_email(i.user_admission_forms.all()),
        get_mother_phone(i.user_admission_forms.all()),
        get_guardian_name(i.user_admission_forms.all()),
        get_guardian_email(i.user_admission_forms.all()),
        get_guardian_phone(i.user_admission_forms.all()),
        get_applied_schools(i.forms.all()),
        get_common_form(i.user_admission_forms.all()),
        get_user_childs(i.user_childs.all()),
        get_enquiry(i.user_enquiry.all()),
        get_cart_details(i.child_cart_user.all())]
        )
    