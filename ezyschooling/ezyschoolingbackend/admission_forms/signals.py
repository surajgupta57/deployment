import requests
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from parents.models import ParentProfile
from notification.models import WhatsappSubscribers
from .models import CommonRegistrationForm, SchoolApplication, ApplicationStatusLog
from .utils import calculate_points, send_form_submit_whatsapp_msg, send_not_selected_whatsapp_msg, \
    send_selected_whatsapp_msg
from .tasks import send_status_update_email, send_status_update_sms, send_form_submit_sms, send_form_submit_mail, send_selected_mail_and_sms, send_not_selected_mail_and_sms,send_form_submit_mailto_school,application_form_submitted_whatsapp_msg_to_school


@receiver(pre_save, sender=CommonRegistrationForm)
def update_first_girl_child(sender, instance, **kwargs):
    if not instance.first_girl_child:
        if instance.first_child and instance.child.gender == 'female':
            instance.first_girl_child = True
    elif instance.first_girl_child:
        if not instance.first_child and instance.child.gender == "female":
            instance.first_girl_child = False
        if instance.child.gender == "male":
            instance.first_girl_child = False


@receiver(post_save, sender=SchoolApplication)
def evalute_points(sender, instance, created, **kwargs):
    if created:
        if instance.school.point_system:
            calculate_points(instance)


@receiver(pre_save, sender=CommonRegistrationForm)
def update_minority_points(sender, instance, **kwargs):
    if instance.id is None:
        pass
    else:
        previous = CommonRegistrationForm.objects.only(
            "category").get(id=instance.id)
        if (previous.category != instance.category) and (instance.category is not "General"):
            instance.child.minority_points = True
            instance.child.save()
        if (instance.category == "General") and (previous.category != instance.category):
            instance.child.minority_points = False
            instance.child.save()

def emailExists(parent):
    if parent != None and parent.email!=None and parent.email!='':
        return parent
    else:
        return None

hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD

@receiver(post_save, sender= ApplicationStatusLog)
def send_status_update_to_parent(sender, instance, *args, **kwargs):
    applicationStatusLog = instance
    application = applicationStatusLog.application
    school = application.school
    form = application.form
    child= application.child.name
    parent_data = emailExists(form.father) or emailExists(form.mother) or emailExists(form.guardian) or emailExists(application.user)
    if parent_data:
        if applicationStatusLog.status.name == 'Form Submitted':
            try:
                send_form_submit_mail(application_id=application.id)
                send_form_submit_mailto_school(application_id=application.id)
            except Exception as e:
                pass
            user_obj = ParentProfile.objects.filter(user__id=form.user.id).first()
            if user_obj and WhatsappSubscribers.objects.filter(user=user_obj.user,is_Subscriber=True).exists():
                user_obj_number = WhatsappSubscribers.objects.get(user=user_obj.user)
                send_form_submit_whatsapp_msg(user_obj_number.phone_number, user_obj.slug)
            if school.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school.user,is_Subscriber=True).exists():
                subscriber_obj = WhatsappSubscribers.objects.get(user=school.user,is_Subscriber=True)
                application_form_submitted_whatsapp_msg_to_school.delay(subscriber_obj.phone_number, user_obj.name, user_obj.phone)
        elif applicationStatusLog.status.name == 'Selected':
            send_selected_mail_and_sms.delay(app_id=application.id)
            user_obj = ParentProfile.objects.filter(user__id=form.user.id).first()
            if user_obj and WhatsappSubscribers.objects.filter(user=user_obj.user,is_Subscriber=True).exists():
                user_obj_number = WhatsappSubscribers.objects.get(user=user_obj.user)
                send_selected_whatsapp_msg(user_obj_number.phone_number,school.name)
        elif applicationStatusLog.status.name == 'Not Selected':
            send_not_selected_mail_and_sms.delay(app_id=application.id)
            user_obj = ParentProfile.objects.filter(user__id=form.user.id).first()
            if user_obj and WhatsappSubscribers.objects.filter(user=user_obj.user,is_Subscriber=True).exists():
                user_obj_number = WhatsappSubscribers.objects.get(user=user_obj.user)
                send_not_selected_whatsapp_msg(user_obj_number.phone_number,school.name)

        else:
            send_status_update_email.delay(
                email = parent_data.email,
                status = applicationStatusLog.status.mail_content,
                school_name = school.name,
                child_name = child,
                user_name = application.user.name,
                school_email = school.email,
                school_phone = school.phone_no,
                school_website = school.website
            )
        #send sms
        # send_status_update_sms.delay(
        #     phone = parent.phone,
        #     status = applicationStatusLog.status.sms_content,
        #     school_name = school.name,
        #     child_name = child,
        #     user_name = application.user.name,
        #     school_email = school.email,
        #     school_phone = school.phone_no,
        #     school_website = school.website
        # )

# @receiver(post_save, sender= SchoolApplication)
# def send_form_submit_sms_to_parent(sender, instance, *args, **kwargs):
#     application = instance
#     form = instance.form
#     parent = emailExists(form.father) or emailExists(form.mother) or emailExists(form.guardian)
#     if parent != None:
#         #send sms
#         send_form_submit_sms.delay(phone = parent.phone)

# @receiver(post_save, sender= SchoolApplication)
# def send_form_submit_mail_to_parent(sender, instance, *args, **kwargs):
#     send_form_submit_mail.delay(application_id=instance.id)


# @receiver(post_save, sender= SchoolApplication)
# def send_form_submit_mail_to_school(sender, instance, *args, **kwargs):
#     send_form_submit_mailto_school.delay(application_id=instance.id)
