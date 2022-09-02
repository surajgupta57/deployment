from datetime import *

import requests
from celery.decorators import task
from celery.utils.log import get_task_logger
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template import Context, Template
from django.template.loader import render_to_string

from accounts.models import User
from admission_forms.models import ChildSchoolCart
from admission_forms.models import SchoolApplication, FormReceipt
from admission_forms.utils import send_2_week_feedback_form_whatsapp_msg, atomic_cart_whatsapp
from miscs.models import UnsubscribeEmail
from notification.models import WhatsappSubscribers
from parents.models import ParentProfile
from schools.models import SchoolEnquiry, SchoolClassNotification, SchoolProfile
from admission_forms.models import SchoolApplication, ApplicationStatusLog
logger = get_task_logger(__name__)
hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD


@task(name="send_status_update_email")
def send_status_update_email(
    email,
    status,
    school_name,
    child_name,
    user_name,
    school_email,
    school_phone,
    school_website,
):
    mssg = Template(status)
    message = mssg.render(
        Context(
            {
                "email": email,
                "child_name": child_name,
                "school_name": school_name,
                "user_name": user_name,
                "school_email": school_email,
                "school_phone": school_phone,
                "school_website": school_website,
            }
        )
    )
    mail = EmailMessage(
        subject="School Application Status Update",
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=["query@ezyschooling.com"],
        headers={"X-SES-CONFIGURATION-SET": "Email-Tracking"},
    )
    mail.content_subtype = "html"
    mail.send()
    logger.info("application Status update mail sent successfully!")


@task(name="send_status_update_sms")
def send_status_update_sms(
    phone,
    status,
    school_name,
    child_name,
    user_name,
    school_email,
    school_phone,
    school_website,
):
    mssg = Template(status)
    message = mssg.render(
        Context(
            {
                "child_name": child_name,
                "school_name": school_name,
                "user_name": user_name,
                "school_email": school_email,
                "school_phone": school_phone,
                "school_website": school_website,
            }
        )
    )

    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSCH",
    }
    requests.get(url, params=data)


@task(name="send_form_submit_sms")
def send_form_submit_sms(phone):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    message = """
    Hi Parent, Thank you for submitting the application with Ezyschooling, your application has been submitted, now you don't need to visit the schools for the submission.
    """
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID": "1207163965751159015",
    }
    requests.get(url, params=data)

# form submission mail to parent
@task(name="send_form_submit_mail")
def send_form_submit_mail(application_id):
    school_app = SchoolApplication.objects.get(id=application_id)
    email = school_app.user.email
    form_receipt = FormReceipt.objects.get(school_applied=school_app)
    school_name = school_app.school.name
    class_name = school_app.apply_for.name
    child_name = school_app.child.name
    logo_url = school_app.school.logo.url
    c_fee = school_app.school.convenience_fee or 0
    discount_applied = school_app.coupon_discount or 0
    session = school_app.registration_data.session
    app_fee = form_receipt.form_fee or 0
    app_link = (
        "https://api.main.ezyschooling.com/api/v1/admission-forms/form/"
        + str(school_app.id)
        + "/pdf/"
    )
    receipt_link = (
        "https://api.main.ezyschooling.com/api/v1/admission-forms/receipt/"
        + str(school_app.id)
        + "/pdf/"
    )
    total = app_fee + c_fee - discount_applied
    profile_link = "https://ezyschooling.com/school/profile/" + school_app.school.slug
    message = render_to_string(
        "admission_forms/school_application_success.html",
        {
            "school_name": school_name,
            "class_name": class_name,
            "child_name": child_name,
            "logo_url": logo_url,
            "profile_link": profile_link,
            "c_fee": c_fee,
            "d_applied":discount_applied,
            "session": session,
            "total": total,
            "app_fee": app_fee,
            "app_link": app_link,
            "receipt_link": receipt_link,
        },
    )

    send_mail(
        subject="Your application has been submitted successfully! 👍",
        message="",
        html_message=message,
        from_email="Ezyschooling <info@ezyschooling.in>",
        recipient_list=[email, settings.DEFAULT_TO_PARENT_EMAIL],
        connection=settings.EMAIL_CONNECTION,
        fail_silently=False,
    )
    # to school
    # email_school = school_app.school.user.email
    #
    # send_mail(subject="One new application received! 👍",
    #             message='Hi',
    #             html_message='',
    #             from_email='Ezyschooling <info@ezyschooling.in>',
    #             recipient_list=[email_school, settings.DEFAULT_TO_SCHOOL_EMAIL],
    #             connection=settings.EMAIL_CONNECTION, fail_silently=False)


