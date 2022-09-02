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

csv=pd.read_csv('./feestructure/all_school.csv')
# fees=FeeStructure.objects.get_or_create(class_relation,school=,)
admission=SchoolFeesType.objects.get(id=1)
tutionm=SchoolFeesType.objects.get(id=2)
development=SchoolFeesType.objects.get(id=3)
other_fees=SchoolFeesType.objects.get(id=4)
misc_fee=SchoolFeesType.objects.get(id=5)

commerce=SchoolStream.objects.get(id=1)
science=SchoolStream.objects.get(id=2)
arts=SchoolStream.objects.get(id=3)

def createobjects(fees,row):
    print("working on row",row['School Name'],row['Class'],row['Stream'])
    if(pd.isnull(row['Admission Fee'])==False):
        admission_fee_obj= SchoolFeesParameters.objects.create(price=row['Admission Fee'],
                                                tenure=row['Tenure Admission Fee'],
                                                head=admission,
                                                school=fees.school)
        fees.fees_parameters.add(admission_fee_obj)

    if(pd.isnull(row['Tuition Fees (M)'])==False):
        tution_fee_obj = SchoolFeesParameters.objects.create(price=row['Tuition Fees (M)'],
                                                tenure=row['Tenure Tuition Fees (M)'],
                                                head=tutionm,
                                                school=fees.school)
        fees.fees_parameters.add(tution_fee_obj)

    if(pd.isnull(row['Tuition Fees (Q)'])==False):
        tution_fee_obj = SchoolFeesParameters.objects.create(price=row['Tuition Fees (Q)'],
                                                tenure=row['Tenure Tuition Fees (Q)'],
                                                head=tutionm,
                                                school=fees.school)
        fees.fees_parameters.add(tution_fee_obj)

    if(pd.isnull(row['Development Fees'])==False):
        Devlopment_fee_obj = SchoolFeesParameters.objects.create(price=row['Development Fees'],
                                                    tenure=row['Tenure Development Fees'],
                                                    head=development,
                                                    school=fees.school)
        fees.fees_parameters.add(Devlopment_fee_obj)

    if(pd.isnull(row['Other Fees'])==False):
        other_fee_obj = SchoolFeesParameters.objects.create(price=row['Other Fees'],
                                                tenure=row['Tenure Other Fees'],
                                                head=other_fees,
                                                school=fees.school
                                                )
        fees.fees_parameters.add(other_fee_obj)

    if(pd.isnull(row['Miscellaneous Charges'])==False):
        misc_fee_obj = SchoolFeesParameters.objects.create(head=misc_fee,
                                                        price=row['Miscellaneous Charges'],
                                                        tenure=row['Tenure Miscellaneous Charges'],
                                                        school=fees.school
                                                        )

        fees.fees_parameters.add(misc_fee_obj)


for index ,row in csv.iterrows():
    if(pd.isnull(row['Class ID'])==False and pd.isnull(row['SchoolID'])==False):
        try:
            if(pd.isnull(row['Stream ID'])):
                school = SchoolProfile.objects.get(id=row['SchoolID'])
                fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school=school)
                if fees:
                    createobjects(fees,row)
            else:
                if ((row['Class ID'] ==14) and (row['Stream']=='Commerce')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=commerce)
                    createobjects(fees,row)
                if((row['Class ID'] ==14) and (row['Stream']=='Science')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=science)
                    createobjects(fees,row)
                if ((row['Class ID'] ==14) and (row['Stream']=='Arts')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=arts)
                    createobjects(fees,row)

                if ((row['Class ID'] == 15) and (row['Stream']=='Commerce')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=commerce)
                    createobjects(fees,row)
                if((row['Class ID'] == 15) and (row['Stream']=='Science')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=science)
                    createobjects(fees,row)
                if ((row['Class ID'] ==15) and (row['Stream']=='Arts')):
                    fees=FeeStructure.objects.create(class_relation_id=row['Class ID'],school_id=row['SchoolID'],stream_relation=arts)
                    createobjects(fees,row)

        except SchoolProfile.DoesNotExist:
            print("Doesnot exist",row['Class'] ,row['Stream'], row['School Name'])
           
    else:
        print("either class id is null or school id is null",row['School Name'])    

        
        

        

       


