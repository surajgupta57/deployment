import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from schools.models import SchoolProfile

all_collab_school = SchoolProfile.objects.filter(collab=True)

for school in all_collab_school:
    school.contact_data_permission = True
    school.save()
