import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()

from schools.models import FeeStructure, SchoolProfile,SchoolFeesParameters

for j in FeeStructure.objects.all():
    total = 0
    for i in j.fees_parameters.all():
        if i.tenure == 'Monthly':
            total += (i.price * 12)
        elif i.tenure == 'Onetime':
            total += i.price
        elif i.tenure == 'Quarterly':
            total += (i.price * 4)
        else:
            total += i.price
    j.fee_price = (total/12)
    j.save()
