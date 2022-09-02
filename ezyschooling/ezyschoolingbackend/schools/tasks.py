from celery import shared_task
from celery.decorators import task
from celery.utils.log import get_task_logger
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.core.mail import send_mail
from django.core.management import call_command
from django.template.loader import render_to_string
from django.utils import timezone
import pandas as pd
from schools.models import (
    SchoolProfile,
    SchoolClasses,
    SchoolAdmissionAlert,
    AdmmissionOpenClasses,
    AppliedSchoolSelectedCsv,
    SelectedStudentFromCsv,
    SchoolEnquiry,SchoolClassNotification,
    SchoolClaimRequests
)
from rest_framework import generics, permissions, status
from admission_forms.models import SchoolApplication, ApplicationStatusLog
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import json
app = Nominatim(user_agent="Ezyschool",timeout=3)
logger = get_task_logger(__name__)


hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD

@task(name="update_school_index_task", queue="long-running")
def update_school_index_task():
    try:
        call_command(
            "search_index",
            "--rebuild",
            models=["schools.SchoolProfile"],
            settings=["backend.settings.production"],
            f=True,
        )
    except Exception as e:
        logger.info(f"an Exception {e} has occured")
        return False
    logger.info("Successfully indexed school profiles")
    return True


@task(name="send_school_code_request_mail")
def send_school_code_request_mail(school_id):
    school = SchoolProfile.objects.get(pk=school_id)
    subject = f"[Ezyschooling] {school.name} sent a Code Request"
    message = f"""
    Dear Admin,
    {school.name} has sent a request for verification code for their account {school.user.email}
    Regards
    EzySchooling Team
    """

    logger.info("Code Request email sent")
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [
            "mayank@ezyschooling.com",
        ],
        fail_silently=False,
    )


@task(name="send_school_signup_admin_alert")
def send_school_signup_admin_alert(school_id, created_by=None):
    school = SchoolProfile.objects.get(pk=school_id)
    contact = school.contacts.first()
    if created_by == "db_team":
        subject = f"New Onboarding Alert | DB Team"

    else:
        subject = f"New Onboarding Alert"
    # subject = f"New Onboarding Alert"
    message = f"""
    Dear Admin,
    {school.name.title()}, {school.school_city.name} has onboarded on ezyschooling website.

    Their information is provided below:
    School Name : {school.name.title()}
    Email : {school.email}
    Region : {school.school_city.name}
    Address : {school.short_address}, {school.street_address}, {school.school_city.name}, {school.zipcode}, {school.school_state.name}
    Contact: {contact.name}, {contact.phone}

    Regards
    Ezyschooling Team
    """
    logger.info("New School Signup Admin Alert/Mail")
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        ["mayank@ezyschooling.com", "krishna.pandey@ezyschooling.com"],
    )


# @task(name="atomic_sync_school_views", queue="long-running")
def atomic_sync_school_views(school_id):
    school = SchoolProfile.objects.get(pk=school_id)
    school.views = school.visits.count()
    school.save()


# @task(name="bulk_sync_school_views", queue="long-running")
def bulk_sync_school_views(offset=0, limit=100):
    schools = SchoolProfile.objects.filter(is_verified=True, is_active=True)
    for i in schools[offset : offset + limit]:
        atomic_sync_school_views.delay(i.id)
    if schools[offset + limit :].count() > 0:
        bulk_sync_school_views.apply_async(args=(offset + limit, limit), countdown=10)
    else:
        # update_school_index_task.delay()
        pass


@task(name="atomic_school_updates_mail", queue="long-running")
def atomic_school_updates_mail(school_id):
    school = SchoolProfile.objects.get(pk=school_id)
    today = timezone.now().date()
    three_days_ago = today - relativedelta(days=1)
    # enquiries = school.enquiries.filter(
    #     timestamp__date__lt=today, timestamp__date__gte=three_days_ago).count()
    # visits = school.visits.filter(
    #     timestamp__date__lt=today, timestamp__date__gte=three_days_ago).count()
    forms = school.forms.filter(
        timestamp__date__lt=today, timestamp__date__gte=three_days_ago
    ).count()
    context = {
        # "enquiries_count": enquiries,
        # "views_count": visits,
        "forms_count": forms
    }

    if enquiries > 0 or visits > 0 or forms > 0:
        message = render_to_string("schools/weekly_updates_mail.html", context)
        school_mails = school.sending_email_ids.split(',') if ',' in school.sending_email_ids else [school.user.email]
        send_mail(
            subject="Ezyschooling Daily Updates",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL]+school_mails,
            fail_silently=False,
            message="",
            html_message=message,
        )


