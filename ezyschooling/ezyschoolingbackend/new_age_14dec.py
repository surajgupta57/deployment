import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from schools.models import *
import pandas as pd

all_schools = SchoolProfile.objects.all().filter(collab=True).filter(school_city__name='Delhi')

for school_profile in all_schools:
    print(school_profile.name)
    print(school_profile.id)

    class_object = SchoolClasses.objects.get(id=21)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2018-03-01"
        end = "2019-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2018-03-01"
        end = "2019-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=12)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2018-03-01"
        end = "2019-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2018-03-01"
        end = "2019-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=22)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2018-03-01"
        end = "2019-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2018-03-01"
        end = "2019-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=17)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2018-03-01"
        end = "2019-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2018-03-01"
        end = "2019-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
# ///////////////////////////////////////////////////////////////////////////////////////////////////////
    class_object = SchoolClasses.objects.get(id=24)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2017-03-01"
        end = "2018-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2017-03-01"
        end = "2018-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=13)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2017-03-01"
        end = "2018-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2017-03-01"
        end = "2018-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=23)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2017-03-01"
        end = "2018-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2017-03-01"
        end = "2018-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
    class_object = SchoolClasses.objects.get(id=16)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2017-03-01"
        end = "2018-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2017-03-01"
        end = "2018-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
    class_object = SchoolClasses.objects.get(id=1)
    if AgeCriteria.objects.filter(school=school_profile,class_relation=class_object,session='2022-2023').exists():
        current_class = AgeCriteria.objects.get(school=school_profile,class_relation=class_object,session='2022-2023')
        start = "2016-03-01"
        end = "2017-04-30"
        current_class.start_date = start
        current_class.end_date = end
        current_class.save()
    else:
        start = "2016-03-01"
        end = "2017-04-30"
        current_class = AgeCriteria.objects.create(school=school_profile,class_relation=class_object,session='2022-2023',start_date=start,end_date=end)
