from celery.decorators import task
from django.core.mail import EmailMessage, send_mail
from django.template import Context,Template
import requests
from django.conf import settings
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


from admission_forms.models import *
from schools.models import *
from childs.models import *
from django.template.loader import render_to_string


sms_content = """Dear {{parent_name}} ,
{{school_name}} has started it's admissions for 2021-22 session,Fill your form online by clicking here : {{school_profile}} and apply to the school now before the time runs out.
- Ezyschooling Team
( 8766340464)"""


@task(name = "send_admission_open_content_email" ,queue="long-running")
def send_admission_open_content_email(email,school_name,school_profile,parent_name):
    message= render_to_string("admission_forms/admission_open_email_content.html",{
        "school_name" : school_name,
        "parent_name" : parent_name,
        "school_profile" : school_profile,
    })
    mail = EmailMessage(
        subject = "Delhi School admissions for session 2021-22 are now open",
        body = message,
        from_email = settings.DEFAULT_FROM_EMAIL,
        to =[email],
        reply_to = ["query@ezyschooling.com"],
        headers = {"X-SES-CONFIGURATION-SET":"Email-Tracking"}
    )
    mail.content_subtype = "html"
    mail.send()


@task(name = "send_admission_open_content_sms" ,queue="long-running")
def send_admission_open_content_sms(phone,content,school_name,school_profile,parent_name):
    mssg = Template(content)
    message=mssg.render(Context({
        "school_name" : school_name,
        "parent_name" : parent_name,
        "school_profile" : school_profile,
    }))

    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSCH"
    }
    requests.get(url, params=data)


def emailExists(parent):
    if parent != None and parent.email!=None and parent.email!='':
        return parent
    else:
        return None


def calling_function():
    carts= ChildSchoolCart.objects.filter(school__collab=True)
    enquiries = SchoolEnquiry.objects.filter(school__collab=True)
    #enquiries = SchoolEnquiry.objects.filter(id=2065)
    #carts = ChildSchoolCart.objects.filter(id=1877)

    for enquiry_obj in enquiries:
        parent_name=enquiry_obj.parent_name
        email = enquiry_obj.email
        phone = enquiry_obj.phone_no
        school_name = enquiry_obj.school.name
        school_profile = "https://ezyschooling.com/school/profile/" + str(enquiry_obj.school.slug)

        send_admission_open_content_email.delay(email,school_name,school_profile,parent_name)
        send_admission_open_content_sms.delay(phone,sms_content,school_name,school_profile,parent_name)
        print("send enquiry mail and sms")

    for cart_item in carts:
        form = cart_item.form
        parent = emailExists(form.father) or emailExists(form.mother) or emailExists(form.guardian)
        if(parent is None):
            continue
        parent_name = parent.name
        email = parent.email
        phone = parent.phone
        school_name = cart_item.school.name
        school_profile = "https://ezyschooling.com/school/profile/" + str(cart_item.school.slug)

        send_admission_open_content_email.delay(email,school_name,school_profile,parent_name)
        send_admission_open_content_sms.delay(phone,sms_content,school_name,school_profile,parent_name)
        print("send cart mail and sms")