@task(name="bulk_school_updates_mail", queue="long-running")
def bulk_school_updates_mail(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        schools = SchoolProfile.objects.filter(
            admmissionopenclasses__isnull=False,
            is_verified=True,
            is_active=True,
            collab=True,
        ).distinct("id")
        for i in schools[offset : offset + limit]:
            atomic_school_updates_mail.delay(i.id)
        if schools[offset + limit :].count() > 0:
            bulk_school_updates_mail.apply_async(args=(offset + limit, limit), countdown=10)


@task(name="send_school_admission_alert_mails")
def send_school_admission_alert_mails(pk):
    admission_open_classes = AdmmissionOpenClasses.objects.get(pk=pk)
    school = admission_open_classes.school
    class_relation = admission_open_classes.class_relation
    subscriber_list = SchoolAdmissionAlert.objects.filter(
        school_relation=school, class_relation=class_relation
    ).values_list("user__email", flat=True)
    subscriber_list = list(subscriber_list)

    subject = f"Admission status changed for {school.name.title()}"
    message = f"""
    Dear Parent,
    {school.name.title()} has changed its admission status.
    STATUS : {admission_open_classes.admission_open} for {class_relation}

    Regards
    Ezyschooling Team
    """
    logger.info("Admission for school opened alert")
    send_mail(
        subject=subject,
        from_email=settings.DEFAULT_FROM_EMAIL,
        message=message,
        recipient_list=subscriber_list,
        fail_silently=False,
    )


def preprocess_text(string):
    if type(string) == str:
        if "_" in string:
            value = string.split("_")
            if len(value) == 3:
                value1 = value[0].lower() + "_" + value[1] + "_" + value[2]
                return value1
            else:
                return string
        else:
            return string
    else:
        return string


@task(name="add_selected_child_data_from_csv")
def add_selected_child_data_from_csv(school_id, doc_id):

    school = generics.get_object_or_404(SchoolProfile, id=school_id)
    doc = generics.get_object_or_404(
        AppliedSchoolSelectedCsv, id=doc_id, school_relation=school
    )
    csv = pd.read_csv(doc.csv_file)
    for index, row in csv.iterrows():
        try:
            SelectedStudentFromCsv.objects.get(
                school_relation=school,
                receipt_id=row["RECEIPT ID"],
                child_name=row["APPLICANT'S NAME"],
            )
        except SelectedStudentFromCsv.DoesNotExist:
            SelectedStudentFromCsv.objects.get_or_create(
                document=doc,
                school_relation=school,
                receipt_id=row["RECEIPT ID"],
                child_name=row["APPLICANT'S NAME"],
            )
    processed_list = [preprocess_text(i) for i in csv["RECEIPT ID"]]
    Applications = SchoolApplication.objects.filter(uid__in=processed_list)
    if Applications:
        for i in Applications:
            ApplicationStatusLog.objects.get_or_create(status_id=4, application=i)
    return True


# Notify Me
@task(name="send_parent_class_notification")
def send_parent_class_notification(parent_mail, school_id, class_id, session):
    if parent_mail:
        school = SchoolProfile.objects.get(id=school_id)
        notify_class = SchoolClasses.objects.get(id=class_id)
        session_year = session
        link = "https://ezyschooling.com/school/profile/" + school.slug
        subject = f"Ezyschooling {school.name} has opened their Admissions"
        html_message = render_to_string(
            "schools/school_notification_mail.html",
            {
                "school_name": school.name,
                "session": session_year,
                "class": notify_class.name,
                "apply_now": link,
            },
        )
        plain_message = ""
        from_email = settings.DEFAULT_FROM_EMAIL
        to = parent_mail
        mail.send_mail(
            subject, plain_message, from_email, [to], html_message=html_message
        )


# Enquiry mail to school
@task(name="send_enquiry_mail_to_school")
def send_enquiry_mail_to_school(enquiry_id):
    enq_data = SchoolEnquiry.objects.get(id=enquiry_id)
    if enq_data.school.id == 286:
        pass
    else:
        if enq_data.school.collab:
            email = enq_data.school.sending_email_ids.split(',') if enq_data.school.sending_email_ids else [enq_data.school.user.email]
            name = enq_data.parent_name or enq_data.user.name
            user_email = enq_data.email
            phone = enq_data.phone_no
            query = enq_data.query
            message = render_to_string("schools/enquiry_collaborated.html",{"name": name,"query": query,"phone": phone,"user_email": user_email,"url": "https://ezyschooling.com/login/?utm_source=mail&utm_medium=login&utm_campaign=enquiry+update",},)
            # send_mail(subject="[Ezyschooling] A parent has reached out to your school",
            #           message=f'Hi,\n{name} was exploring your school and has raised a query regarding.\n Query raised: "{query}".\nBelow are the contact details so that you can resolve the query soon and help the parent in the admission process further.:\nNumber: {phone}\nEmail-ID: {user_email}.\nWe hope that you are able to reach out to the parent soon so that take a decision soon.\nIf you have any query, feel free to contact us.\n\nThanks & Regards\nTeam Ezyschooling\nwww.ezyschooling.com',
            #           html_message='',
            #           from_email='Ezyschooling <info@ezyschooling.in>',
            #           recipient_list=[email, settings.DEFAULT_TO_SCHOOL_EMAIL],
            #           connection=settings.EMAIL_CONNECTION, fail_silently=False)
            send_mail(subject="[Ezyschooling] A parent has reached out to your school",
                message='',
                html_message=message,
                from_email='Ezyschooling <info@ezyschooling.in>',
                recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL]+email,
                connection=settings.EMAIL_CONNECTION, fail_silently=False)
        else:
            if enq_data.school.email:
                email = enq_data.school.sending_email_ids.split(',') if enq_data.school.sending_email_ids else [enq_data.school.user.email]
                name = enq_data.parent_name or enq_data.user.name
                user_email = enq_data.email
                phone = enq_data.phone_no
                query = enq_data.query
                message = render_to_string("schools/enquiry_non-collaborated.html",{"name": name,"query": query,"phone": phone,"user_email": user_email,"url": "https://ezyschooling.com/login/",},)
                # send_mail(subject="[Ezyschooling] A parent has reached out to your school",
                #           message=f'Hi,\n{name} was exploring your school and has raised a query regarding.\n Query raised: "{query}".\nBelow are the contact details so that you can resolve the query soon and help the parent in the admission process further.:\nEmail-ID: {user_email}.\nWe hope that you are able to reach out to the parent soon so that take a decision soon.\nIf you have any query, feel free to contact us.\n\nThanks & Regards\nTeam Ezyschooling\nwww.ezyschooling.com',
                #           html_message='',
                #           from_email='Ezyschooling <info@ezyschooling.in>',
                #           recipient_list=[email, settings.DEFAULT_TO_SCHOOL_EMAIL],
                #           connection=settings.EMAIL_CONNECTION, fail_silently=False)
                send_mail(subject="[Ezyschooling] A parent has reached out to your school",
                    message='',
                    html_message=message,
                    from_email='Ezyschooling <info@ezyschooling.in>',
                    recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL]+email,
                    connection=settings.EMAIL_CONNECTION, fail_silently=False)


