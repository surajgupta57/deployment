import requests

from accounts.api.v1.serializers import UserSerializer
from admission_forms.models import (ChildSchoolCart,
                                    SchoolApplication)
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import transaction
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer

from admin_custom.models import ViewedParentPhoneNumberBySchool
from parents.api.v1.serializers import ParentAddressSerializer
from parents.models import ParentProfile
from rest_framework import serializers
from schools.documents import SchoolProfileDocument
from schools.models import *
from schools.tasks import send_school_signup_admin_alert
from notification.models import WhatsappSubscribers

class SchoolRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=allauth_settings.USERNAME_REQUIRED)
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    name = serializers.CharField(required=True, write_only=True)
    contact_name = serializers.CharField(required=True, write_only=True)
    contact_number = serializers.CharField(required=True, write_only=True)
    short_address = serializers.CharField(
        max_length=255, required=True, write_only=True)
    street_address = serializers.CharField(
        max_length=255, required=True, write_only=True)
    # city = serializers.CharField(max_length=50, required=True, write_only=True)
    # zipcode = serializers.CharField(
    #     max_length=7, required=True, write_only=True)
    # state = serializers.IntegerField(required=True, write_only=True)
    # region = serializers.IntegerField(required=True, write_only=True)
    district = serializers.IntegerField(required=True, write_only=True)
    city = serializers.IntegerField(required=True, write_only=True)
    state = serializers.IntegerField(required=True, write_only=True)
    pincode = serializers.IntegerField(required=True, write_only=True)
    district_region = serializers.IntegerField(required=True, write_only=True)
    country = serializers.IntegerField(required=True, write_only=True)
    latitude = serializers.DecimalField(required=False, max_digits=22, decimal_places=16)
    longitude = serializers.DecimalField(required=False, max_digits=22, decimal_places=16)
    password1 = serializers.CharField(required=True, write_only=True)

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
            "username": self.validated_data.get("username", ""),
            "email": self.validated_data.get("email", ""),
            "name": self.validated_data.get("name", ""),
            "contact_name": self.validated_data.get("contact_name", ""),
            "contact_number": self.validated_data.get("contact_number", ""),
            "short_address": self.validated_data.get("short_address", ""),
            "street_address": self.validated_data.get("street_address", ""),
            "zipcode": self.validated_data.get("zipcode", ""),
            # "city": self.validated_data.get("city", ""),
            # "state": self.validated_data.get("state", None),
            # "region": self.validated_data.get("region", None),
            "city": self.validated_data.get("city", None),
            "state": self.validated_data.get("state", None),
            "district": self.validated_data.get("district", None),
            "district_region": self.validated_data.get("district_region", None),
            "country": self.validated_data.get("country", None),
            "pincode": self.validated_data.get("pincode", None),
            "latitude": self.validated_data.get("latitude", ""),
            "longitude": self.validated_data.get("longitude", ""),
            "password1": self.validated_data.get("password1", ""),
            "ad_source": self.validated_data.get("ad_source")
        }

    def custom_signup(self, request, user):
        name = self.validated_data.get("name", "")
        contact_name = self.validated_data.get("contact_name", "")
        contact_number = self.validated_data.get("contact_number", "")
        short_address = self.validated_data.get("short_address", "")
        street_address = self.validated_data.get("street_address", "")
        zipcode = self.validated_data.get("zipcode", "")
        # city = self.validated_data.get("city", "")
        # state = self.validated_data.get("state", None)
        # region = self.validated_data.get("region", None)
        city = self.validated_data.get("city", None),
        state = self.validated_data.get("state", None),
        district =  self.validated_data.get("district",None),
        district_region = self.validated_data.get("district_region", None),
        country = self.validated_data.get("country", None),
        pincode = self.validated_data.get("pincode", None),
        email = self.validated_data.get("email", None)
        latitude = self.validated_data.get("latitude", None)
        try:
            ad_source = request.data["ad_source"]
        except Exception as e:
            ad_source = "undefined"
        if latitude == None:
            latitude = 28.644800
        longitude = self.validated_data.get("longitude", None)
        if longitude == None:
            longitude = 77.216721
        school = SchoolProfile(
            user=user,
            name=name,
            short_address=short_address,
            street_address=street_address,
            zipcode=zipcode,
            latitude=latitude,
            longitude=longitude)
        if country:
            school.school_country_id = country[0]
        if state:
            school.school_state_id = state[0]
        if city:
            school.school_city_id = city[0]
        if district:
            school.district_id = district[0]
        if district_region:
            school.district_region_id = district_region[0]
        if pincode:
            school.pincode_id = pincode[0]
        if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
            ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
        else:
            ad_source =''
        school.ad_source = ad_source
        school.save()
        Contact.objects.create(
            school=school, name=contact_name, phone=contact_number)
        return school.id

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        school_profile = self.custom_signup(request, user)
        transaction.on_commit(
            lambda: send_school_signup_admin_alert.delay(school_profile)
        )
        setup_user_email(request, user, [])
        user.is_school = True
        user.current_school = school_profile
        user.save()
        return user

class SchoolClassesSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolClasses
        fields = [
            "id",
            "name",
            "slug",
            "rank",
        ]


class SchoolTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolType
        fields = [
            "id",
            "name",
            "slug",
        ]


class SchoolBoardSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolBoard
        fields = [
            "id",
            "name",
            "slug",
        ]


class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "slug",
            "photo"
        ]


class PincodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pincode
        fields = [
            "id",
            "pincode",
            "type"
        ]

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            "id",
            "name",
            "slug",
            "photo"
        ]

class StatesSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    class Meta:
        model = States
        fields = [
            "id",
            "name",
            "slug",
            "photo",
            "country"
        ]



class CitySerializer(serializers.ModelSerializer):
    states = StatesSerializer()
    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "is_featured",
            "slug",
            "photo",
            "states",
        ]

class DistrictSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "slug",
            "photo",
             "city",
        ]

class DistrictSerializerWithoutCity(serializers.ModelSerializer):
    #city = CitySerializer()
    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "slug",
            "photo",
     #        "city",
        ]


class DistrictRegionSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    pincode = PincodeSerializer(many=True)
    class Meta:
        model = DistrictRegion
        fields = [
            "id",
            "name",
            "slug",
            "photo",
            "district",
            "pincode"
        ]


class AreaSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    states = StatesSerializer()
    city = CitySerializer()
    district = DistrictSerializer()
    district_area = DistrictRegionSerializer()
    pincode = PincodeSerializer(many=True)
    class Meta:
        model = Area
        fields = [
            "id",
            "name",
            "slug",
            "photo",
            "country",
            "states",
            "city",
            "district",
            "district_area",
            "pincode"
        ]


class SchoolFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolFormat
        fields = [
            "id",
            "title",
            "slug",
            "photo"
        ]


class StateSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = [
            "id",
            "name",
            "slug",
        ]


class AdmmissionOpenClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmmissionOpenClasses
        fields = [
            "id",
            "class_relation",
            "admission_open",
            "form_limit",
            "available_seats",
            "session",
            "last_date",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["class_relation"] = SchoolClassesSerializer(
            instance.class_relation).data
        return response

    def save(self, validated_data):
        open_classes = AdmmissionOpenClasses.objects.create(
            session=validated_data["session"],
            school=SchoolProfile.objects.get(slug=validated_data['school_slug']),
            class_relation=SchoolClasses.objects.get(id=validated_data['class_relation'])
        )
        return open_classes.id

    def update(self, instance, validated_data):
        instance.session = validated_data.get("session")
        instance.admission_open = validated_data.get("admission_open") or instance.admission_open
        instance.form_limit = validated_data.get("form_limit")
        instance.available_seats = validated_data.get("available_seats")
        instance.last_date = validated_data.get("last_date")
        instance.class_relation = SchoolClasses.objects.get(id=validated_data['class_relation'])
        instance.save()
        return instance.id


class SchoolAdmissionFormFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolAdmissionFormFee
        fields = [
            "id",
            "class_relation",
            "form_price",
            "created_at",
        ]

class AgeCriteriaSerializer(serializers.ModelSerializer):

    class_relation = SchoolClassesSerializer(read_only=True)

    class Meta:
        model = AgeCriteria
        fields = [
            "id",
            "class_relation",
            "session",
            "start_date",
            "end_date"
        ]

class SchoolStreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolStream
        fields = ("id","stream")

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields= ['id','rank','name','slug']

class SchoolProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "email",
            "slug",
            "phone_no",
            "website",
            "school_timings",
            "school_type",
            "school_board",
            "school_boardss",
            "school_format",
            "medium",
            "academic_session",
            "ownership",
            "latitude",
            "longitude",
            "short_address",
            "street_address",
            "city",
            "avg_fee",
            # "state",
            "zipcode",
            "logo",
            "cover",
            "year_established",
            "school_category",
            "description",
            "student_teacher_ratio",
            "form_price",
            "convenience_fee",
            "video_tour_link",
            "point_system",
            "required_admission_form_fields",
            "required_child_fields",
            "required_father_fields",
            "required_mother_fields",
            "required_guardian_fields",
            # "region",
            "scholarship_program",
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            "class_relation",
        ]


