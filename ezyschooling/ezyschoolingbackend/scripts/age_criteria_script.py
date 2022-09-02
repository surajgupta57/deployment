import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()


from admission_forms.models import *
from schools.models import *
from childs.models import *



schools=SchoolProfile.objects.filter(state__id=1)
class_ids =[1]

for school_obj in schools:
    for class_id in class_ids:
        class_obj = SchoolClasses.objects.get(id=class_id)
        AgeCriteria.objects.filter(school=school_obj,class_relation=class_obj).delete()
        AgeCriteria.objects.create(school=school_obj,class_relation=class_obj,start_date="2015-04-01",end_date="2016-03-31")
        print(f"{school_obj} ||| {class_obj}")
        print("***********************************************************")
print("done dana done")

