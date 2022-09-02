import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from schools.models import *
import pandas as pd
import json

data = {}
poparea_name_list = []

areaQuery = DistrictRegion.objects.all()
for item in areaQuery:
    poparea_name_list.append(item.name)

poparea_name_list.sort()

data['areas'] = []
for item in poparea_name_list:
    areaData = DistrictRegion.objects.all().filter(name=item)
    for internalItem in areaData:
        if internalItem.city:
            areaCity = internalItem.city.name
        else:
            areaCity = 'null'

        if internalItem.district:
            areaDistrict = internalItem.district.name
        else:
            areaDistrict = 'null'

        data['areas'].append({
        'name': internalItem.name,
        'slug': internalItem.slug,
        'city': areaCity,
        'district': areaDistrict,
        })

with open('customJsonData/PopAreaData.json', 'w') as outfile:
    json.dump(data, outfile)
