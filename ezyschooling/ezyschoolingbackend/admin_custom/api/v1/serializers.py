from rest_framework import serializers

from childs.api.v1.serializers import ChildSerialzer
from celery.utils.log import get_task_logger
from schools.models import SchoolProfile, City, District, DistrictRegion, States, Pincode
from admin_custom.models import CAdminUser, SalesCAdminUser, UserType, CounselingAction, CommentSection, ActionSection, DatabaseCAdminUser, CounselorCAdminUser
from accounts.api.v1.serializers import UserSerializer
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from accounts.api.v1 import views
from accounts.models import *
logger = get_task_logger(__name__)


class SchoolProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolProfile
        fields = ['collab', 'district_region', 'district', 'school_city', 'school_state']


class CAdminUserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = (
            "id",
            "category_name",
        )


class ActionSectionSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        model = ActionSection
        fields = (
            "id",
            "category",
            "name",
            "slug",
        )


class CounselingChildDataSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_applying_for.name')

    class Meta:
        model = Child
        fields = [
            "id",
            "name",
            "date_of_birth",
            "gender",
            "class_name",
        ]


class SchoolProfileForCounselingSerializer(serializers.ModelSerializer):
    school_city_name = serializers.CharField(source='school_city.name')
    district_region_name = serializers.CharField(source='district_region.name')
    district_name = serializers.CharField(source='district.name')

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "slug",
            "school_city",
            "school_city_name",
            "district_region",
            "district_region_name",
            "district",
            "district_name",
        ]


class CounselingChildSchoolCartSerializer(serializers.ModelSerializer):
    school = SchoolProfileForCounselingSerializer(read_only=True)
    child = CounselingChildDataSerializer(read_only=True)

    class Meta:
        model = ChildSchoolCart
        fields = [
            "id",
            "school",
            "child",
            "session",
            "timestamp",
        ]


class CounselingSchoolEnquirySerializer(serializers.ModelSerializer):
    school = SchoolProfileForCounselingSerializer(read_only=True)
    user = serializers.CharField(source='user.name', default=None)

    class Meta:
        model = SchoolEnquiry
        fields = [
            "id",
            "user",
            "parent_name",
            "school",
            "phone_no",
            "email",
            "query",
            "source",
            "timestamp",
        ]
        extra_kwargs = {
            'timestamp': {'read_only': True},
        }


class CounselingSchoolApplicationSerializer(serializers.ModelSerializer):
    school = SchoolProfileForCounselingSerializer(read_only=True)
    child = CounselingChildDataSerializer(read_only=True)

    class Meta:
        model = SchoolApplication
        fields = [
            "id",
            "uid",
            "school",
            "child",
        ]