# form received mail to School
@task(name="send_form_submit_mailto_school")
def send_form_submit_mailto_school(application_id):
    school_app = SchoolApplication.objects.get(id=application_id)
    email = school_app.school.sending_email_ids.split(',') if school_app.school.sending_email_ids else [school_app.school.user.email]
    parent_name=""
    if school_app.user.name:
        parent_name = school_app.user.name
    else:
        parent_name = "NA"
    class_name = str(school_app.registration_data.child_class_applying_for.name)
    child_name = str(school_app.registration_data.child_name)
    session = str(school_app.registration_data.session)
    message = render_to_string(
        "admission_forms/application_submit_in_school.html",
        {
            "child_name": child_name,
            "class": class_name,
            "session": session,
            "parent_name":parent_name
        },
    )
    send_mail(subject="One new application received! 👍",
            #   message=f'New application form has been received for {session} session.\nChild name is {child_name} applied for class {class_name} and parent details are as follows:\nParent name: {parent_name},.\nIf any query, feel free to contact us.\n\nThanks & Regards\nTeam Ezyschooling\nwebsite: www.ezyschooling.com',
              message="",
              html_message=message,
              from_email='Ezyschooling <info@ezyschooling.in>',
              recipient_list=[settings.DEFAULT_TO_SCHOOL_EMAIL]+email,
              connection=settings.EMAIL_CONNECTION, fail_silently=False)


def emailExists(parent):
    if parent != None and parent.email != None and parent.email != "":
        return parent
    else:
        return None


@task(name="send_selected_mail_and_sms")
def send_selected_mail_and_sms(app_id):
    school_app = SchoolApplication.objects.get(id=app_id)
    email = school_app.user.email
    child_name = school_app.child.name
    school_name = school_app.school.name
    school_profile_link = (
        "https://ezyschooling.com/school/profile/" + school_app.school.slug
    )
    app_status_link = "https://ezyschooling.com/profile/tracker/" + str(app_id)
    applied_class = school_app.registration_data.child_class_applying_for.name
    session = school_app.registration_data.session
    message = render_to_string(
        "admission_forms/selected.html",
        {
            "child_name": child_name,
            "school_name": school_name,
            "applied_class": applied_class,
            "session": session,
            "school_profile_link": school_profile_link,
            "app_status_link": app_status_link,
        },
    )
    # Send Mail
    send_mail(
        subject="Congratulations! Your child has been selected into your dream school. 🤩",
        message="",
        html_message=message,
        from_email="Ezyschooling <info@ezyschooling.in>",
        recipient_list=[email, settings.DEFAULT_TO_PARENT_EMAIL],
        connection=settings.EMAIL_CONNECTION,
        fail_silently=False,
    )
    # Send SMS
    form = school_app.form
    parent = (
        emailExists(form.father)
        or emailExists(form.mother)
        or emailExists(form.guardian)
    )
    if parent != None and parent.phone:
        phone = parent.phone
        if len(school_name) > 29:
            school_name_sms = school_name[:26] + "..."
        else:
            school_name_sms = school_name
        url = "http://manage.ibulksms.in/api/sendhttp.php"
        message_text = f"""
        Dear Parent, Your application has been accepted to {school_name_sms}. Congratulations from Ezyschooling family! More:https://bit.ly/EzyExp
        """
        data = {
            "authkey": settings.SMS_API_KEY,
            "mobiles": f"91{phone}",
            "message": message_text,
            "country": "91",
            "route": "4",
            "sender": "EZYSHL",
            "DLT_TE_ID": "1207164369559111820",
        }
        requests.get(url, params=data)
    logger.info("Form Selected Mail and SMS")