# Class open enquiry mail
@task(name="send_parent_enquiry_class_status")
def send_parent_enquiry_class_status(enq_parent_data, school_id, class_id):
    if enq_parent_data["email"] is not None:
        school = SchoolProfile.objects.get(id=school_id)
        enq_class = SchoolClasses.objects.get(id=class_id)
        total_school_inq = SchoolEnquiry.objects.filter(school=school).count()
        total_school_notification = SchoolClassNotification.objects.filter(school=school).count()
        intrested_parents = int(total_school_inq + total_school_notification + (school.views * 0.4))
        link = "https://ezyschooling.com/login?utm_source=mail&utm_medium=apply&utm_campaign=enquiry+reminder"
        subject = "Apply before admissions close in your dream school!"
        # html_message = render_to_string('schools/class_enquiry_status_mail.html',
        #                                 {'school_name': school.name, 'session': session_year,
        #                                  'class': enq_class.name, 'apply_now': link}
        if intrested_parents > 50:
            message = render_to_string("schools/parent_enquiry_mail_adm_open.html",
                                            {'school_name': school.name, 'interest_parents': intrested_parents,'class': enq_class.name, 'apply_now': link})
        else:
            message = render_to_string("schools/Parent_enquiry_mail.html",
                                            {'school_name': school.name,'interest_parents': "Many",'class': enq_class.name, 'apply_now': link})
        to = enq_parent_data["email"]
        send_mail(subject=subject,
                  message='',
                  html_message=message,
                  from_email='Ezyschooling <info@ezyschooling.in>',
                  recipient_list=[settings.DEFAULT_TO_PARENT_EMAIL] + [to],
                  connection=settings.EMAIL_CONNECTION, fail_silently=False)
        # if intrested_parents > 50:
        #     message = f"""
        #         Dear Parent,
        #         We noticed that you enquired for {enq_class.name} admissions in {school.name}.
        #         We wanted to notify you that admissions are open in this school but seats are limited.\n
        #         {intrested_parents} parents have already shown interest and that suggests that you should be taking a very quick action.\n
        #         Don't worry! Our counselors will be contacting you soon to answer all your doubts and in the meantime you can start with the admission process.
        #         \n
        #         Sign up and start your application form before it's too late!\n
        #         {link}\n\n
        #
        #
        #         Regards
        #         Ezyschooling Team
        #     """
        # else:
        #     message = f"""
        #         Dear Parent,
        #         We noticed that you enquired for {enq_class.name} admissions in {school.name}.
        #         We wanted to notify you that admissions are open in this school but seats are limited.\n
        #         Many parents have already shown interest and that suggests that you should be taking a very quick action.\n
        #         Don't worry! Our counselors will be contacting you soon to answer all your doubts and in the meantime you can start with the admission process.
        #         \n
        #         Sign up and start your application form before it's too late!\n
        #         {link}\n\n
        #
        #
        #         Regards
        #         Ezyschooling Team
        #     """
        # from_email = settings.DEFAULT_FROM_EMAIL
        # to = enq_parent_data["email"]
        # send_mail(subject=subject,
        #           message=message,
        #           from_email='Ezyschooling <info@ezyschooling.in>',
        #           recipient_list=[settings.DEFAULT_TO_PARENT_EMAIL] + [to],
        #           connection=settings.EMAIL_CONNECTION, fail_silently=False)
    else:
        pass

