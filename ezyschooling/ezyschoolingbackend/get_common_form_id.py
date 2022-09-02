import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from admission_forms.models import SchoolApplication,FormReceipt
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Func, Value, Count
from parents.models import ParentProfile
import string
import pandas as pd
import json
unchanged_dataUploadLocation = 'customJsonData/' + "unchanged-" + 'form reciept.txt'
changed_dataUploadLocation = 'customJsonData/' + "changed-" + 'form reciept.txt'
print("Step 1")
all_apps = SchoolApplication.objects.all()
print("Step 2")
unfilterred_data = []
print("Step 3")
for i in all_apps:
    unfilterred_data.append({
        "UID":i.uid,
        "SchoolID": i.school.id
    })
print("Step 4")
filtered_data = []
print("Step 5")
for i in unfilterred_data:
    unfilterred_data_count = unfilterred_data.count(i)
    if unfilterred_data_count > 1:
        filterred_data_count = filtered_data.count(i)
        if filterred_data_count == 0:
            filtered_data.append(i)
print("Step 6")
# all_alpha_string = string.ascii_lowercase
# all_alpha = list(all_alpha_string)
all_alpha = range(50)
unchanged_data = []
changed_data = []
def get_phone(user):
    phones=[]
    parents=ParentProfile.objects.filter(user=user)
    for parent in parents:
        if(parent.phone not in phones):
            phones.append(parent.phone)
    return phones
for value in filtered_data:
    all_dupes = SchoolApplication.objects.filter(uid=value['UID'],school__id=value['SchoolID']).order_by('timestamp')
    count = 0
    for app in all_dupes:
        rec = FormReceipt.objects.get(school_applied=app)
        if app.uid == rec.receipt_id:
            user_phone = get_phone(app.user)
            unchanged_data.append({
                "Application ID: ": app.uid,
                "Receipt ID: ":rec.receipt_id,
                "Session: ": app.registration_data.session,
                "Child Name: ": app.registration_data.child_name,
                "Parent's Contact: ": user_phone,
                "School Name": app.school.name,
                "School ID": app.school.id,
                "User Email": app.user.email,
            })
        else:
            new_id = uid=value['UID'] + '_' +str(all_alpha[count])
            if len(new_id) > 15:
                new_id = uid=value['UID'] + str(all_alpha[count])
                print(app.uid)
                print(rec.receipt_id)
                print(new_id)

                count = count+1
                user_phone = get_phone(app.user)
                changed_data.append({
                    "Old Application ID: ": app.uid,
                    "Old Receipt ID: ":rec.receipt_id,
                    "New Application ID: ": new_id,
                    "New Receipt ID: ": new_id,
                    "Session: ": app.registration_data.session,
                    "Child Name: ": app.registration_data.child_name,
                    "Parent's Contact: ": user_phone,
                    "School Name": app.school.name,
                    "School ID": app.school.id,
                    "User Email": app.user.email,
                })
                app.uid = new_id
                rec.receipt_id = new_id
                app.save()
                rec.save()
            else:
                print(app.uid)
                print(rec.receipt_id)
                print(new_id)

                count = count+1
                user_phone = get_phone(app.user)
                changed_data.append({
                    "Old Application ID: ": app.uid,
                    "Old Receipt ID: ":rec.receipt_id,
                    "New Application ID: ": new_id,
                    "New Receipt ID: ": new_id,
                    "Session: ": app.registration_data.session,
                    "Child Name: ": app.registration_data.child_name,
                    "Parent's Contact: ": user_phone,
                    "School Name": app.school.name,
                    "School ID": app.school.id,
                    "User Email": app.user.email,

                })
                app.uid = new_id
                rec.receipt_id = new_id
                app.save()
                rec.save()
    print("------")

with open(unchanged_dataUploadLocation, 'w') as outfile:
    json.dump(unchanged_data, outfile)

with open(changed_dataUploadLocation, 'w') as outfile:
    json.dump(changed_data, outfile)
# t = 0
# for app in all_apps:
#     if FormReceipt.objects.filter(school_applied=app).exists():
#         rec = FormReceipt.objects.get(school_applied=app)
#         if not app.uid == rec.receipt_id:
#             t = t+1
#
# print(t)
# dupes_id = SchoolApplication.objects.values('uid').annotate(Count('id')).order_by().filter(id__count__gt=1)
# total = 0
# for item in dupes_id:
#     total = total + item['id__count']
# print(total)
# print(len(dupes_id))
# for d in dupes_id:
#     print(d['uid'])
#     all_dupes = SchoolApplication.objects.filter(uid=d['uid']).order_by('timestamp')
#     for app in all_dupes:
#         if app == all_dupes[0]:
#             pass
#         else:
#             oldaa = SchoolApplication.objects.filter(school=app.school).count()
#             print("Old School App Count: ", oldaa)
#             cval = SchoolApplication.objects.filter(school=app.school).count() + app.school.count_start + 1 - d['id__count']
#             new_id = "ezy_" + str(app.school.short_name) + "_" + str(cval)
#             print(new_id)
#             newa = SchoolApplication.objects.filter(school=app.school).count()
#             print("New School App Count: ", newa)
#     print("--------")
