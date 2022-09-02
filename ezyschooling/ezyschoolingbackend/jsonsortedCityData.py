import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from schools.models import *
import pandas as pd
import json

data = {}
city_name_list = []

citiesQuery = City.objects.all()
for item in citiesQuery:
    city_name_list.append(item.name)

city_name_list.sort()

data['cities'] = []
for item in city_name_list:
    cityData = City.objects.get(name=item)
    data['cities'].append({
    'name': cityData.name,
    'slug': cityData.slug,
    })

with open('customJsonData/citiesData.txt', 'w') as outfile:
    json.dump(data, outfile)
