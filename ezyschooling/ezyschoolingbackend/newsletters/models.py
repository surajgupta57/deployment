import uuid

from django.db import models
from django.utils.timezone import now


class Preference(models.Model):
    user = models.OneToOneField(
        "accounts.User", related_name="mail_preferences", on_delete=models.CASCADE)
    region = models.ForeignKey("schools.Region", on_delete=models.SET_NULL, null=True, blank=True)
    news = models.BooleanField(default=False)
    parenting = models.BooleanField(default=False)
    quiz = models.BooleanField(default=False)
    admission = models.BooleanField(default=False)
    family_annual_income = models.CharField(max_length=255, blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s Preferences"


class Subscription(models.Model):
    WEEKLY = "W"
    DAILY = "D"

    ADMISSION = "A"
    PARENTING = "P"
    NEWS = "N"
    QUIZ = "Q"

    GROUP_CHOICES = (
        (ADMISSION, "Admission"),
        (PARENTING, "Parenting"),
        (NEWS, "News"),
        (QUIZ, "Quiz")
    )

    FREQUENCY_CHOICES = (
        (WEEKLY, "Weekly"),
        (DAILY, "Daily")
    )

    uuid = models.UUIDField(
        editable=False, default=uuid.uuid4, verbose_name="UUID", null=True, blank=True)
    preferences = models.ForeignKey(
        Preference, null=True, blank=True, on_delete=models.CASCADE, related_name="subscriptions")
    email = models.EmailField(
        help_text="To be used for anonymous user", blank=True, null=True)
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, null=True, blank=True)
    group = models.CharField(max_length=10, choices=GROUP_CHOICES)
    active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    subscribed_date = models.DateTimeField(null=True, blank=True)
    unsubscribed_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Subscriber"
        verbose_name_plural = "Subscribers"

    def get_email(self):
        if self.preferences:
            return self.preferences.user.email
        return self.email

    def __str__(self):
        if self.preferences:
            return f"{self.preferences.user} - {self.group}"
        return f"{self.email} - {self.group}"
