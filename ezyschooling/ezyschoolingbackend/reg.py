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
from parents.models import *


def copy_the_form_data(form_id,reg_form_id):
    data={}

    obj = CommonRegistrationForm.objects.get(id=form_id)
    list_common=['short_address','street_address','city','state','pincode','country','last_school_name','last_school_board_id',
    'last_school_address','last_school_class_id','transfer_certificate','single_parent_proof','reason_of_leaving','report_card',
    'email','phone_no','single_child','first_child','single_parent','first_girl_child','staff_ward','sibling1_alumni_name',
    'sibling2_alumni_name','sibling2_alumni_school_name_id','sibling1_alumni_proof','sibling2_alumni_proof','family_photo',
    'distance_affidavit',
    'baptism_certificate','parent_signature_upload','mother_tongue','differently_abled_proof','caste_category_certificate',
    'is_twins','second_born_child','third_born_child','lockstatus','transport_facility_required']
    list_parent= ['email','name','date_of_birth','gender','photo','companyname','aadhaar_number','transferable_job',
                'special_ground','designation','profession','special_ground_proof','parent_aadhar_card','pan_card_proof','income',
                'phone','bio','parent_type','street_address','city','state','pincode','country','education','occupation',
                'office_address','office_number','alumni_school_name_id','alumni_year_of_passing','passing_class','alumni_proof']
    list_child=['name','photo','date_of_birth','gender','gender','religion','nationality','aadhaar_number','aadhaar_card_proof','blood_group',
        'birth_certificate','address_proof','address_proof2','first_child_affidavit','vaccination_card','vaccination_card','minority_proof',
        'is_christian','minority_points','student_with_special_needs_points','armed_force_points','armed_force_proof','orphan','no_school','class_applying_for_id']
    for i in list_common:
        data[i]=obj.__dict__[i]
    if obj.child:
        child = Child.objects.get(id=obj.child.id)
        for i in list_child:
            data['child_'+str(i)] = child.__dict__[i]
    if obj.father:
        father=ParentProfile.objects.get(id=obj.father.id)
        for i in list_parent:
            data['father_'+str(i)] = father.__dict__[i]
    if obj.mother:
        mother=ParentProfile.objects.get(id=obj.mother.id)
        for i in list_parent:
            data['mother_'+str(i)] = mother.__dict__[i]
    if obj.guardian:
        guardian=ParentProfile.objects.get(id=obj.guardian.id)
        for i in list_parent:
            data['guardian_'+str(i)] = guardian.__dict__[i]
    
    copy_obj = CommonRegistrationFormAfterPayment.objects.filter(id=reg_form_id)
    copy_obj.update(**data)
    
for i in SchoolApplication.objects.all():
    if i.form:
        obj= CommonRegistrationForm.objects.get(id=i.form.id)
        reg=CommonRegistrationFormAfterPayment.obj.create(user=i.form.user)
        copy_the_form_data(obj.id,reg.id)
        print("datacopied")
        i.registration_data=reg
        i.save()


