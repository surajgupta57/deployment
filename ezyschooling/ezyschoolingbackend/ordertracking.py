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
today = date.today()

# data=FormOrder.objects.filter(timestamp__year=today.year,timestamp__month=today.month,timestamp__day=today.day)

data_csv=pd.read_csv('payments - 23 Feb 21.csv')


successcount=0
failcount=0
for index, row in data_csv.iterrows():
    day=23
    month=2
    year=2021
    try:
        order = FormOrder.objects.get(timestamp__year=year,timestamp__month=month,timestamp__day=day,order_id=row['order_id'])
        if order.payment_id is None:
            if(row['status']=='captured'):
                   print(row['id'],row['order_id'],row['amount'],row['contact'],row['email'],order.payment_id,order.signature,row['status'],order.child,order.child.id,order.child.user,row['created_at'])
                   successcount+=1 
        if order.payment_id is not None:
             if(row['status']=='captured'):
                 successcount+=1     
    except FormOrder.DoesNotExist:
       failcount+=1