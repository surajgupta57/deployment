import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

import json
from ownelasticsearch.indexname import index

cityUploadLocation = 'customJsonData/' + index + 'citiesData.txt'
popAreaUploadLocation = 'customJsonData/' + index + 'PopAreaData.txt'
gradeUploadLocation = 'customJsonData/' + index + 'classData.txt'
boardsUploadLocation = 'customJsonData/' + index + 'BoardsData.txt'
districtUploadLocation = 'customJsonData/' + index + 'DistrictData.txt'
