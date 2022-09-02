from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from django.conf import settings
from core.utils import Base64ImageField
from newsletters.models import Preference, Subscription
from newsletters.tasks import subscribe_registered_user
from parents.models import *
from schools.models import SchoolEqnuirySource
from parents.tasks import *
from phones.models import PhoneNumber
from phones.utils import send_verification_code
from accounts.api.v1 import views
from notification.models import WhatsappSubscribers


class ParentRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=allauth_settings.USERNAME_REQUIRED)
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    phone = serializers.CharField(required=True, max_length=30)
    name = serializers.CharField(required=True, write_only=True)
    password1 = serializers.CharField(required=True, write_only=True)
    mail_pref = serializers.BooleanField(required=True)
    is_uniform_app = serializers.BooleanField(required=False)
    is_facebook_user = serializers.BooleanField(required=False)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address.")
                )
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def get_cleaned_data(self):
        return {
            "name": self.validated_data.get("name", ""),
            "password1": self.validated_data.get("password1", ""),
            "username": self.validated_data.get("username", ""),
            "email": self.validated_data.get("email", ""),
            "phone": self.validated_data.get("phone", ""),
            "mail_pref": self.validated_data.get("mail_pref", ""),
            "whatsapp": self.validated_data.get("whatsapp"),
            "ad_source": self.validated_data.get("ad_source")

        }

    def custom_signup(self, request, user):
        name = self.validated_data.get("name", "")
        email = self.validated_data.get("email", "")
        phone = self.validated_data.get("phone", "")
        try:
            ad_source = request.data["ad_source"]
        except Exception as e:
            ad_source = "undefined"
        whatsapp = self.validated_data.get("whatsapp", "yes")
        user_id = settings.WHATSAPP_HSM_USER_ID
        password = settings.WHATSAPP_HSM_USER_PASSWORD
        if whatsapp == "yes":
            if WhatsappSubscribers.objects.filter(phone_number=phone).exists():
                obj = WhatsappSubscribers.objects.filter(phone_number=phone).first()
                obj.is_Subscriber = True
                obj.user = user
                obj.save()
                phone_wa = f"91{phone}" if len(phone) == 10 else phone
                requests.get(f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_IN&format=json&userid={user_id}&password={password}&phone_number={phone_wa}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
            else:
                obj = WhatsappSubscribers.objects.create(user=user,phone_number=phone)
                obj.is_Subscriber = True
                obj.save()
                phone_wa = f"91{phone}" if len(phone) == 10 else phone
                requests.get(f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_IN&format=json&userid={user_id}&password={password}&phone_number={phone_wa}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
        if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
            ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
        else:
            ad_source =''
        user.ad_source=ad_source
        user.save()
        parent_profile = ParentProfile.objects.create(
            user=user, name=name, email=email, phone=phone)
        return parent_profile.id

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        mail_pref = self.cleaned_data.pop("mail_pref")
        phone = self.cleaned_data["phone"]
        whatsapp = self.cleaned_data["whatsapp"]
        adapter.save_user(request, user, self)
        parent_profile = self.custom_signup(request, user)
        transaction.on_commit(
            lambda: add_parent_to_google_sheets.delay(parent_profile)
        )
        newsletter_pref = Preference.objects.create(user=user, parenting=mail_pref)
        subs = Subscription.objects.create(
            preferences=newsletter_pref,
            group=Subscription.PARENTING,
            active=mail_pref,
            subscribed_date=now())
        if mail_pref:
            transaction.on_commit(
                lambda: subscribe_registered_user.delay(subs.get_email())
            )
        setup_user_email(request, user, [])
        views.login_signal.send(sender=self.__class__, PING=True,user=user)
        user.is_parent = True
        is_uniform_app=self.validated_data.get("is_uniform_app", "")
        if is_uniform_app:
            user.is_uniform_app=True

        is_facebook_user = self.validated_data.get("is_facebook_user", "")
        if is_facebook_user:
            user.is_facebook_user=True

        user.current_parent = parent_profile
        name = self.validated_data.get("name", "")
        user.name = name
        user.save()
        transaction.on_commit(
            lambda: send_parent_welcome_mail.delay(parent_profile)
        )
        return user


class ParentProfileDetailSerializer(serializers.ModelSerializer):

    phone_verified = serializers.SerializerMethodField()

    class Meta:
        model = ParentProfile
        fields = [
            "id",
            "user",
            "email",
            "name",
            "date_of_birth",
            "gender",
            "slug",
            "photo",
            "income",
            "aadhaar_number",
            "companyname",
            "transferable_job",
            "special_ground",
            "designation",
            "profession",
            "special_ground_proof",
            "parent_aadhar_card",
            "pan_card_proof",
            "phone",
            "phone_verified",
            "bio",
            "parent_type",
            "education",
            "occupation",
            "office_address",
            "office_number",
            "street_address",
            "city",
            "state",
            "pincode",
            "country",
            "alumni_school_name",
            "alumni_year_of_passing",
            "passing_class",
            "alumni_proof",
            "timestamp",
            "covid_vaccination_certificate",
            "frontline_helper",
            'college_name',
            'course_name',
        ]
        read_only_fields = ["id", "slug", "user"]

    def get_phone_verified(self, instance):
        phone = PhoneNumber.objects.filter(user=instance.user, number=instance.phone)
        if phone.exists():
            if not WhatsappSubscribers.objects.filter(user=instance.user).exists():
                WhatsappSubscribers.objects.create(user=instance.user,phone_number=instance.phone,is_Subscriber=True)
            return phone.first().verified
        else:
            return False


class ParentProfileAddSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentProfile
        fields = [
            "id",
            "user",
            "email",
            "name",
            "date_of_birth",
            "gender",
            "slug",
            "photo",
            "income",
            "phone",
            "bio",
            "aadhaar_number",
            "companyname",
            "transferable_job",
            "special_ground",
            "designation",
            "profession",
            "special_ground_proof",
            "parent_aadhar_card",
            "pan_card_proof",
            "parent_type",
            "education",
            "occupation",
            "street_address",
            "city",
            "state",
            "pincode",
            "country",
            "office_address",
            "office_number",
            "alumni_school_name",
            "alumni_year_of_passing",
            "passing_class",
            "alumni_proof",
            "covid_vaccination_certificate",
            "frontline_helper",
            'college_name',
            'course_name',
            "timestamp",
        ]

class ParentAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentAddress
        fields = [
            # "id",
            "street_address",
            "city",
            "state",
            "pincode",
            "country",
            "region",
            "monthly_budget",
        ]
        extra_kwargs = {'street_address': {'required': True},
                        'city': {'required': True},
                        'pincode': {'required': True},
                        }
class ParentArticleProfileSerializer(serializers.ModelSerializer):
    photo = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = ParentProfile
        fields = [
            "id",
            "name",
            "photo",
            "slug",
        ]


class ParentSchoolViewProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentProfile
        fields = [
            "name",
            "phone",
            "email"
        ]