def get_nearby_location(type,keyword,lat,long):
    URL = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{long}&rankby=distance&type={type}&keyword={keyword}&key={settings.GOOGLE_MAP_API_KEY}"
    response = requests.request("GET", URL, headers={}, data={})
    name = response.json()["results"][0]['name']
    nearby = response.json()["results"][0]['vicinity']
    latitude = response.json()["results"][0]['geometry']['location']['lat']
    longitude = response.json()["results"][0]['geometry']['location']['lng']
    school = (lat,long)
    location = (latitude, longitude)
    distance = f"{int(geodesic(school, location).km)} kms" if not int(geodesic(school, location).km) == 0 else f"{int(geodesic(school, location).m)} meters"
    return {"name":name,"nearby_locality":nearby,"latitude":latitude,"longitude":longitude,"distance":distance}


# School enquiry WhatsApp trigger!
@task(name="schools_whatsapp_enquiry_trigger")
def schools_whatsapp_enquiry_trigger(school_phone_no, parent):
    if not parent["school_phone_number_cannot_viewed"]:
        phone_number = parent["phone_no"]
    else:
        n = parent["phone_no"].replace(" ", "").split(",") if parent["phone_no"] else []
        list2 = []
        if len(n) > 0:
            for a in n:
                list1 = []
                list1[:0] = a
                list1.reverse()
                for index, val in enumerate(list1):
                    if index == 4:
                        break
                    else:
                        list1[index] = 'x'
                list1.reverse()
                hidden_number = ''.join(map(str, list1))
                list2.append(hidden_number)
            hidden_number = ', '.join(map(str, list2))
        else:
            hidden_number = None
        phone_number = hidden_number
    msg_template = f"*Someone has enquired for your school* ⁉️\n\nName: {parent['name']}\nPhone: {phone_number}\n\nMake sure to reach out to them as soon as you can!"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(school_phone_no) == 10:
        school_phone_no = "91" + school_phone_no
    request_body = {
        'method': 'SENDMESSAGE',
        'format': 'json',
        'send_to': school_phone_no,
        'v': '1.1',
        'isTemplate': True,
        'msg_type': 'TEXT',
        'msg': msg_template,
        'userid': str(hsm_user_id),
        'password': str(hsm_user_password)}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    requests.post(endpoint, headers=headers, data=request_body)

@task(name="send_school_claim_admin_alert")
def send_school_claim_admin_alert(claim_id):
    claim_object = SchoolClaimRequests.objects.get(id=claim_id)
    subject = f"New Claim Alert - {claim_object.school.name}, {claim_object.school.school_city.name}"
    message = f"""
    Dear Admin,
    {claim_object.name} has claimed for {claim_object.school.name.title()}, {claim_object.school.school_city.name} for school at EzySchooling.

    Their information is provided below:
    School Name : {claim_object.school.name.title()}
    School Profile : 'https://ezyschooling.com/school/profile/'{claim_object.school.slug}
    Region : {claim_object.school.school_city.name}
    Address : {claim_object.school.short_address}, {claim_object.school.street_address}, {claim_object.school.school_city.name}, {claim_object.school.zipcode}, {claim_object.school.school_state.name}
    Claimer's Phone Number : {claim_object.phone_number}
    Claimer's Email : {claim_object.email}
    Claimer's Designation : {claim_object.designation.title()}

    Regards
    Ezyschooling Team
    """
    logger.info("School Claim Admin Alert/Mail")
    return send_mail(subject=subject,
              message=message,
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=["mayank@ezyschooling.com", "krishna.pandey@ezyschooling.com"],
              connection=settings.EMAIL_CONNECTION, fail_silently=False)
