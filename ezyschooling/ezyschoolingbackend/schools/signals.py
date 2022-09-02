from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import SchoolProfile, SchoolPoint, AdmmissionOpenClasses, FeeStructure, SchoolAdmissionAlert, AgeCriteria, AdmissionSession, SchoolClassNotification, SchoolEnquiry,BoardingSchoolExtend, SchoolClaimRequests
from .tasks import update_school_index_task, send_school_admission_alert_mails, send_parent_class_notification, send_enquiry_mail_to_school, send_parent_enquiry_class_status, get_nearby_location, schools_whatsapp_enquiry_trigger, send_school_claim_admin_alert
from miscs.models import EzyschoolingEmployees
from .utils import default_boarding_school_faq_value
from notification.models import WhatsappSubscribers
# from miscs.tasks import send_test_mail_aws

@receiver(post_save, sender=SchoolProfile)
def create_school_point_object(sender, instance, **kwargs):
    if kwargs["created"]:
        SchoolPoint.objects.create(school=instance)

@receiver([post_save, post_delete], sender=FeeStructure)
@receiver([post_save, post_delete], sender=AdmmissionOpenClasses)
@receiver([post_save, post_delete], sender=AgeCriteria)
def update_school_index(sender, instance, **kwargs):
    #update_school_index_task.delay()
        pass

# @receiver(post_save, sender=AdmmissionOpenClasses)
def send_subscribers_mail(sender, instance, **kwargs):
    if instance.admission_open in ["OPEN","ABOUT TO CLOSE"]:
        send_school_admission_alert_mails.delay(instance.pk)


# @receiver(post_save, sender=SchoolProfile)
def Admission_open_object(sender, instance, **kwargs):
    currentSession, nextSession = AdmissionSession.objects.all().order_by('id')[:2][0], AdmissionSession.objects.all().order_by('id')[:2][1]
    for i in instance.class_relation.all():
        if AdmmissionOpenClasses.objects.get_or_create(class_relation=i,session=currentSession.name,school=instance):
            AdmmissionOpenClasses.objects.get_or_create(class_relation=i,session=currentSession.name,school=instance)
        elif AdmmissionOpenClasses.objects.get_or_create(class_relation=i,session=nextSession.name,school=instance):
            AdmmissionOpenClasses.objects.get_or_create(class_relation=i,session=nextSession.name,school=instance)
        elif AdmmissionOpenClasses.objects.get_or_create(class_relation=i,school=instance):
            AdmmissionOpenClasses.objects.get_or_create(class_relation=i,school=instance)
        print("event")

@receiver(post_delete,sender=SchoolProfile)
def Admission_delete_object(sender, instance, **kwargs):
    pass

# Notify Me-

@receiver(post_save, sender=AdmmissionOpenClasses)
def send_notification_mail(sender, instance, **kwargs):
    if instance.admission_open== "OPEN":
        school_obj=instance.school
        class_obj=instance.class_relation
        session=instance.session
        notify_objects=SchoolClassNotification.objects.filter(school=school_obj,notify_class=class_obj,session=session).select_related('user')
        for noty in notify_objects:
            if not noty.notification_sent:
                email = None
                if noty.email:
                    email = noty.email
                elif noty.user and noty.user.email:
                    email = noty.user.email
                if email:
                    noty.notification_sent=True
                    noty.save()
                    send_parent_class_notification.delay(email, school_obj.id, class_obj.id, session)
            else:
                pass


# send enquiry sms to parent
# def enquiry_sms_to_parent(phone, message):
#     url = "http://manage.ibulksms.in/api/sendhttp.php"
#     data = {
#         "authkey": settings.SMS_API_KEY,
#         "mobiles": f"91{phone}",
#         "message": message,
#         "country": "91",
#         "route": "4",
#         "sender": "EZYSHL",
#         "DLT_TE_ID":""
#     }
#     requests.get(url, params=data)

# send enquiry mails to parent
@receiver(post_save, sender=SchoolEnquiry)
def send_enquiry_mail_to_parent(sender, instance, **kwargs):
    obj = AdmmissionOpenClasses.objects.filter(school=instance.school, class_relation=instance.class_relation,admission_open="OPEN").first()
    if obj:
        school_obj = instance.school
        class_obj = instance.class_relation
        parent = {"name": instance.parent_name, "phone": instance.phone_no}
        if instance.email:
            parent["email"] = instance.email
            send_parent_enquiry_class_status.delay(parent, school_obj.id, class_obj.id)
        elif instance.user and instance.user.email:
            parent["email"] = instance.user.email
            send_parent_enquiry_class_status.delay(parent, school_obj.id, class_obj.id)
        else:
            pass


# send enquiry mails to school
@receiver(post_save, sender=SchoolEnquiry)
def send_enquiry_mail(sender, instance, created,*args, **kwargs):
    send_enquiry_mail_to_school.delay(enquiry_id=instance.id)
    if SchoolProfile.objects.filter(id=instance.school.id).exists():
        school_obj = SchoolProfile.objects.get(id=instance.school.id)
        if school_obj and school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
            subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
            parent = {"phone_no": instance.phone_no, "name": instance.parent_name, "school_phone_number_cannot_viewed": instance.school.phone_number_cannot_viewed}
            schools_whatsapp_enquiry_trigger.delay(subscriber_obj.phone_number, parent)

#Get all nearby values for boarding schools
@receiver(post_save, sender=BoardingSchoolExtend)
def provide_default_values(sender,instance,created,*args, **kwargs):
    if created:
        instance.faq_related_data = default_boarding_school_faq_value()
        instance.save()
        nearby_station = get_nearby_location(type="train_station",keyword="railway station",lat=instance.extended_school.latitude,long=instance.extended_school.longitude)
        nearby_airport = get_nearby_location(type="airport",keyword="airport",lat=instance.extended_school.latitude,long=instance.extended_school.longitude)
        nearby_hospital = get_nearby_location(type="hospital",keyword="hospital",lat=instance.extended_school.latitude,long=instance.extended_school.longitude)
        instance.faq_related_data['station_name'] = nearby_station['name']
        instance.faq_related_data['station_distance'] = nearby_station['distance']
        instance.faq_related_data['station_cordinates']['lat'] = nearby_station['latitude']
        instance.faq_related_data['station_cordinates']['lng'] = nearby_station['longitude']
        instance.faq_related_data['station_nearby_location'] = nearby_station['nearby_locality']
        instance.faq_related_data['airport_name'] = nearby_airport['name']
        instance.faq_related_data['airport_distance'] = nearby_airport['distance']
        instance.faq_related_data['airport_cordinates']['lat'] = nearby_airport['latitude']
        instance.faq_related_data['airport_cordinates']['lng'] = nearby_airport['longitude']
        instance.faq_related_data['airport_nearby_location'] = nearby_airport['nearby_locality']
        instance.faq_related_data['hospital_name'] = nearby_hospital['name']
        instance.faq_related_data['hospital_distance'] = nearby_hospital['distance']
        instance.faq_related_data['hospital_cordinates']['lat'] = nearby_hospital['latitude']
        instance.faq_related_data['hospital_cordinates']['lng'] = nearby_hospital['longitude']
        instance.faq_related_data['hospital_nearby_location'] = nearby_hospital['nearby_locality']
        instance.save()

@receiver(post_save, sender=SchoolClaimRequests)
def send_school_claim_mail(sender,instance,created,*args, **kwargs):
    if created:
        send_school_claim_admin_alert.delay(instance.id)