@task(name="send_not_selected_mail_and_sms")
def send_not_selected_mail_and_sms(app_id):
    school_app = SchoolApplication.objects.get(id=app_id)
    email = school_app.user.email
    child_name = school_app.child.name
    school_name = school_app.school.name
    school_profile_link = (
        "https://ezyschooling.com/school/profile/" + school_app.school.slug
    )
    app_status_link = "https://ezyschooling.com/profile/tracker/" + str(app_id)
    applied_class = school_app.registration_data.child_class_applying_for.name
    session = school_app.registration_data.session
    message = render_to_string(
        "admission_forms/not-selected.html",
        {
            "child_name": child_name,
            "school_name": school_name,
            "applied_class": applied_class,
            "session": session,
            "school_profile_link": school_profile_link,
            "app_status_link": app_status_link,
        },
    )
    # Send Mail
    send_mail(
        subject="School Admission results from Ezyschooling",
        message="",
        html_message=message,
        from_email="Ezyschooling <info@ezyschooling.in>",
        recipient_list=[email, settings.DEFAULT_TO_PARENT_EMAIL],
        connection=settings.EMAIL_CONNECTION,
        fail_silently=False,
    )
    # Send SMS
    form = school_app.form
    parent = (
        emailExists(form.father)
        or emailExists(form.mother)
        or emailExists(form.guardian)
    )
    if parent != None and parent.phone:
        phone = parent.phone
        if len(school_name) > 29:
            school_name_sms = school_name[:26] + "..."
        else:
            school_name_sms = school_name
        url = "http://manage.ibulksms.in/api/sendhttp.php"
        message_text = f"""
        Dear Parent, Your application has been rejected by {school_name_sms}. Ezyschooling:https://bit.ly/EzyExp
        """
        data = {
            "authkey": settings.SMS_API_KEY,
            "mobiles": f"91{phone}",
            "message": message_text,
            "country": "91",
            "route": "4",
            "sender": "EZYSHL",
            "DLT_TE_ID": "1207164369570785194",
        }
        requests.get(url, params=data)
    logger.info("Form Not Selected Mail and SMS")


@task(name="atomic_cart_mail_morning")
def atomic_cart_mail_morning(user_id):
    try:
        user_obj = User.objects.get(id=user_id)
        email = user_obj.email
        if not UnsubscribeEmail.objects.filter(email=email).exists():
            if user_obj.current_parent:
                parent = ParentProfile.objects.get(id=user_obj.current_parent)
                user_name = parent.name if parent else "Parent"
            else:
                user_name = "Parent"
            user_cart_data = ChildSchoolCart.objects.filter(user__id=user_id).order_by("-timestamp")
            latest_added_school = ChildSchoolCart.objects.filter(user__id=user_id).order_by("-timestamp")
            if latest_added_school:
                latest_added_school = latest_added_school[:1][0]
                total_school_inq = SchoolEnquiry.objects.filter(school=latest_added_school.school).count()
                total_school_notification = SchoolClassNotification.objects.filter(school=latest_added_school.school).count()
                intrested_parents = int(total_school_inq + total_school_notification +  (latest_added_school.school.views * 0.4))
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
                        if cart.school.district:
                            district = cart.school.district.name
                        if cart.school.description:
                            description = cart.school.description
                    school_list.append({
                    'name':name,
                    'slug':slug,
                    'logo':logo,
                    'district_region':district_region,
                    'district':district,
                    'description':description,
                    })
                message = render_to_string("admission_forms/abandoned_cart_email.html",{
                            "username": user_name,
                            "total_cart_item": total_cart_item,
                            "user_cart_data": school_list,
                            "intrested_parents": intrested_parents,
                    },)
                send_mail(
                    subject="Apply to the schools waiting in your cart before time runs out",
                    message="",
                    html_message=message,
                    from_email="Ezyschooling <info@ezyschooling.in>",
                    recipient_list=[email, settings.DEFAULT_TO_PARENT_EMAIL],
                    connection=settings.EMAIL_CONNECTION,
                    fail_silently=False,
                )
                logger.info("Sending Abandoned Cart Email - Morning")
    except:
        pass



