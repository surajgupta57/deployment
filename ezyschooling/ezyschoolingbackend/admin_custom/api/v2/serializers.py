from django.db import transaction
from datetime import datetime

from rest_framework import serializers
from schools.tasks import send_school_signup_admin_alert
from django.utils.translation import ugettext_lazy as _
from childs.api.v1.serializers import ChildSerialzer
from celery.utils.log import get_task_logger
from schools.models import SchoolProfile, City, District, DistrictRegion, States, Pincode, SchoolBoard, SchoolFormat, Area, Country, AdmmissionOpenClasses, SchoolAdmissionFormFee, Contact
from admin_custom.models import CAdminUser, SalesCAdminUser, UserType, CounselingAction, CommentSection, ActionSection, ParentCallScheduled
from admin_custom.models import CAdminUser, SalesCAdminUser, UserType, CounselorCAdminUser
from accounts.api.v1.serializers import UserSerializer
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from schools.models import SchoolEnquiry
from parents.models import ParentProfile
from accounts.api.v1 import views
from accounts.models import *
from schools.api.v1.serializers import SchoolClassesSerializer
logger = get_task_logger(__name__)


class SchoolProfileInsideSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField(
        method_name="get_address", read_only=True
    )
    school_city = serializers.SerializerMethodField(
        method_name="get_school_city", read_only=True
    )
    district = serializers.SerializerMethodField(
        method_name="get_district", read_only=True
    )
    district_region = serializers.SerializerMethodField(
        method_name="get_district_region", read_only=True
    )
    school_state = serializers.SerializerMethodField(
        method_name="get_school_state", read_only=True
    )
    school_country = serializers.SerializerMethodField(
        method_name="get_school_country", read_only=True
    )
    class_relation = serializers.SerializerMethodField(
        method_name="get_class_relation", read_only=True
    )
    languages = serializers.SerializerMethodField(
        method_name="get_languages", read_only=True
    )
    school_boardss = serializers.SerializerMethodField(
        method_name="get_school_boardss", read_only=True
    )

    class Meta:
        model = SchoolProfile
        fields = "__all__"

    def get_address(self, obj):
        return {"street_address":obj.street_address,"short_address":obj.short_address}
    def get_school_city(self, obj):
        if obj.school_city:
            return {"id":obj.school_city.id,"name":obj.school_city.name}
        else:
            return None
    def get_district(self, obj):
        if obj.district:
            return {"id":obj.district.id,"name":obj.district.name}
        else:
            return None
    def get_district_region(self, obj):
        if obj.district_region:
            return {"id":obj.district_region.id,"name":obj.district_region.name}
        else:
            return None
    def get_school_state(self, obj):
        if obj.school_state:
            return {"id":obj.school_state.id,"name":obj.school_state.name}
        else:
            return None
    def get_school_country(self, obj):
        if obj.school_country:
            return {"id":obj.school_country.id,"name":obj.school_country.name}
        else:
            return None

    def get_school_boardss(self, obj):
        if obj.school_boardss.filter():
            boards = obj.school_boardss.filter()
            res = []
            for sch_bds in boards:
                res.append({"id": sch_bds.id, "name": sch_bds.name})
            return res
        else:
            return []

    def get_languages(self, obj):
        if obj.languages.filter():
            languages = obj.languages.filter()
            res = []
            for lang in languages:
                res.append({"id": lang.id, "name": lang.name})
            return res
        else:
            return []

    def get_class_relation(self, obj):
        if obj.class_relation.filter():
            classes = obj.class_relation.filter()
            res = []
            for cls in classes:
                res.append({"id": cls.id, "name": cls.name})
            return res
        else:
            return []

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.short_name = validated_data["short_name"]
        instance.phone_no = validated_data["phone_no"]
        instance.medium = validated_data["medium"]
        instance.academic_session = validated_data["academic_session"]
        instance.short_name = validated_data["short_name"]
        instance.latitude = validated_data["latitude"]
        instance.longitude = validated_data["longitude"]
        instance.short_address = validated_data["short_address"]
        instance.street_address = validated_data["street_address"]
        instance.collab = validated_data["collab"]
        instance.online_school = validated_data["online_school"]
        instance.year_established = validated_data["year_established"]
        instance.built_in_area = validated_data["built_in_area"]
        instance.school_category = validated_data["school_category"]
        instance.avg_fee = validated_data["avg_fee"]
        instance.calculated_avg_fee = validated_data["calculated_avg_fee"]
        instance.ownership = validated_data["ownership"]
        instance.description = validated_data["description"]
        instance.student_teacher_ratio = validated_data["student_teacher_ratio"]
        instance.is_active = validated_data["is_active"]
        instance.for_homepage = validated_data["for_homepage"]
        instance.is_featured = validated_data["is_featured"]
        instance.form_price = validated_data["form_price"]
        instance.convenience_fee = validated_data["convenience_fee"]
        instance.video_tour_link = validated_data["video_tour_link"]
        instance.point_system = validated_data["point_system"]
        instance.hide_point_calculator = validated_data["hide_point_calculator"]
        instance.required_admission_form_fields = validated_data["required_admission_form_fields"]
        instance.required_child_fields = validated_data["required_child_fields"]
        instance.required_mother_fields = validated_data["required_mother_fields"]
        instance.required_father_fields = validated_data["required_father_fields"]
        instance.required_guardian_fields = validated_data["required_guardian_fields"]
        instance.visits = validated_data["visits"]
        instance.views = validated_data["views"]
        instance.views_permission = validated_data["views_permission"]
        instance.views_check_permission = validated_data["views_check_permission"]
        instance.enquiry_permission = validated_data["enquiry_permission"]
        instance.contact_data_permission = validated_data["contact_data_permission"]
        instance.counselling_data_permission = validated_data["counselling_data_permission"]
        instance.virtual_tour = validated_data["virtual_tour"]
        instance.last_avg_fee_calculated = validated_data["last_avg_fee_calculated"]
        instance.logo = validated_data["logo"]
        instance.cover = validated_data["cover"]
        instance.school_board = SchoolBoard.objects.get(id=validated_data['school_board']['id'])
        instance.school_format = SchoolFormat.objects.get(id=validated_data['school_format']['id'])
        instance.school_area = Area.objects.get(id=validated_data['school_area']['id'])
        instance.district_region = DistrictRegion.objects.get(id=validated_data['district_region']['id'])
        instance.district = District.objects.get(id=validated_data['district']['id'])
        instance.school_city = City.objects.get(id=validated_data['school_city']['id'])
        instance.school_state = States.objects.get(id=validated_data['school_state']['id'])
        instance.school_country = Country.objects.get(id=validated_data['school_country']['id'])
        instance.pincode = Pincode.objects.get(id=validated_data['pincode']['id'])
        instance.school_state = States.objects.get(id=validated_data['school_state']['id'])
        instance.school_state = States.objects.get(id=validated_data['school_state']['id'])
        instance.school_state = States.objects.get(id=validated_data['school_state']['id'])

        old_sch_boards = instance.school_boardss.filter()
        old_languages = instance.languages.filter()
        old_class_relations = instance.class_relation.filter()
        if not validated_data["school_boardss"]:
            for old_sch_board in old_sch_boards:
                instance.school_boardss.remove(old_sch_board)

        for old_sch_board in old_sch_boards:
            for board_data in validated_data["school_boardss"]:
                if str(old_sch_board.id) != str(
                    board_data["id"]
                ):  # working deletion now
                    instance.school_boardss.remove(old_sch_board)

        for board_data in validated_data["school_boardss"]:  # working for addition too.
            instance.school_boardss.add(board_data["id"])

        if not validated_data["languages"]:
            for old_language in old_languages:
                instance.languages.remove(old_language)

        for old_language in old_languages:
            for language_data in validated_data["languages"]:
                if str(old_language.id) != str(
                    language_data["id"]
                ):  # working deletion now
                    instance.languages.remove(old_language)

        for language_data in validated_data["languages"]:  # working for addition too
            instance.languages.add(language_data["id"])
        if not validated_data["class_relation"]:
            for old_class_relation in old_class_relations:
                instance.class_relation.remove(old_class_relation)

        for old_class_relation in old_class_relations:
            for class_relation_data in validated_data["class_relation"]:
                if str(old_class_relation.id) != str(
                    language_data["id"]
                ):  # working deletion now
                    instance.languages.remove(old_class_relation)

        for class_relation_data in validated_data["class_relation"]:  # working for addition too.
            instance.class_relation.add(class_relation_data["id"])


        instance.save()
        return instance.slug


