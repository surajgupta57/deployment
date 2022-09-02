import pytz
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token as AuthToken
from admission_forms.models import ChildSchoolCart,SchoolApplication,CommonRegistrationForm
from schools.models import SchoolEnquiry
from parents.models import ParentProfile
from childs.models import Child

class User(AbstractUser):
    is_parent = models.BooleanField(default=False)
    is_school = models.BooleanField(default=False)
    is_expert = models.BooleanField(default=False)
    is_brand = models.BooleanField(default=False)
    is_uniform_app = models.BooleanField(default=False)
    is_facebook_user = models.BooleanField(default=False)
    current_child = models.IntegerField(default=-1)
    current_school = models.IntegerField(default=-1)
    name = models.CharField(max_length=255, null=True, blank=True)
    current_parent = models.IntegerField(default=-1)
    ad_source = models.CharField(max_length=100, blank=True, null=True)

    def current_parent_detail(self):
        return ParentProfile.objects.filter(user=self, pk=self.current_parent)

    @property
    def get_cart_items_count(self):
        count=ChildSchoolCart.objects.filter(form__user=self.id).count()
        return count

    @property
    def get_school_applied_count(self):
        count=SchoolApplication.objects.filter(user=self.id).count()
        return count

    @property
    def get_school_enquiry_count(self):
        count=SchoolEnquiry.objects.filter(email=self.email).count()
        return count

    @property
    def get_phone_no(self):
        profile=ParentProfile.objects.get(user=self, pk=self.current_parent)
        return profile.phone

    @property
    def get_child_count(self):
        count=Child.objects.filter(user=self).count()
        return count

    @property
    def get_parent_profile_count(self):
        count=ParentProfile.objects.filter(user=self).count()
        return count

    @property
    def get_form_count(self):
        count=CommonRegistrationForm.objects.filter(user=self).count()
        return count

    # @property
    # def get_form(self):
    #     data=CommonRegistrationForm.objects.filter(user=self)
    #     if data.exists():
    #         list=[]
    #         for i in data:
    #             form={}
    #             form['']
    #             form['']
    #             form['']
    #     else:
    #         return ""


class Token(AuthToken):
    key = models.CharField("Key", max_length=40, db_index=True, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name="User",
    )
