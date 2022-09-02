import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from schools.models import *
import pandas as pd
import json

data = {}
class_name_list = []

classesQuery = SchoolClasses.objects.all()
for item in classesQuery:
    class_name_list.append(item.name)

class_name_list.sort()

data['classes'] = []
for item in class_name_list:
    classData = SchoolClasses.objects.get(name=item)
    data['classes'].append({
    'name': classData.name,
    'slug': classData.slug,
    })

with open('customJsonData/classData.txt', 'w') as outfile:
    json.dump(data, outfile)
