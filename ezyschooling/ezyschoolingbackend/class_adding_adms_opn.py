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

data=pd.read_csv("AvailableClasses4.csv")
for index,row in data.iterrows():
    print(row['school_id'], row['school_name'])
    school = SchoolProfile.objects.get(id=row['school_id'])
    all_classes = SchoolClasses.objects.all()
    current_classes_in_school = school.class_relation.all()
    classInSchool = row['Class_name']
    all_classes_different = classInSchool.split(",")
    school_class_final_data = [];
    for item in all_classes_different:
        if item[0] == " ":
            item = item[1:]
        if item[-1] == " ":
            item = item[:-1]
        # school_class_final_data.append(item)
        
        if item[0].islower():
            print(item)
            school_class_final_data.append(item.capitalize())
        else:
            school_class_final_data.append(item)

    for currentClass in current_classes_in_school:
        if currentClass.name in school_class_final_data:
            pass
        else:
            if ( AdmmissionOpenClasses.objects.filter(school=school,class_relation=currentClass.id)):
                obj_del = AdmmissionOpenClasses.objects.filter(school=school,class_relation=currentClass.id)
                for open_class in obj_del:
                    open_class.delete()
            school.class_relation.remove(currentClass)
            school.save()
            
    current_classes_in_school_list = list(current_classes_in_school)
    current_classes_in_school_list_final = []
    for item in current_classes_in_school_list:
        current_classes_in_school_list_final.append(item.name)

    for item in school_class_final_data:
        if item in current_classes_in_school_list_final:
            pass
        else:
            new_class = SchoolClasses.objects.get(name=item)
            print(new_class)
            school.class_relation.add(new_class)
            school.save()
    done = "Done - "
    print(done, row['school_name'])