# class CounselingActionSerializer(serializers.ModelSerializer):
#     comment = serializers.SerializerMethodField()
#     enquiry_data = CounselingSchoolEnquirySerializer(allow_null=True)
#
#     class Meta:
#         model = CounselingAction
#         fields = [
#             'id',
#             'user',
#             'enquiry_data',
#             'counseling_user',
#             'child_data',
#             'enquiry_action',
#             'child_action',
#             'enquiry_scheduled_time',
#             'child_scheduled_time',
#             'comment',
#             'created_at',
#             'updated_at',
#         ]
#
#     def get_comment(self, obj):
#         if not obj.user:
#             comment_obj = CommentSection.objects.filter(
#                 user__isnull=True,
#                 enquiry_comment=obj.enquiry_data,
#                 counseling=obj.counseling_user,
#                 )
#             res = [
#                 {"counselor": c_obj.counseling.user.user_ptr.name, "data": c_obj.comment, "timestamp": c_obj.timestamp}
#                 for c_obj in comment_obj]
#             return res
#         elif obj.user and obj.child_data and obj.enquiry_data:
#             comment_obj = CommentSection.objects.filter(
#                 user=obj.user,
#                 counseling=obj.counseling_user,
#                 enquiry_comment=obj.enquiry_data,
#                 child=obj.child_data,
#                 )
#             res = [
#                 {"counselor": c_obj.counseling.user.user_ptr.name, "data": c_obj.comment, "timestamp": c_obj.timestamp}
#                 for c_obj in comment_obj]
#             return res
#         elif obj.user and not obj.child_data and obj.enquiry_data:
#             comment_obj = CommentSection.objects.filter(
#                 user=obj.user,
#                 counseling=obj.counseling_user,
#                 enquiry_comment=obj.enquiry_data,
#             )
#             res = [
#                 {"counselor": c_obj.counseling.user.user_ptr.name, "data": c_obj.comment, "timestamp": c_obj.timestamp}
#                 for c_obj in comment_obj]
#             return res
#         elif obj.user and obj.child_data and not obj.enquiry_data:
#             comment_obj = CommentSection.objects.filter(
#                 user=obj.user,
#                 counseling=obj.counseling_user,
#                 child=obj.child_data,
#             )
#             res = [{"counselor": c_obj.counseling.user.user_ptr.name, "data": c_obj.comment, "timestamp": c_obj.timestamp} for c_obj in comment_obj]
#             return res
#
#     def save(self, validated_data, user):
#
#         user_id = validated_data.get("user")
#         child_id = validated_data.get("child_data")
#
#         if validated_data['enquiry_data']['id']:
#             enq_data = validated_data['enquiry_data']['id']
#
#             enquiry_data = SchoolEnquiry.objects.filter(id=enq_data).first()
#
#         else:
#             enquiry_data = None
#         try:
#             if user_id and enquiry_data:
#                 counseling_obj, _ = CounselingAction.objects.get_or_create(
#                     user=User.objects.get(id=validated_data['user']),
#                     counseling_user=CounselorCAdminUser.objects.get(user__user_ptr_id=user.id),
#                     child_data=Child.objects.filter(id=child_id).first() or None,
#                     enquiry_data=enquiry_data
#                 )
#             elif user_id and not enquiry_data:
#                 counseling_obj, _ = CounselingAction.objects.get_or_create(
#                     user=User.objects.get(id=validated_data['user']),
#                     counseling_user=CounselorCAdminUser.objects.get(user__user_ptr_id=user.id),
#                     child_data=Child.objects.filter(id=child_id).first() or None,
#                 )
#             elif not user_id and enquiry_data:
#                 if CounselingAction.objects.filter(enquiry_data=enquiry_data).exists():
#
#                     counseling_obj = CounselingAction.objects.get(enquiry_data=enquiry_data)
#                 else:
#
#                     counseling_obj= CounselingAction.objects.create(
#                         counseling_user=CounselorCAdminUser.objects.get(user__user_ptr_id=user.id),
#                         enquiry_data=enquiry_data
#                     )
#         except Exception as e:
#             logger.info(e)
#             return None, e
#         enquiry_action = ActionSection.objects.filter(id=validated_data.get('enquiry_action')).first()
#         if enquiry_action:
#             counseling_obj.enquiry_action = enquiry_action
#
#         child_action = ActionSection.objects.filter(
#             id=validated_data.get('child_action')).first()
#         if user_id and child_action:
#             counseling_obj.child_action = child_action
#             counseling_obj.child_scheduled_time = validated_data.get('child_scheduled_time')
#         counseling_obj.enquiry_scheduled_time = validated_data.get('enquiry_scheduled_time') or None
#
#         counseling_obj.save()
#         if counseling_obj.user:
#             if counseling_obj.child_data and counseling_obj.enquiry_data:
#                 counselor_comment = CommentSection.objects.create(
#                     user=counseling_obj.user,
#                     counseling=counseling_obj.counseling_user,
#                     child=counseling_obj.child_data,
#                     enquiry_comment=counseling_obj.enquiry_data
#                 )
#                 counselor_comment.comment = validated_data.get('comment')
#                 counselor_comment.save()
#             elif counseling_obj.child_data and not counseling_obj.enquiry_data:
#                 counselor_comment = CommentSection.objects.create(
#                     user=counseling_obj.user,
#                     counseling=counseling_obj.counseling_user,
#                     child=counseling_obj.child_data,
#                 )
#                 counselor_comment.comment = validated_data.get('comment')
#                 counselor_comment.save()
#             elif not counseling_obj.child_data and counseling_obj.enquiry_data:
#                 counselor_comment = CommentSection.objects.create(
#                     user=counseling_obj.user,
#                     counseling=counseling_obj.counseling_user,
#                     enquiry_comment=counseling_obj.enquiry_data
#                 )
#                 counselor_comment.comment = validated_data.get('comment')
#                 counselor_comment.save()
#         elif not counseling_obj.user:
#             if CounselingAction.objects.filter(enquiry_data=enquiry_data).exists():
#                 counseling_obj = CounselingAction.objects.filter(enquiry_data__email=enquiry_data.email).first()
#                 counselor_comment = CommentSection.objects.create(
#                     counseling=counseling_obj.counseling_user,
#                     enquiry_comment=counseling_obj.enquiry_data
#                 )
#                 counselor_comment.comment = validated_data.get('comment')
#                 counselor_comment.save()
#         return counseling_obj.id, None


