import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()


from admission_forms.models import *
from schools.models import *
from childs.models import *
from payments.models import *
from datetime import datetime
from dateutil import parser
from datetime import date
from admission_forms.utils import calculate_points
today = date.today()

#apps = SchoolApplication.objects.all()
apps = SchoolApplication.objects.filter(school__id=317)


for app in apps:
    if app.school.point_system :
    #if app.school.point_system and ( app.total_points==0 or app.total_points==None ):
        calculate_points(app)
        print(f"points calculated for {app}")


