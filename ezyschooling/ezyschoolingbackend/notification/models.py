from django.db import models
from accounts.models import User
from schools.models import SchoolEnquiry
from .utils import WebPushKey
# Create your models here.


class DeviceRegistrationToken(models.Model):
    pc_registration_id = models.TextField()
    mobile_registration_id = models.TextField()
    city = models.ForeignKey(
        "schools.City", on_delete=models.SET_NULL, null=True, blank=True)
    is_boarding_school = models.BooleanField(null=True, blank=True)
    is_online_school = models.BooleanField(null=True, blank=True)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class PushNotificationData(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    click_action = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    for_mobile_users = models.BooleanField(default=False)
    for_desktop_users = models.BooleanField(default=False)
    city = models.ForeignKey("schools.City", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.city:
            return f"{self.title} - {self.city.name}"
        return f"{self.title}"

    class Meta:
        verbose_name = "Sent Notification"
        verbose_name_plural = "Sent Notifications"

class WhatsappSubscribers(models.Model):
    user = models.ForeignKey(User, related_name="WhatsappSubscribers", on_delete=models.CASCADE,null=True,blank=True)
    enquiry = models.ForeignKey(SchoolEnquiry, related_name="WhatsappSubscribersViaEnquiry", on_delete=models.CASCADE,null=True,blank=True)
    is_Subscriber = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=12)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        verbose_name = "WhatsApp Subscriber"
        verbose_name_plural = "WhatsApp Subscribers"

class UserSelectedCity(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(
        "schools.City", on_delete=models.SET_NULL, null=True, blank=True)
    is_boarding_school = models.BooleanField(null=True, blank=True)
    is_online_school = models.BooleanField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} on  {self.city}"

    class Meta:
        verbose_name = "User's City"
        verbose_name_plural = "User Cities"