class CAdminuserProfileSerializer(serializers.ModelSerializer):
    user_ptr = UserSerializer()

    class Meta:
        model = CAdminUser
        fields = [
            "id",
            "user_ptr",
            "is_admin",
            "is_executive",
            "user_type",
            "phone_no",
            "designation",
        ]
        read_only_fields = ["id", "user_ptr"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "slug",
        ]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "slug",
        ]


class PincodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pincode
        fields = [
            "id",
            "pincode",
            "type"
        ]


class DistrictRegionSerializer(serializers.ModelSerializer):
    pincode = PincodeSerializer(many=True)
    class Meta:
        model = DistrictRegion
        fields = [
            "id",
            "name",
            "slug",
            "pincode"
        ]
    def to_representation(self, instance):
        response = super().to_representation(instance)
        region = DistrictRegion.objects.get(id=instance.id)
        response["name"] = instance.name + ' (' + region.district.name + ')'
        return response


class StatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = [
            "id",
            "name",
            "slug",
        ]


class SalesCAdminuserProfileSerializer(serializers.ModelSerializer):
    user = CAdminuserProfileSerializer()
    city = CitySerializer()
    district = DistrictSerializer()
    district_region = DistrictRegionSerializer()
    state = StatesSerializer()

    class Meta:
        model = SalesCAdminUser
        fields = [
            "id",
            "user",
            "city",
            "district",
            "district_region",
            "state",
        ]


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
        ]


class CAdminuserInfoSerializer(serializers.ModelSerializer):
    user_ptr = UserInfoSerializer()

    class Meta:
        model = CAdminUser
        fields = ["designation", "phone_no", "user_ptr"]


class SalesExecutiveListSerializer(serializers.ModelSerializer):
    user = CAdminuserInfoSerializer()
    city = CitySerializer()

    class Meta:
        model = SalesCAdminUser
        fields = ["id", "user", "city"]


class SchoolDetailSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    district_region = DistrictRegionSerializer()

    class Meta:
        model = SchoolProfile
        fields = ["id", "name", "slug", "district", "district_region"]


class SalesExecutiveDetailSerializer(serializers.ModelSerializer):
    user = CAdminuserInfoSerializer()
    city = CitySerializer()
    district = DistrictSerializer()
    district_region = DistrictRegionSerializer()
    state = StatesSerializer()
    assigned_schools = SchoolDetailSerializer(many=True)

    class Meta:
        model = SalesCAdminUser
        fields = ["id", "user", "city", "state", "district", "district_region", "assigned_schools"]


""" Counselor Custom Admin serializer """


class DistrictRegionSerializerforCA(serializers.ModelSerializer):
    class Meta:
        model = DistrictRegion
        fields = [
            "id",
            "name",
            "slug"
        ]


class CounselorCAdminUserProfileSerializer(serializers.ModelSerializer):
    user = CAdminuserProfileSerializer()
    city = CitySerializer()
    district = DistrictSerializer()
    district_region = DistrictRegionSerializerforCA()
    # status = serializers.SerializerMethodField()

    class Meta:
        model = CounselorCAdminUser

        fields = [
            "id",
            "user",
            "city",
            "district",
            "district_region",
            'online_schools',
            'boarding_schools',
            'unassigned_call_data_permission',
            # 'status'
        ]
    # def get_status(self, instance):
    #     return instance.profile_views.count()
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["city"] = CitySerializer(instance.city.all(), many=True).data
        rep["district"] = DistrictSerializer(instance.district.all(), many=True).data
        rep["district_region"] = DistrictRegionSerializerforCA(instance.district_region.all(), many=True).data
        return rep


class CounselorExecutiveDetailSerializer(serializers.ModelSerializer):
    user = CAdminuserProfileSerializer()
    class Meta:
        model = CounselorCAdminUser
        fields = ["id", "user", "city", "district", "district_region"]

class CounselorExecutiveListSerializer(serializers.ModelSerializer):
    user = CAdminuserInfoSerializer()
    city = CitySerializer(many=True)
    district = DistrictSerializer(many=True)
    district_region = DistrictRegionSerializer(many=True)

    class Meta:
        model = CounselorCAdminUser
        fields = ["id", "user", "city", "district", "district_region"]

class DatabaseCAdminUserProfileSerializer(serializers.ModelSerializer):
    user = CAdminuserProfileSerializer()

    class Meta:
        model = DatabaseCAdminUser
        fields = ["id", "user", "delete_permission", "edit_permission"]
