import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from admission_forms.models import *
from schools.models import *
from admission_forms.models import *

all_cart_item = ChildSchoolCart.objects.all()

for item in all_cart_item:
    print(item)
    print(item.id)
    if item.school.school_city:
        if item.school.school_city.name == "Delhi":
            if item.session == "2021-2022":
                item.delete()
                print("Done")
