import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from schools.models import *
import pandas as pd
import json

data = {}
board_name_list = []

boardsQuery = SchoolBoard.objects.all()
for item in boardsQuery:
    board_name_list.append(item.name)

board_name_list.sort()

data['boards'] = []
for item in board_name_list:
    boardData = SchoolBoard.objects.get(name=item)
    data['boards'].append({
    'name': boardData.name,
    'slug': boardData.slug,
    })

with open('customJsonData/BoardsData.txt', 'w') as outfile:
    json.dump(data, outfile)