@task(name="atomic_cart_mail_evening")
def atomic_cart_mail_evening(user_id):
    try:
        user_obj = User.objects.get(id=user_id)
        email = user_obj.email
        if not UnsubscribeEmail.objects.filter(email=email).exists():
            if user_obj.current_parent:
                parent = ParentProfile.objects.get(id=user_obj.current_parent)
                user_name = parent.name if parent else "Parent"
            else:
                user_name = "Parent"
            user_cart_data = ChildSchoolCart.objects.filter(user__id=user_id).order_by("-timestamp")
            latest_added_school = ChildSchoolCart.objects.filter(user__id=user_id).order_by("-timestamp")
            if latest_added_school:
                latest_added_school = latest_added_school[:1][0]
                total_school_inq = SchoolEnquiry.objects.filter(school=latest_added_school.school).count()
                total_school_notification = SchoolClassNotification.objects.filter(school=latest_added_school.school).count()
                intrested_parents = int(total_school_inq+ total_school_notification+(latest_added_school.school.views * 0.4))
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
                        if cart.school.district:
                            district = cart.school.district.name
                        if cart.school.description:
                            description = cart.school.description
                    school_list.append({
                    'name':name,
                    'slug':slug,
                    'logo':logo,
                    'district_region':district_region,
                    'district':district,
                    'description':description,
                    })
                message = render_to_string("admission_forms/abandoned_cart_email.html",{
                            "username": user_name,
                            "total_cart_item": total_cart_item,
                            "user_cart_data": school_list,
                            "intrested_parents": intrested_parents,
                    },
                )
                send_mail(
                    subject="Apply to the schools waiting in your cart before time runs out",
                    message="",
                    html_message=message,
                    from_email="Ezyschooling <info@ezyschooling.in>",
                    recipient_list=[email, settings.DEFAULT_TO_PARENT_EMAIL],
                    connection=settings.EMAIL_CONNECTION,
                    fail_silently=False,
                )
                logger.info("Sending Abandoned Cart Email - Morning")
    except:
        pass


def atomic_cart_sms(phone, message):
    url = "http://manage.ibulksms.in/api/sendhttp.php"
    data = {
        "authkey": settings.SMS_API_KEY,
        "mobiles": f"91{phone}",
        "message": message,
        "country": "91",
        "route": "4",
        "sender": "EZYSHL",
        "DLT_TE_ID": "1207163894530255711",
    }
    requests.get(url, params=data)