class DatabaseAdmmissionOpenClassesSerializer(serializers.ModelSerializer):

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

class DatabaseSchoolAdmissionFormFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolAdmissionFormFee
        fields = [
            "id",
            "school_relation",
            "class_relation",
            "form_price",
            "created_at",
        ]


class DatabaseSchoolRegisterSerializer(serializers.Serializer):
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
            "city": self.validated_data.get("city", None),
            "state": self.validated_data.get("state", None),
            "district": self.validated_data.get("district", None),
            "district_region": self.validated_data.get("district_region", None),
            "country": self.validated_data.get("country", None),
            "pincode": self.validated_data.get("pincode", None),
            "latitude": self.validated_data.get("latitude", ""),
            "longitude": self.validated_data.get("longitude", ""),
            "password1": self.validated_data.get("password1", ""),
        }

    def custom_signup(self, request, user):
        name = self.validated_data.get("name", "")
        contact_name = self.validated_data.get("contact_name", "")
        contact_number = self.validated_data.get("contact_number", "")
        short_address = self.validated_data.get("short_address", "")
        street_address = self.validated_data.get("street_address", "")
        zipcode = self.validated_data.get("zipcode", "")
        city = self.validated_data.get("city", None),
        state = self.validated_data.get("state", None),
        district =  self.validated_data.get("district",None),
        district_region = self.validated_data.get("district_region", None),
        country = self.validated_data.get("country", None),
        pincode = self.validated_data.get("pincode", None),
        email = self.validated_data.get("email", None)
        latitude = self.validated_data.get("latitude", None)
        if latitude == None:
            latitude = 28.644800
        longitude = self.validated_data.get("longitude", None)
        if longitude == None:
            longitude = 77.216721
        school = SchoolProfile(
            user=user,
            name=name,
            email=email,
            phone_no=contact_number,
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
            lambda: send_school_signup_admin_alert(school_profile, created_by="db_team")
        )
        setup_user_email(request, user, [])
        user.is_school = True
        user.current_school = school_profile
        user.save()
        return user

class ParentCallScheduledSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentCallScheduled
        fields = (
            "id",
            "user",
            "city",
            "name",
            "phone",
            "message",
            "time_slot",
            "timestamp",
        )

    def save(self, validated_data, user):
        obj = ParentCallScheduled.objects.create(
            city=City.objects.get(id=validated_data["city"]),
            name=validated_data["name"],
            phone=validated_data["phone"],
            message=validated_data["message"],
        )
        obj.time_slot = validated_data["time_slot"]
        obj.user = User.objects.filter(id=user.id).first() if user else None
        obj.save()
        return obj.id


class CounselorUserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CounselorCAdminUser

        fields = [
            "id",
            "user",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["user"] = instance.user.user_ptr.name
        return rep
