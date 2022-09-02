import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from schools.models import AdmmissionOpenClasses, SchoolProfile,SchoolAdmissionFormFee

all_collab_schools = SchoolProfile.objects.filter(collab=True)
data = []
for school in all_collab_schools:
    if AdmmissionOpenClasses.objects.filter(school=school,admission_open="OPEN").exists():
        all_open_classes = AdmmissionOpenClasses.objects.filter(school=school,admission_open="OPEN")
        for open_class in all_open_classes:
            if not SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=open_class.class_relation).exists():
                data.append({
                    'name': school.name,
                    'id':school.id,
                })
                break

print(len(data))
import json
with open('no-admission-fee.txt', 'w') as outfile:
    json.dump(data, outfile)
