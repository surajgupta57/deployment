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
f = open('./schooldataJSON/Gurugram_Final.json',)
data= json.load(f)
print(len(data))
count=0
for i in data['school_list']:
    if "ID" in i['SCHOOL'].keys():
        for facility in (i['SCHOOL']['FACILITIES']):
            for facility,values in facility.items():
                # print(facility,values)
                for k, kv  in values.items():
                    try:
                        #print(i['SCHOOL']['NAME'],i['SCHOOL']['ID'],k,kv)
                        obj=Feature.objects.get(school_id=i['SCHOOL']['ID'],features__name=k)
                        if obj:
                            print('objectFound',obj.features.name,obj.school.name)
                            if kv=="AVAILABLE":
                                obj.exist='Yes'
                            elif kv=='NOT AVAILABLE':
                                obj.exist='No'
                            else:
                                pass
                        obj.save()
                    except Feature.DoesNotExist:
                        print(i['SCHOOL']['NAME'])
        count+=1
print(count)
