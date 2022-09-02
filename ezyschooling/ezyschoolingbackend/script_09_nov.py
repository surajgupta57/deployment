import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from admission_forms.models import *
from schools.models import *

all_admission_open_classes = AdmmissionOpenClasses.objects.all()

for item in all_admission_open_classes:
    print(item)
    print(item.id)
    if item.admission_open == "OPEN":
        if item.school.school_city:
            if item.school.school_city.name == "Delhi":
                if item.session == "2021-2022":
                    item.admission_open = "CLOSE"
                    item.save()
                    print("Done")
