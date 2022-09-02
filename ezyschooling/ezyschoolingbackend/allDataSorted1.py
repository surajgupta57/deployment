import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from schools.models import *
import pandas as pd
import json
from ownelasticsearch.indexname import index


cityUploadLocation = 'customJsonData/' + index + 'citiesData.txt'
popAreaUploadLocation = 'customJsonData/' + index + 'PopAreaData.txt'
gradeUploadLocation = 'customJsonData/' + index + 'classData.txt'
boardsUploadLocation = 'customJsonData/' + index + 'BoardsData.txt'
districtUploadLocation = 'customJsonData/' + index + 'DistrictData.txt'

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

with open(cityUploadLocation, 'w') as outfile:
    json.dump(data, outfile)


# Board
data1 = {}
board_name_list = []

boardsQuery = SchoolBoard.objects.all()
for item in boardsQuery:
    board_name_list.append(item.name)

board_name_list.sort()

data1['boards'] = []
for item in board_name_list:
    boardData = SchoolBoard.objects.get(name=item)
    data1['boards'].append({
    'name': boardData.name,
    'slug': boardData.slug,
    })

with open(boardsUploadLocation, 'w') as outfile:
    json.dump(data1, outfile)

# Grade

data2 = {}
class_name_list = []

classesQuery = SchoolClasses.objects.all()
for item in classesQuery:
    class_name_list.append(item.name)

class_name_list.sort()

data2['classes'] = []
for item in class_name_list:
    classData = SchoolClasses.objects.get(name=item)
    data2['classes'].append({
    'name': classData.name,
    'slug': classData.slug,
    })

with open(gradeUploadLocation, 'w') as outfile:
    json.dump(data2, outfile)

# Popular Area

data3 = {}
poparea_name_list = []

areaQuery = DistrictRegion.objects.all()
for item in areaQuery:
    poparea_name_list.append(item.name)

poparea_name_list.sort()

data3['areas'] = []
for item in poparea_name_list:
    areaData = DistrictRegion.objects.all().filter(name=item)
    for internalItem in areaData:
        if internalItem.city:
            areaCity = internalItem.city.slug
            areaCityName = internalItem.city.name
        else:
            areaCity = 'null'
            areaCityName = 'null'

        if internalItem.district:
            areaDistrict = internalItem.district.slug
            areaDistrictName = internalItem.district.name
        else:
            areaDistrict = 'null'
            areaDistrictName = 'null'

        data3['areas'].append({
        'name': internalItem.name,
        'slug': internalItem.slug,
        'city' : areaCityName,
        'city_slug': areaCity,
        'district' : areaDistrictName,
        'district_slug': areaDistrict,
        })


with open(popAreaUploadLocation, 'w') as outfile:
    json.dump(data3, outfile)

# City Wise Pop Area

cityData = City.objects.all()
for city in cityData:
    data4 = {}
    city_poparea_name_list = []
    CityAreaQuery = DistrictRegion.objects.all().filter(city=city)
    for item in CityAreaQuery:
        city_poparea_name_list.append(item.name)

    city_poparea_name_list.sort()

    data4['areas'] = []
    for item in city_poparea_name_list:
        areaData = DistrictRegion.objects.all().filter(city=city).filter(name=item)
        for internalItem in areaData:
            if internalItem.city:
                areaCity = internalItem.city.slug
                areaCityName = internalItem.city.name
            else:
                areaCity = 'null'
                areaCityName = 'null'

            if internalItem.district:
                areaDistrict = internalItem.district.slug
                areaDistrictName = internalItem.district.name
            else:
                areaDistrict = 'null'
                areaDistrictName = 'null'

            data4['areas'].append({
            'name': internalItem.name,
            'slug': internalItem.slug,
            'city' : areaCityName,
            'city_slug': areaCity,
            'district' : areaDistrictName,
            'district_slug': areaDistrict,
            })

    cityPopAreaUploadLocation = 'customJsonData/' + index + city.slug + 'CitiesData.txt'

    with open(cityPopAreaUploadLocation, 'w') as outfile:
        json.dump(data4, outfile)

#Distruct Wise Pop Area

cityDistData = City.objects.all()
for city in cityDistData:
    if District.objects.all().filter(city=city).count() >1:
        cityDist = District.objects.all().filter(city=city)
        for dist in cityDist:
            data5 = {}
            district_poparea_name_list = []
            DistrictAreaQuery = DistrictRegion.objects.all().filter(city=city).filter(district=dist)
            for item in DistrictAreaQuery:
                district_poparea_name_list.append(item.name)
            district_poparea_name_list.sort()
            data5['areas'] = []
            for item in district_poparea_name_list:

                areaData = DistrictRegion.objects.all().filter(city=city).filter(district=dist).filter(name=item)
                for internalItem in areaData:
                    if internalItem.city:
                        areaCity = internalItem.city.slug
                        areaCityName = internalItem.city.name
                    else:
                        areaCity = 'null'
                        areaCityName = 'null'

                    if internalItem.district:
                        areaDistrict = internalItem.district.slug
                        areaDistrictName = internalItem.district.name
                    else:
                        areaDistrict = 'null'
                        areaDistrictName = 'null'

                    data5['areas'].append({
                    'name': internalItem.name,
                    'slug': internalItem.slug,
                    'city' : areaCityName,
                    'city_slug': areaCity,
                    'district' : areaDistrictName,
                    'district_slug': areaDistrict,
                    })

            distPopAreaUploadLocation = 'customJsonData/' + index + dist.slug + city.slug + 'DistrictData.txt'
            with open(distPopAreaUploadLocation, 'w') as outfile:
                json.dump(data5, outfile)

# District

data6 = {}
district_name_list = []

data6['districts'] = []
for city in City.objects.all():
    if District.objects.all().filter(city=city).count() >1:
        districtQuery = District.objects.all().filter(city=city)
        for item in districtQuery:
            district_name_list.append(item.name)
        district_name_list.sort()

for item in district_name_list:
    districtData = District.objects.get(name=item)
    if districtData.city:
        cityName = districtData.city.name
        citySlug = districtData.city.slug
    data6['districts'].append({
    'name': districtData.name,
    'slug': districtData.slug,
    'city': cityName,
    'city_slug': citySlug,
    })

with open(districtUploadLocation, 'w') as outfile:
    json.dump(data6, outfile)

# district_name_list = []
# district_slug_list = []
#
# districtQuery = District.objects.all()
#
# for item in districtQuery:
#     district_name_list.append(item.name)
#     district_slug_list.append(item.slug)
# print(district_name_list)
# print("------------")
# print(district_slug_list)
# district_name_list.sort()
# district_slug_list.sort()
# print("============")
# print(district_name_list)
# print("------------")
# print(district_slug_list)
