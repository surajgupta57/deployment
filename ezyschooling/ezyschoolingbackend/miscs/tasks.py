from celery.decorators import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMessage, send_mail, get_connection
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
import gspread
import os
from backend.settings.base import DEFAULT_TO_PARENT_EMAIL, DEFAULT_TO_SCHOOL_EMAIL
from .models import AdmissionGuidance, AdmissionGuidanceProgramme,ContactUs,SponsorsRegistrations,WebinarRegistrations
from admission_forms.models import ChildSchoolCart
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@task(name="send_admission_guidance_mail")
def send_admission_guidance_mail(attendee_id):
    attendee = AdmissionGuidance.objects.get(pk=attendee_id)
    message = render_to_string("miscs/guidance_mail.html", {"slot": attendee.slot,'email': attendee.email, 'phone': attendee.phone})
    send_mail(
        subject="Thank you for registering!",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=[attendee.email, DEFAULT_TO_PARENT_EMAIL],
        fail_silently=False,
    )

@task(name="send_admission_guidance_programme_mail")
def send_admission_guidance_programme_mail(attendee_id,name):
    attendee = AdmissionGuidanceProgramme.objects.get(pk=attendee_id)
    message = render_to_string("miscs/admission_guidance_programme_mail.html",{'name':name})
    send_mail(
        subject="Start to Finish School Admission Guidance",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=[attendee.email, DEFAULT_TO_PARENT_EMAIL],
        fail_silently=False,
    )



@task(name="send_sponser_mail")
def send_sponser_mail(attendee_id):
    attendee = SponsorsRegistrations.objects.get(pk=attendee_id)
    message = render_to_string("miscs/sponser_mail.html",{'name':attendee.name})
    send_mail(
        subject="Schools Engagement Programme | Ezyschooling",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=[attendee.email, DEFAULT_TO_SCHOOL_EMAIL],
        fail_silently=False,
    )


@task(name="webinar_registration_mail")
def webinar_registration_mail(attendee_id):
    attendee = WebinarRegistrations.objects.get(pk=attendee_id)
    message = render_to_string("miscs/webinar_registration_mail.html",{'name':attendee.name})
    send_mail(
        subject="Invitation for Panel Discussion",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=[attendee.email, DEFAULT_TO_PARENT_EMAIL],
        fail_silently=False,
    )

@task(name="add_admission_guidance_data")
def add_admission_guidance_data(attendee_id):
    attendee = AdmissionGuidance.objects.get(pk=attendee_id)
    gc = gspread.service_account(
        filename=os.path.join(
            settings.BASE_DIR,
            "sheets_cred.json"))
    spreadsheet = gc.open_by_key(settings.GOOGLE_SHEET_ID)
    sheet = spreadsheet.worksheet('automatic admission guidance')
    sheet.append_row([attendee.id,
                      attendee.parent_name,
                      attendee.phone,
                      attendee.email,
                      attendee.target_region,
                      attendee.budget,
                      attendee.slot_id,
                      attendee.message,
                      attendee.created_at.strftime("%d/%m/%Y")
                      ])
    logger.info("Parent Details added to Google Sheet")

@task(name="add_contact_us_data")
def add_contact_us_data(attendee_id):
    contact = ContactUs.objects.get(pk=attendee_id)
    gc = gspread.service_account(
        filename=os.path.join(
            settings.BASE_DIR,
            "sheets_cred.json"))
    spreadsheet = gc.open_by_key(settings.GOOGLE_SHEET_ID)
    sheet = spreadsheet.worksheet('contact us form')
    sheet.append_row([contact.id,
                      contact.email,
                      contact.phone_number,
                      contact.message,
                      contact.created_at.strftime("%d/%m/%Y")
                      ])
    logger.info("Contact US Details added to Google Sheet")



@task(name="inform_admin_via_mail")
def inform_admin_via_mail(attendee_id):
    attendee = WebinarRegistrations.objects.get(pk=attendee_id)
    message = render_to_string("miscs/inform.html",{'name':attendee.name,'email':attendee.email,'phone':attendee.phone,'school_name':attendee.school_name})
    send_mail(
        subject="Some One has registered for webinar",
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=message,
        recipient_list=["nikita.arora@ezyschooling.com","mayank@ezyschooling.com"],
        fail_silently=False,
    )

# @task(name="send_test_mail_aws")
# def send_test_mail_aws():
#     print("Hey working")
#     school_list = ChildSchoolCart.objects.all().order_by('-timestamp')[:4]
#     message = render_to_string("parents/atc_fff_mail.html",
#                                 {'username': "Himalaya",
#                                 'complete_form_count': 9,
#                                 'incomplete_form_count':0,
#                                 'school_list':school_list,
#                                 'intrested_parents':53,
#                                 'is_atc':True,
#                                 'is_fff':False,})
#
#     send_mail(subject="Important! Complete your child's admission form with Ezyschooling",
#     message='',
#             html_message=message,
#             from_email='Ezyschooling <info@ezyschooling.in>',
#             recipient_list=['himalaya.ezyschooling@gmail.com'],
#             connection=settings.EMAIL_CONNECTION, fail_silently=False)
#     logger.info("AWS test mail send")
