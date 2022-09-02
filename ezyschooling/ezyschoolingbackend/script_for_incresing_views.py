import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()


from admission_forms.models import *
from schools.models import *
from childs.models import *
from payments.models import *
from datetime import datetime
from dateutil import parser
import pandas as pd
from datetime import date
from articles.models import *
from analatics.models import *



views=4000

data = ExpertArticle.objects.get(id=553)
print("current_count",data.visits.count())
print("path",data.visits.all()[0].path)
path = data.visits.all()[0].path
print("content_type_id",data.visits.all()[0].content_type_id)
content_type_id = data.visits.all()[0].content_type_id
print("object_id",data.visits.all()[0].object_id)
object_id = data.visits.all()[0].object_id
for i in range(1,views): 
    PageVisited.objects.create(path=path, user_id=None, client_ip='49.36.129.126', content_type_id= content_type_id, object_id= object_id,is_mobile =False, is_tablet= False, is_touch_capable= False, is_pc= True, is_bot= False, browser_family='Chrome', browser_version= '[90, 0, 4430]', browser_version_string='90.0.4430', os_family='Windows', os_version= '[10]', os_version_string= '10', device_family='Other')
