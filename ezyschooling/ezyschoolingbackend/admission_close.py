import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from schools.models import SchoolProfile, SchoolClasses, AdmmissionOpenClasses
from admission_forms.models import ChildSchoolCart
delhi_schools = SchoolProfile.objects.all().filter(collab=True).filter(school_city__name='Delhi')
class_pre_school = SchoolClasses.objects.get(id=21)
class_pre_primary = SchoolClasses.objects.get(id=24)
class_1 = SchoolClasses.objects.get(id=1)

for school_profile in delhi_schools:
    if AdmmissionOpenClasses.objects.filter(class_relation=class_1,school=school_profile,admission_open="OPEN",session='2022-2023').exists():
        class1 = AdmmissionOpenClasses.objects.get(class_relation=class_1,school=school_profile,admission_open="OPEN",session='2022-2023')
        print("Class 1")
        class1.admission_open="CLOSE"
        class1.save()
    if AdmmissionOpenClasses.objects.filter(class_relation=class_pre_primary,school=school_profile,admission_open="OPEN",session='2022-2023').exists():
        pre_primary = AdmmissionOpenClasses.objects.get(class_relation=class_pre_primary,school=school_profile,admission_open="OPEN",session='2022-2023')
        print("Pre Primary")
        pre_primary.admission_open="CLOSE"
        pre_primary.save()
    if AdmmissionOpenClasses.objects.filter(class_relation=class_pre_school,school=school_profile,admission_open="OPEN",session='2022-2023').exists():
        pre_school = AdmmissionOpenClasses.objects.get(class_relation=class_pre_school,school=school_profile,admission_open="OPEN",session='2022-2023')
        print("Pre School")
        pre_school.admission_open="CLOSE"
        pre_school.save()
    print(school_profile.name)
    print("------------------")