class SchoolProfileSerializer(serializers.ModelSerializer):

    unique_views = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    enquiries_count = serializers.SerializerMethodField()
    admmissionopenclasses_set = AdmmissionOpenClassesSerializer(
        read_only=True, many=True)
    agecriteria_set = AgeCriteriaSerializer(read_only=True, many=True)
    class_relation = SchoolClassesSerializer(read_only=True, many=True)
    school_type = SchoolTypeSerializer()
    school_board = SchoolBoardSerializer()
    school_boardss = SchoolBoardSerializer(read_only=True,many=True)
    school_format = SchoolFormatSerializer()
    medium = serializers.CharField(source="get_medium_display")
    ownership = serializers.CharField(source="get_ownership_display")
    # region = RegionSerializer()
    # state = StateSerializer()
    school_country = CountrySerializer()
    school_state = StatesSerializer()
    school_city = CitySerializer()
    district = DistrictSerializer()
    district_region = DistrictRegionSerializer()
    schooladmissionformfee_set = SchoolAdmissionFormFeeSerializer(read_only=True,many=True)
    languages = LanguageSerializer(many=True)
    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "email",
            "slug",
            "phone_no",
            "website",
            "school_timings",
            "school_type",
            "school_board",
            "school_boardss",
            "medium",
            "academic_session",
            "latitude",
            "longitude",
            "short_address",
            "street_address",
            "city",
            # "state",
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            "zipcode",
            "logo",
            "collab",
            "online_school",
            "boarding_school",
            "scholarship_program",
            "ownership",
            "school_format",
            "cover",
            "year_established",
            "school_category",
            "description",
            "student_teacher_ratio",
            "form_price",
            "video_tour_link",
            "required_admission_form_fields",
            "required_child_fields",
            "required_father_fields",
            "required_mother_fields",
            "required_guardian_fields",
            # "region",
            "unique_views",
            "total_views",
            "point_system",
            "enquiries_count",
            "views_permission",
            "views_check_permission",
            "enquiry_permission",
            "contact_data_permission",
            "counselling_data_permission",
            "class_relation",
            "admmissionopenclasses_set",
            "agecriteria_set",
            "is_active",
            "is_verified",
            "hide_point_calculator",
            "schooladmissionformfee_set",
            "virtual_tour",
            'languages',
            "built_in_area",
        ]
        read_only_fields = (
            "school_type",
            "school_board",
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            "collab",
            "class_relation",
            "schooladmissionformfee_set",
            "virtual_tour",
            "admmissionopenclasses_set")

    def get_unique_views(self, instance):
        return instance.profile_views.count()

    def get_enquiries_count(self, instance):
        return instance.enquiries.count()

    def get_total_views(self, instance):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if request.user.id is not None:
                user = request.user
                if user.is_parent:
                    if SchoolView.objects.filter(
                        school=instance, user_id=request.user.id).exists():
                        school_view = SchoolView.objects.get(school=instance, user_id=request.user.id)
                        school_view.count += 1
                        school_view.save()
                    else:
                        school_view_create = SchoolView.objects.create(school=instance, user_id=request.user.id)
                        school_view = SchoolView.objects.get(school=instance, user_id=request.user.id)
                        school_view.count += 1
                        school_view.save()
        instance.views = instance.views + 1
        instance.save()

        return instance.views


class GallerySerializer(serializers.ModelSerializer):

    class Meta:
        model = Gallery
        fields = [
            "id",
            "image",
        ]


class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = [
            "id",
            "activity_type",
            "name",
            "order",
        ]


class ActivityTypeCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActivityType
        fields = [
            "id",
            "name",
            "order",
        ]


class ActivityTypeSerializer(serializers.ModelSerializer):

    activities = ActivitySerializer(many=True, read_only=True)

    class Meta:
        model = ActivityType
        fields = [
            "id",
            "name",
            "activities",
        ]

class SchoolFeesTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolFeesType
        fields = '__all__'

class SchoolFeesParametersSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
  #  head = SchoolFeesTypeSerializer()
    class Meta:
        model = SchoolFeesParameters
        fields = '__all__'




class FeeStructureSerializer(serializers.ModelSerializer):

    class_relation = SchoolClassesSerializer()
    fees_parameters =  SchoolFeesParametersSerializer(many=True)
    stream_relation= SchoolStreamSerializer()
    class Meta:
        model = FeeStructure
        fields = [
            "id",
            "class_relation",
            "stream_relation",
            'fees_parameters',
            "fee_price",
            "session",
            "note",
        ]


def calculate_total_fees(tenure,price,head_id):
    total = 0
    if tenure == 'Monthly':
        total += (price * 12)
    elif tenure == 'Onetime':
       if head_id.head =='Admission Fees':
               pass
       else:
            total += price
    elif tenure == 'Quarterly':
        total += (price*4)
    else:
        total += price
    return total

class FeeStructureCreateUpdateSeirializer(serializers.ModelSerializer):
    fees_parameters = SchoolFeesParametersSerializer(many=True)
    class Meta:
        model = FeeStructure
        fields = [
            "id",
            "class_relation",
            "stream_relation",
            'fees_parameters',
            "fee_price",
            "session",
            "note",
        ]

    def create(self, validated_data):
        feestructureobj = FeeStructure.objects.create(
            class_relation=validated_data.get('class_relation'),
            stream_relation=validated_data.get('stream_relation'),
            school=validated_data.get('school'),
            session=validated_data.get('session'),
            note=validated_data.get('note'),
            )
        feestructureobj.save()
        total = 0
        if len(validated_data.get('fees_parameters'))!= 0:
            for i in range(0,len(validated_data.get('fees_parameters'))):
                obj = SchoolFeesParameters.objects.create(
                    tenure=validated_data.get('fees_parameters')[i].get('tenure'),
                    price=validated_data.get('fees_parameters')[i].get('price'),
                    upper_price=validated_data.get('fees_parameters')[i].get('upper_price'),
                    range=validated_data.get('fees_parameters')[i].get('range'),
                    refundable=validated_data.get('fees_parameters')[i].get('refundable'),
                    head=validated_data.get('fees_parameters')[i].get('head'),
                    school=validated_data.get('school')
                )
                total += calculate_total_fees(
                        validated_data.get('fees_parameters')[i].get('tenure'),
                        validated_data.get('fees_parameters')[i].get('price'),
                        validated_data.get('fees_parameters')[i].get('head')
                    )
                feestructureobj.fees_parameters.add(obj)
        feestructureobj.fee_price = (total/12)
        feestructureobj.save()
        return feestructureobj

    def update(self, instance, validated_data):
       instance.class_relation =  SchoolClasses.objects.get(name=validated_data.get('class_relation'))
       try:
           instance.stream_relation = SchoolStream.objects.get(stream=validated_data.get('stream_relation'))
       except SchoolStream.DoesNotExist:
           instance.stream_relation = None
       instance.fee_price = validated_data.get('fee_price', instance.fee_price)
       instance.save()

       if len(validated_data.get('fees_parameters')) == 0:
           instance.fees_parameters.clear()
       total = 0
       for i in range(0,len(validated_data.get('fees_parameters'))):
            if validated_data.get('fees_parameters')[i].get('id'):
                SchoolFeesParameters.objects.filter(
                id=validated_data.get('fees_parameters')[i].get('id')).update(
                    tenure=validated_data.get('fees_parameters')[i].get('tenure'),
                    price=validated_data.get('fees_parameters')[i].get('price'),
                    upper_price=validated_data.get('fees_parameters')[i].get('upper_price'),
                    range=validated_data.get('fees_parameters')[i].get('range'),
                    refundable=validated_data.get('fees_parameters')[i].get('refundable'),
                    head=validated_data.get('fees_parameters')[i].get('head'),
                    school = instance.school
                )
                total += calculate_total_fees(
                        validated_data.get('fees_parameters')[i].get('tenure'),
                        validated_data.get('fees_parameters')[i].get('price'),
                        validated_data.get('fees_parameters')[i].get('head')
                    )
            else:
                obj = SchoolFeesParameters.objects.create(
                	tenure=validated_data.get('fees_parameters')[i].get('tenure'),
                	price=validated_data.get('fees_parameters')[i].get('price'),
                    upper_price=validated_data.get('fees_parameters')[i].get('upper_price'),
                    range=validated_data.get('fees_parameters')[i].get('range'),
                	refundable=validated_data.get('fees_parameters')[i].get('refundable'),
                	head=validated_data.get('fees_parameters')[i].get('head'),
                	school = instance.school
                )
                total += calculate_total_fees(
                        validated_data.get('fees_parameters')[i].get('tenure'),
                        validated_data.get('fees_parameters')[i].get('price'),
                        validated_data.get('fees_parameters')[i].get('head')

                    )
                instance.fees_parameters.add(obj)
       instance.fee_price = (total/12)
       instance.note=validated_data.get('note')
       instance.save()
       return instance


class SchoolPointCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolPoint
        fields = [
            "single_child_points",
            "siblings_points",
            "parent_alumni_points",
            "staff_ward_points",
            "first_born_child_points",
            "first_girl_child_points",
            "transport_facility_points",
            "single_girl_child_points",
            "is_christian_points",
            "girl_child_points",
            "single_parent_points",
            "minority_points",
            "student_with_special_needs_points",
            "children_of_armed_force_points",
            'father_covid_vacination_certifiacte_points',
            'mother_covid_vacination_certifiacte_points',
            'guardian_covid_vacination_certifiacte_points',
            'mother_covid_19_frontline_warrior_points',
            'father_covid_19_frontline_warrior_points',
            'guardian_covid_19_frontline_warrior_points',
            'state_transfer_points',
        ]


class DistancePointSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistancePoint
        fields = [
            "id",
            "start",
            "end",
            "point",
        ]


class SchoolDashboardProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "logo",
            "school_type",
            "school_board",
            "school_boardss",
            "school_category",
            "class_relation",
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            "scholarship_program",
        ]


class SchoolDashboardProfileSerializer(serializers.ModelSerializer):

    unique_views = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    admmissionopenclasses_set = AdmmissionOpenClassesSerializer(
        read_only=True, many=True)
    class_relation = SchoolClassesSerializer(read_only=True, many=True)
    school_type = SchoolTypeSerializer()
    school_board = SchoolBoardSerializer()
    school_boardss = SchoolBoardSerializer(read_only=True,many=True)
    region = RegionSerializer()
    state = StateSerializer()

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "unique_views",
            "total_views",
            "logo",
            "school_type",
            "school_board",
            "school_boardss",
            "school_category",
            "class_relation",
            "admmissionopenclasses_set",
            "scholarship_program",
            "boarding_school",
        ]

    def get_unique_views(self, instance):
        return instance.profile_views.count()

    def get_total_views(self, instance):
        return instance.views


class SchoolApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolApplication
        fields = [
            'uid',
            'apply_for',
            'child',
            'form',
            'timestamp',
            'total_points',
            'distance_points',
            'single_child_points',
            'siblings_studied_points',
            'parents_alumni_points',
            'staff_ward_points',
            'first_born_child_points',
            'first_girl_child_points',
            'transport_facility_points',
            'single_girl_child_points',
            'christian_points',
            'viewed',
            'girl_child_point',
            'single_parent_point',
            'minority_points',
            'student_with_special_needs_points',
            'children_of_armed_force_points',
            'father_covid_vacination_certifiacte_points',
            'mother_covid_vacination_certifiacte_points',
            'guardian_covid_vacination_certifiacte_points',
            'mother_covid_19_frontline_warrior_points',
            'father_covid_19_frontline_warrior_points',
            'guardian_covid_19_frontline_warrior_points',
            'state_transfer_points',
        ]


class SchoolFormApplicationProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "collab",
        ]


class SchoolViewSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    classes = serializers.SerializerMethodField()
    added_in_cart = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = SchoolView
        fields = [
            "id",
            "parent",
            "count",
            "classes",
            "updated_at",
            "added_in_cart",
            'location',
        ]

    def get_classes(self, instance):
        return list(
            instance.user.user_childs.values_list(
                "class_applying_for__name",
                flat=True).distinct())

    def get_parent(self, instance):
        parent_id = int(instance.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        request = self.context.get("request")
        school = SchoolProfile.objects.get(id=request.user.current_school)
        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, school_view=instance).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            result = {"name": parent.name, "phone": parent.phone, "email": parent.email, 'viewed': True}
            return result
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = parent.phone.replace(" ", "").split(",") if parent.phone else []
            list2 = []
            if len(n)>0:
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
            result = {"name":parent.name,"phone":hidden_number,"email":parent.email, 'viewed': False}
            return result

    def get_added_in_cart(self, instance):
        return ChildSchoolCart.objects.filter(child__user=instance.user, school=instance.school).exists()

    def get_location(self,instance):
        parent_id = int(instance.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        address = parent.parent_address.all().first()
        return ParentAddressSerializer(address).data

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["updated_at"] = naturaltime(instance.updated_at)
        return response


class SchoolOngoingApplicationsSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = ChildSchoolCart
        fields = [
            "id",
            "parent",
            "timestamp",
            'location',
        ]

    def get_parent(self, instance):
        parent_id = int(instance.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        request = self.context.get("request")
        school = SchoolProfile.objects.get(id=request.user.current_school)
        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, ongoing_application=instance).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            result = {"name": parent.name, "phone": parent.phone, "email": parent.email, 'viewed': True}
            return result
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = parent.phone.replace(" ", "").split(",") if parent.phone else []
            list2 = []
            if len(n)>0:
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
            result = {"name":parent.name,"phone":hidden_number,"email":parent.email, 'viewed': False}
            return result

    def get_location(self,instance):
        parent_id = int(instance.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        address = parent.parent_address.all().first()
        return ParentAddressSerializer(address).data

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["timestamp"] = naturaltime(instance.timestamp)
        return response


class SchoolEnquirySerializer(serializers.ModelSerializer):
    # class_relation = serializers.CharField(source="class_relation.name",default="NA")
    class Meta:
        model = SchoolEnquiry
        fields = [
            "parent_name",
            "phone_no",
            "email",
            "query",
            "source",
            "ad_source",
            "timestamp",
            "class_relation",
        ]
        extra_kwargs = {
            'timestamp': {'read_only': True},
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.user:
            parent = ParentProfile.objects.get(id=instance.user.current_parent)
            response["parent_name"] = parent.name
            response["email"] = parent.email
            if parent.phone:
                response["phone_no"] = parent.phone
            else:
                response["phone_no"] = instance.phone_no
        else:
            response["parent_name"] = instance.parent_name
            response["email"] = instance.email
            response["phone_no"] = instance.phone_no
        user_id = settings.WHATSAPP_HSM_USER_ID
        password = settings.WHATSAPP_HSM_USER_PASSWORD
        phone_wa = f"91{instance.phone_no}" if len(instance.phone_no) <= 10 else instance.phone_no
        WhatsappSubscribers.objects.create(enquiry=instance, is_Subscriber=True, phone_number=instance.phone_no)
        requests.get(f"https://media.smsgupshup.com/GatewayAPI/rest?method=OPT_IN&format=json&userid={user_id}&password={password}&phone_number={phone_wa}&v=1.1&auth_scheme=plain&channel=WHATSAPP")
        return response


class SchoolCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolVerificationCode
        fields = [
            "name",
            "address",
            "code",
        ]

        extra_kwargs = {
            "name": {
                "required": False
            },
            "address": {
                "required": False
            }
        }


class AlumniSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug"
        ]


class FeaturedSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolProfile
        fields = [
            "name",
            "city",
            "slug",
            "logo"
        ]


class ActivityTypeAutocompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityTypeAutocomplete
        fields = [
            "id",
            "name"
        ]


class ActivityAutocompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityAutocomplete
        fields = [
            "name"
        ]


class AgeCriteriaCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = AgeCriteria
        fields = [
            "id",
            "class_relation",
            "session",
            "start_date",
            "end_date"
        ]


class SchoolDocumentSerializer(DocumentSerializer):
    highlight = serializers.SerializerMethodField()

    class Meta:
        document = SchoolProfileDocument
        fields = [
            "id",
            "name",
            "email",
            "slug",
            "phone_no",
            "website",
            "school_timings",
            "street_address",
            "city",
            "zipcode",
            "collab",
            "year_established",
            "school_category",
            "description",
            "student_teacher_ratio",
            "point_system",
            "is_active",
            "is_verified",
            "form_price",
            "total_points",
            "logo",
            "hide_point_calculator",
            "max_fees",
            "min_fees",
            # Nested Fields
            "school_type",
            "school_format",
            "school_board",
            "school_boardss",
            "region",
            "state",
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            "feature_set",
            "class_relation",
            "admmissionopenclasses_set",
            "feestructure_set",
            "agecriteria_set",
            "geocoords",

            "admissionclasses_open_count",
            "unique_views",
            "total_views",
        ]

    def get_highlight(self, obj):
        if hasattr(obj.meta, 'highlight'):
            return obj.meta.highlight.__dict__['_d_']
        return {}

    def to_representation(self, instance):
        response = super().to_representation(instance)
        user = self.context["request"].user
        if user.is_authenticated and user.is_parent:
            points = 0
            response["your_points"] = points
        return response


class SchoolPDFProfileSerializer(serializers.ModelSerializer):
    state = StateSerializer()

    class Meta:
        model = SchoolProfile
        fields = [
            "name",
            "logo",
            "short_address",
            "street_address",
            "city",
            "state",
            "zipcode",
            "phone_no"
        ]

class SchoolAdmissionAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolAdmissionAlert
        fields = [
            "id",
            "school_relation",
            "class_relation",
            "created_at"
        ]
        read_only_fields=['id']

class SchoolUploadCsvSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedSchoolSelectedCsv
        fields = [
            "id",
            "school_relation",
            "csv_file",
        ]

class SchoolSelectedChildDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedStudentFromCsv
        fields = [
            "id",
            "school_relation",
            "csv_file",
        ]

class FeatureNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureName
        fields = [
            "id",
            "name",
        ]

class SubFeatureSerializer(serializers.ModelSerializer):
    parent = FeatureNameSerializer()
    class Meta:
        model = Subfeature
        fields = [
            "id",
            "name",
            "parent",
        ]

class SchoolFeaturesSerializer(serializers.ModelSerializer):
    features = SubFeatureSerializer()
    class Meta:
        model = Feature
        fields = [
            "id",
            "school",
            "exist",
            "features"
        ]

class AdmissionSessionsSerializer(serializers.ModelSerializer):

    class Meta():
        model = AdmissionSession
        fields='__all__'


class SchoolAvailableClassesSerializer(serializers.ModelSerializer):
    class_relation = SchoolClassesSerializer(read_only=True, many=True)
    class Meta:
        model = SchoolProfile
        fields = [
            "class_relation",
        ]
        read_only_fields = (
            "class_relation",
        )

class AdmissionPageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionPageContent
        fields='__all__'

# Notify Me
class SchoolClassNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolClassNotification
        fields = '__all__'


class SchoolProfileCartSerializer(serializers.ModelSerializer):
    district_region = DistrictRegionSerializer()
    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug",
            "form_price",
            "convenience_fee",
            "collab",
            "timestamp",
            "street_address",
            "city",
            "state",
            "zipcode",
            "logo",
            "required_admission_form_fields",
            "required_child_fields",
            "required_father_fields",
            "required_mother_fields",
            "required_guardian_fields",
            "district_region",
        ]

class SchoolAdmissionResultImageSerializer(serializers.ModelSerializer):

   class Meta:
       model = SchoolAdmissionResultImage
       fields = [
           "id",
           "image",
           "name",
       ]

class SchoolConatctSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()

    class Meta:
        model = SchoolContactClickData
        fields = [
            "id",
            "name",
            "mobile_number",
            "email",
            "count_school",
        ]
    def get_name(self,instance):
        parent_id = int(instance.user.current_parent)
        if ParentProfile.objects.filter(pk=parent_id).exists():
            parent = ParentProfile.objects.get(pk=parent_id)
            return parent.name
        else:
            return ""
    def get_email(self,instance):
        return instance.user.email

    def get_mobile_number(self,instance):
        request = self.context.get("request")
        school = SchoolProfile.objects.get(id=request.user.current_school)
        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, parent_called=instance).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            return {"mobile_number": instance.mobile_number,"viewed":True}
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = instance.mobile_number.replace(" ", "").split(",") if instance.mobile_number else []
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
            return {"mobile_number":hidden_number,"viewed":False}
        else:
            return instance.mobile_number


    def to_representation(self, instance):
        total_count = 0
        if SchoolContactClickData.objects.filter(school=instance.school).exists():
            all_data = SchoolContactClickData.objects.filter(school=instance.school)
            for data in all_data:
                total_count += data.count_school
            response = super().to_representation(instance)
        response["total_school_count"] = total_count
        return response

class HomePageSchoolSerializer(serializers.ModelSerializer):

   class Meta:
       model = SchoolProfile
       fields = [
           "id",
           "logo",
           "name",
           "slug",
       ]