@task(name="bulk_atomic_cart_mail_morning", queue="long-running")
def bulk_atomic_cart_mail_morning(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        currentDate = datetime.now().date()
        yesterdayDate = currentDate - relativedelta(days=1)
        yesterdayDateTime = str(yesterdayDate) + " 19:00:00"
        yesterdayDateTime = datetime.strptime(yesterdayDateTime, "%Y-%m-%d %X")
        currentDateTime = str(currentDate) + " 09:00:00"
        currentDateTime = datetime.strptime(currentDateTime, "%Y-%m-%d %X")
        cart_data = ChildSchoolCart.objects.filter(
            timestamp__date__lte=currentDateTime, timestamp__date__gte=yesterdayDateTime
        )
        user_ids_mor = []
        for item in cart_data:
            user_ids_mor.append(item.user.id)
        user_ids_mor = list(set(user_ids_mor))

        for i in user_ids_mor:
            user_ids_mor.remove(i)
            atomic_cart_mail_morning.delay(i)
            atomic_cart_whatsapp(i)
            user_obj = User.objects.filter(id=i).first()
            if user_obj.current_parent:
                parent = ParentProfile.objects.get(id=user_obj.current_parent)
                if parent.phone and len(parent.phone) == 10:
                    phone = parent.phone
                    sms_message = f"""Dear {parent.name[:30] or parent.user.name[:30]},
    Complete your dream school admission form now with Ezyschooling, limited seats are left. Hurry!
    Complete now:  https://bit.ly/31rXVH7"""
                    atomic_cart_sms(phone, sms_message)


@task(name="bulk_atomic_cart_mail_evening", queue="long-running")
def bulk_atomic_cart_mail_evening(offset=0, limit=100):
    if settings.IS_PERIODIC_TASK_ACTIVATED:
        currentDate = datetime.now().date()
        currentDateTimeStart = str(currentDate) + " 09:00:00"
        currentDateTimeEnd = str(currentDate) + " 19:00:00"
        currentDateTimeStart = datetime.strptime(currentDateTimeStart, "%Y-%m-%d %X")
        currentDateTimeEnd = datetime.strptime(currentDateTimeEnd, "%Y-%m-%d %X")
        cart_data = ChildSchoolCart.objects.filter(timestamp__date__lte=currentDateTimeEnd,timestamp__date__gte=currentDateTimeStart)
        user_ids_eve = []
        for item in cart_data:
            user_ids_eve.append(item.user.id)
        user_ids_eve = list(set(user_ids_eve))
        for i in user_ids_eve:
            user_ids_eve.remove(i)
            atomic_cart_mail_evening.delay(i)
            atomic_cart_whatsapp(i)
            user_obj = User.objects.filter(id=i).first()
            if user_obj.current_parent:
                parent = ParentProfile.objects.get(id=user_obj.current_parent)
                if parent.phone and len(parent.phone) == 10:
                    phone = parent.phone
                    sms_message = f"""Dear {parent.name[:30] or parent.user.name[:30]},
    Complete your dream school admission form now with Ezyschooling, limited seats are left. Hurry!
    Complete now:  https://bit.ly/31rXVH7"""
                    atomic_cart_sms(phone, sms_message)


@task(name="send_2_week_feedback_form")
def send_2_week_feedback_form():  # add a logic to send whatsapp msg exactly after 2 week
    start_date = str((datetime.today() - timedelta(days=14))).split(" ")[0]
    fromdate = datetime.strptime(start_date + " 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    todate = datetime.strptime(start_date + " 11:59:59.000000", "%Y-%m-%d %H:%M:%S.%f")
    if ApplicationStatusLog.objects.filter(application__timestamp__range=(fromdate, todate)).exclude(status__name='Not Selected').exists():
        applicationStatusLog = ApplicationStatusLog.objects.filter(application__timestamp__range=(fromdate, todate)).exclude(status__name='Not Selected')
        if applicationStatusLog:
            for app in applicationStatusLog:
                application = app.application
                form_details = application.form
                if WhatsappSubscribers.objects.filter(user=form_details.user, is_Subscriber=True).exists():
                    whatsapp_user = WhatsappSubscribers.objects.get(user=form_details.user, is_Subscriber=True)
                    send_2_week_feedback_form_whatsapp_msg(whatsapp_user.phone_number)
                    logger.info(f"Whatsapp Feedback form/Message sent to {whatsapp_user.phone_number}")
                else:
                    logger.info(f"No Detail found")
    else:
        pass

# application_form_submitted_whatsapp_msg_to school:
@task(name="application_form_submitted_whatsapp_msg_to_school")
def application_form_submitted_whatsapp_msg_to_school(school_phone_no, parent_name, parent_phone):
    msg_template = f"*You have received one new application* 📝\n\nName: {parent_name}\nPhone: {parent_phone}\n\nEnsure to take necessary action now!"
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
