import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from schools.models import *
import random

allSchools = SchoolProfile.objects.all()

for item in allSchools:
    increasing_view_number = random.randint(199, 251)
    print(f"School Name - {item.name}")
    print(f"School Old Views - {item.views}")
    print(f"Add On Views - {increasing_view_number}")
    new_View = item.views + increasing_view_number
    item.views = new_View
    print(f"New View - {item.views}")
    item.save()
    print("Views Updated")
