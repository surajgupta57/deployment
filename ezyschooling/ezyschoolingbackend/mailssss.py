import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
from datetime import *
from dateutil.relativedelta import relativedelta
from admission_forms.models import ChildSchoolCart
from accounts.models import User
from schools.models import SchoolEnquiry, SchoolClassNotification
from django.template.loader import render_to_string
from parents.models import ParentProfile

# currentDate = datetime.now().date()
# yesterdayDate = currentDate - relativedelta(days=1)
# yesterdayDateTime =str(yesterdayDate) +  ' 19:00:00'
# yesterdayDateTime = datetime.strptime(yesterdayDateTime, '%Y-%m-%d %X')
# currentDateTime =str(currentDate) +  ' 09:00:00'
# currentDateTime = datetime.strptime(currentDateTime, '%Y-%m-%d %X')
# cart_data = ChildSchoolCart.objects.filter(timestamp__date__lt=currentDateTime,timestamp__date__gte=yesterdayDateTime)
# user_ids = []
# for item in cart_data:
#     user_ids.append(item.user.id)
# user_ids = set(user_ids)
#
# def atomic_cart_mail_morning(user_id):
#     user_obj = User.objects.get(id=user_id)
#     if user_obj.current_parent:
#         parent = ParentProfile.objects.get(id=user_obj.current_parent)
#         name = parent.name;
#     else:
#         name = "Parent"
#     user_cart_data = ChildSchoolCart.objects.filter(user__id=user_id).order_by('-timestamp')
#     latest_added_school = ChildSchoolCart.objects.filter(user__id=user_id).order_by('-timestamp')[:1][0]
#     total_school_inq = SchoolEnquiry.objects.filter(school=latest_added_school.school).count()
#     total_school_notification = SchoolClassNotification.objects.filter(school=latest_added_school.school).count()
#     intrested_parents = int(total_school_inq + total_school_notification + (latest_added_school.school.views*0.4))
#     total_cart_item = len(user_cart_data)
#     message = render_to_string("admission_forms/abandoned_cart_email.html",
#                                 {'username': name,
#                                 'total_cart_item':total_cart_item,
#                                 'user_cart_data':user_cart_data,
#                                 'intrested_parents':intrested_parents})
#     if not UnsubscribeEmail.objects.filter(email=email).exists:
#         send_mail(subject="Apply to the schools waiting in your cart before time runs out",
#                 message='',
#                 html_message=message,
#                 from_email='Ezyschooling <info@ezyschooling.in>',
#                 recipient_list=[email, DEFAULT_TO_PARENT_EMAIL],
#                 connection=settings.EMAIL_CONNECTION, fail_silently=False)
#         logger.info("Sending Abandoned Cart Email - Morning")

currentDate = datetime.now().date()
currentDateTimeStart =str(currentDate) +  ' 09:00:00'
currentDateTimeEnd =str(currentDate) +  ' 19:00:00'
currentDateTimeStart = datetime.strptime(currentDateTimeStart, '%Y-%m-%d %X')
currentDateTimeEnd = datetime.strptime(currentDateTimeEnd, '%Y-%m-%d %X')
print(currentDateTimeStart)
print(currentDateTimeEnd)

cart_data = ChildSchoolCart.objects.filter(timestamp__date__lte=currentDateTimeEnd,timestamp__date__gte=currentDateTimeStart)

user_ids = []
for item in cart_data:
    print(item.child.name)
    user_ids.append(item.user.id)
print(len(user_ids))
user_ids = set(user_ids)
print(user_ids)

def atomic_cart_mail_evening(user_id):
    user_obj = User.objects.get(id=user_id)
    if user_obj.current_parent:
        parent = ParentProfile.objects.get(id=user_obj.current_parent)
        name = parent.name;
    else:
        name = "Parent"
    user_cart_data = ChildSchoolCart.objects.filter(user__id=user_id).order_by('-timestamp')
    latest_added_school = ChildSchoolCart.objects.filter(user__id=user_id).order_by('-timestamp')[:1][0]
    total_school_inq = SchoolEnquiry.objects.filter(school=latest_added_school.school).count()
    total_school_notification = SchoolClassNotification.objects.filter(school=latest_added_school.school).count()
    intrested_parents = int(total_school_inq + total_school_notification + (latest_added_school.school.views*0.4))
    total_cart_item = len(user_cart_data)
    school_list = []
    for cart in user_cart_data:
        name, slug, logo, district_region, district, description = '','','','','',''
        if cart.school:
            name = cart.school.name
            slug = cart.school.slug
            if cart.school.logo:
                logo = cart.school.logo.url
            if cart.school.district_region:
                district_region = cart.school.district_region.name
            else:
                print("1")
            if cart.school.district:
                district = cart.school.district.name
            else:
                print("2")
            if cart.school.description:
                description = cart.school.description
            else:
                print("3")
        school_list.append({
        'name':name,
        'slug':slug,
        'logo':logo,
        'district_region':district_region,
        'district':district,
        'description':description,
        })
    
    message = render_to_string("admission_forms/abandoned_cart_email.html",
                                {'username': name,
                                'total_cart_item':total_cart_item,
                                'user_cart_data':school_list,
                                'intrested_parents':intrested_parents})
    # if not UnsubscribeEmail.objects.filter(email=email).exists:
    #     send_mail(subject="Apply to the schools waiting in your cart before time runs out",
    #             message='',
    #             html_message=message,
    #             from_email='Ezyschooling <info@ezyschooling.in>',
    #             recipient_list=[email, DEFAULT_TO_PARENT_EMAIL],
    #             connection=settings.EMAIL_CONNECTION, fail_silently=False)
    #     logger.info("Sending Abandoned Cart Email - Morning")
#
for i in user_ids:
    atomic_cart_mail_evening(i)
