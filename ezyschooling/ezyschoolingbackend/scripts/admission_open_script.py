import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()

from admission_forms.models import *
from schools.models import *
from childs.models import *



schools=SchoolProfile.objects.filter(collab=True)
class_ids =[12]

for school_obj in schools:
    for class_id in class_ids:
        class_obj = SchoolClasses.objects.get(id=class_id)
        AdmmissionOpenClasses.objects.filter(class_relation=class_obj,school=school_obj).delete()
        AdmmissionOpenClasses.objects.create(class_relation=class_obj,school=school_obj,admission_open="OPEN",available_seats=1000,last_date="2021-03-04",session="2021-2022")
        SchoolAdmissionFormFee.objects.filter(class_relation=class_obj,school_relation=school_obj).delete()
        SchoolAdmissionFormFee.objects.create(class_relation=class_obj,school_relation=school_obj,form_price=25)
        print(f"{school_obj} ||| {class_obj}")
        print("***********************************************************")
print("done dana done")

