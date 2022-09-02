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
import json
​
data = pd.read_csv("fee_new2223.csv")
​
def create_fee_object(index,row,s):
    try:
        print(row['School Name'], row['Class ID'], row['Stream ID'])
        school = SchoolProfile.objects.get(id=row['School ID'])
        if pd.isna(row['Stream ID']):
            feestructure, created = FeeStructure.objects.get_or_create(school=school, class_relation_id=row['Class ID'],session=s)
        else:
            feestructure, created = FeeStructure.objects.get_or_create(school=school, class_relation_id=row['Class ID'],stream_relation_id=row['Stream ID'],session=s)
        if not pd.isna(row['Registration Fees']):
            regfee = SchoolFeesParameters.objects.create(school=school, head_id=8,tenure=row['Tenure Registration Fees'],price=row['Registration Fees'])
            feestructure.fees_parameters.add(regfee)
        if not pd.isna(row['Admission Fee']):
            addfee = SchoolFeesParameters.objects.create(school=school, head_id=1, tenure=row['Tenure Admission Fee'],price=row['Admission Fee'])
            feestructure.fees_parameters.add(addfee)
        if not pd.isna(row['Tuition Fees (A)']):
            tut_fee = SchoolFeesParameters.objects.create(school=school, head_id=2,tenure=row['Tenure Tuition Fees (A)'],price=row['Tuition Fees (A)'])
            feestructure.fees_parameters.add(tut_fee)
        if not pd.isna(row['Tuition Fees (M)']):
            tut_fee = SchoolFeesParameters.objects.create(school=school, head_id=2,tenure=row['Tenure Tuition Fees (M)'],price=row['Tuition Fees (M)'])
            feestructure.fees_parameters.add(tut_fee)
        if not pd.isna(row['Tuition Fees (Q)']):
            tut_fee = SchoolFeesParameters.objects.create(school=school, head_id=2,tenure=row['Tenure Tuition Fees (Q)'],price=row['Tuition Fees (Q)'])
            feestructure.fees_parameters.add(tut_fee)
        if not pd.isna(row['Security Fees']):
            sec_fee = SchoolFeesParameters.objects.create(school=school, head_id=9, tenure=row['Tenure Security Fees'],price=row['Security Fees'])
            feestructure.fees_parameters.add(sec_fee)
        if not pd.isna(row['Annual Fees']):
            annual_fee = SchoolFeesParameters.objects.create(school=school, head_id=7, tenure=row['Tenure Annual Fees'],price=row['Annual Fees'])
            feestructure.fees_parameters.add(annual_fee)
        if not pd.isna(row['Development Fees']):
            dev_fee = SchoolFeesParameters.objects.create(school=school, head_id=3,tenure=row['Tenure Development Fees'],price=row['Development Fees'])
            feestructure.fees_parameters.add(dev_fee)
        if not pd.isna(row['Other Fees']):
            other_fee = SchoolFeesParameters.objects.create(school=school, head_id=4, tenure=row['Tenure Other Fees'],price=row['Other Fees'])
            feestructure.fees_parameters.add(other_fee)
        if not pd.isna(row['Miscellaneous Charges']):
            misc_fee = SchoolFeesParameters.objects.create(school=school, head_id=5,tenure=row['Tenure Miscellaneous Charges'],price=row['Miscellaneous Charges'])
            feestructure.fees_parameters.add(misc_fee)
        if not pd.isna(row['Optional Fees']):
            optn_fee = SchoolFeesParameters.objects.create(school=school, head_id=11,tenure=row['Tenure Optional Fees'],price=row['Optional Fees'])
            feestructure.fees_parameters.add(optn_fee)
        if not pd.isna(row['Composite Fees']):
            compt_fee = SchoolFeesParameters.objects.create(school=school, head_id=24,tenure=row['Composite Fees Tenure'],price=row['Composite Fees'])
            feestructure.fees_parameters.add(compt_fee)
        if not pd.isna(row['Transport Fees Start']):
            if not pd.isna(row['Flexible']) and row['Flexible']==True:
                trans_fee = SchoolFeesParameters.objects.create(school=school, head_id=15,tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'],upper_price=row['Transport Fees End'],range=True)
            else:
                trans_fee = SchoolFeesParameters.objects.create(school=school, head_id=15,tenure=row['Tenure Transport Fees'],price=row['Transport Fees Start'],range=False)
            feestructure.fees_parameters.add(trans_fee)
        if not pd.isna(row['Monthly']):
            feestructure.fee_price = row['Monthly']
            feestructure.save()
        else:
            feestructure.fee_price = 0
            feestructure.save()
        feestructure.session =s
        feestructure.save()
    except SchoolProfile.DoesNotExist:
        pass

for index, row in data.iterrows():
    s1='2021-2022'
    s2='2022-2023'
    if not pd.isna(row[s1]) and row[s1]==True:
        # print(row[s1],s1, end=":")
        create_fee_object(index,row,s1)
    if not pd.isna(row[s2]) and row[s2]==True:
        # print(row[s2],s2)
        create_fee_object(index,row,s2)
