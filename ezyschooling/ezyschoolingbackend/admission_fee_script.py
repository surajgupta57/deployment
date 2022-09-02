import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from schools.models import *
import pandas as pd
import json
zeroFeeUploadLocation = 'script_data/' + 'fees' + 'zeroFee.txt'
noFeeUploadLocation = 'script_data/' + 'fees' + 'noFee.txt'

all_schools = SchoolProfile.objects.all().filter(collab=True).filter(school_city__name='Delhi')
data = []
data1 = []
for school_profile in all_schools:
    all_class = []

    if AdmmissionOpenClasses.objects.filter(school=school_profile, session='2022-2023',admission_open='OPEN').exists():
        all_adm_opn_class = AdmmissionOpenClasses.objects.all().filter(school=school_profile, session='2022-2023',admission_open='OPEN')
        for class_n in all_adm_opn_class:
            class_n_value = class_n.class_relation
            if SchoolAdmissionFormFee.objects.filter(school_relation=school_profile,class_relation=class_n_value).exists():
                all_school_class_fee =  SchoolAdmissionFormFee.objects.all().filter(school_relation=school_profile,class_relation=class_n_value)
                for school_class_fee in all_school_class_fee:
                    if school_class_fee.form_price == 0:
                        print("Updating Fee")
                        data.append({
                        'School Name': school_profile.name,
                        'School ID': school_profile.id,
                        'Class Name': school_class_fee.class_relation.name,
                            })
                        school_class_fee.form_price = 25
                        school_class_fee.save()


            else:
                print("Creating Fee")
                data1.append({
                'School Name': school_profile.name,
                'School ID': school_profile.id,
                'Class Name': class_n_value.name,
                    })
                SchoolAdmissionFormFee.objects.create(school_relation=school_profile,class_relation=class_n_value,form_price=25)



with open(zeroFeeUploadLocation, 'w') as outfile:
    json.dump(data, outfile)

with open(noFeeUploadLocation, 'w') as outfile:
    json.dump(data1, outfile)
