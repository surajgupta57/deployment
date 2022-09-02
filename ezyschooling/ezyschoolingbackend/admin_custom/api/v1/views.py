from dateutil.relativedelta import relativedelta
from django.db.transaction import atomic
from rest_framework.generics import ListAPIView

from admin_custom.models import CAdminUser, SalesCAdminUser, UserType, CounselorCAdminUser, CommentSection, ActionSection, DatabaseCAdminUser, ViewedParentPhoneNumberBySchool, LeadGenerated, VisitScheduleData, SchoolPerformedActionOnEnquiry

from admin_custom.models import CAdminUser, SalesCAdminUser, UserType, CounselingAction
from admin_custom.filters import *
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from admission_forms.api.v1.serializers import ChildSchoolCartSerializer
from admin_custom.permissions import IsExecutiveUser,IsAdminUser, IsDatabaseAdminUser, SchoolCounsellingDataPermission
from schools.models import *
from accounts.models import *
from admission_forms.models import SchoolApplication, ApplicationStatus, ApplicationStatusLog, FormReceipt, ChildSchoolCart, SchoolApplication
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from . import serializers
from django.core.exceptions import ObjectDoesNotExist
from backend.logger import info_logger, error_logger
from allauth.account import app_settings as allauth_settings
from accounts.api.v1.serializers import TokenSerializer, UserSerializer
from rest_auth.registration.views import RegisterView
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime
from celery.utils.log import get_task_logger
from rest_framework.filters import SearchFilter
from admin_custom.api.v2.serializers import SchoolProfileInsideSerializer

from .serializers import (
    CounselingSchoolApplicationSerializer,
    CounselingSchoolEnquirySerializer,
    CounselingChildSchoolCartSerializer,
    CounselingChildDataSerializer,
    ActionSectionSerializer,
    CitySerializer,
    DistrictRegionSerializer,
    DistrictSerializer,
)

logger = get_task_logger(__name__)


def validateEmail(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


class CAdminuserProfileView(APIView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            try:
                cadmin_user = CAdminUser.objects.get(user_ptr__id=self.request.user.id)

                if SalesCAdminUser.objects.filter(user=cadmin_user).exists():
                    sales_admin = SalesCAdminUser.objects.get(user=cadmin_user)
                    serializer = serializers.SalesCAdminuserProfileSerializer(sales_admin)
                    return Response(serializer.data)
                elif CounselorCAdminUser.objects.filter(user=cadmin_user).exists():
                    Counselor_admin = CounselorCAdminUser.objects.get(user=cadmin_user)
                    serializer = serializers.CounselorCAdminUserProfileSerializer(Counselor_admin)
                    return Response(serializer.data)
                elif DatabaseCAdminUser.objects.filter(user=cadmin_user).exists():
                    db_admin = DatabaseCAdminUser.objects.get(user=cadmin_user)
                    serializer = serializers.DatabaseCAdminUserProfileSerializer(db_admin)
                    return Response(serializer.data)

                # serializer = serializers.CAdminuserProfileSerializer(cadmin_user)
                # return Response(serializer.data)
            except ObjectDoesNotExist:
                error_logger(
                    f"{self.__class__.__name__} ProfileData for given id doesn't exist id {self.request.user.id}"
                )
                return Response(status=status.HTTP_404_NOT_FOUND)
        error_logger(f"{self.__class__.__name__} FORBIDDEN 403")
        return Response(status=status.HTTP_403_FORBIDDEN)


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def get_schools(c_admin_user):
    schools = ""
    if c_admin_user.is_admin:
        schools = SchoolProfile.objects.all().select_related(
            "user", "school_city", "district_region", "district", "pincode"
        )
    else:
        sales_exec = ""
        if SalesCAdminUser.objects.filter(user=c_admin_user).exists():
            sales_exec = SalesCAdminUser.objects.select_related(
                "user", "city", "state", "district_region", "district"
            ).get(user=c_admin_user)

            if sales_exec.district_region:
                schools = SchoolProfile.objects.filter(
                    school_city=sales_exec.city,
                    school_state=sales_exec.state,
                    district_region=sales_exec.district_region,
                    district=sales_exec.district,
                ).select_related(
                    "user", "school_city", "district_region", "district", "pincode"
                )
            elif sales_exec.district:
                schools = SchoolProfile.objects.filter(
                    school_city=sales_exec.city,
                    school_state=sales_exec.state,
                    district=sales_exec.district,
                ).select_related(
                    "user", "school_city", "district_region", "district", "pincode"
                )
            else:
                schools = SchoolProfile.objects.filter(
                    school_city=sales_exec.city, school_state=sales_exec.state
                ).select_related(
                    "user", "school_city", "district_region", "district", "pincode"
                )
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    return schools


class SchoolDetailCardView(APIView):
    def get(self, request, id):
        c_admin_user = ""
        if CAdminUser.objects.filter(id=id).exists():
            c_admin_user = CAdminUser.objects.select_related(
                "user_type", "user_ptr"
            ).get(id=id)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        schools = get_schools(c_admin_user)
        if schools:
            schools = schools.order_by("-views")[:10]
            result = {}
            result["results"] = []
            for school in schools:
                data = {}
                data["logo_url"] = ""
                if school.logo:
                    data["logo_url"] = str(school.logo.url)
                data["name"] = school.name
                data["id"] = school.id
                data["slug"] = school.slug
                data["short_address"] = school.short_address
                data["pincode"] = ""
                data["city"] = ""
                data["district"] = ""
                data["district_region"] = ""
                if school.pincode:
                    data["pincode"] = school.pincode.pincode
                if school.school_city:
                    data["city"] = school.school_city.name
                if school.district:
                    data["district"] = school.district.name
                if school.district_region:
                    data["district_region"] = school.district_region.name
                data["mail"] = school.email
                data["website"] = school.website
                data["phone"] = school.phone_no
                data["poc_name"] = school.user.name
                data["poc_email"] = school.user.email
                result["results"].append(data)
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class DashboardInfoView(APIView):
    def get(self, request, id):
        c_admin_user = ""
        if CAdminUser.objects.filter(id=id).exists():
            c_admin_user = CAdminUser.objects.select_related(
                "user_type", "user_ptr"
            ).get(id=id)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        schools = get_schools(c_admin_user)
        if schools:
            result = {}
            collab = 0
            for school in schools:
                if school.collab:
                    collab = collab + 1
            result["results"] = {}
            result["results"]["total_schools"] = str(len(schools))
            result["results"]["total_collab_schools"] = str(collab)
            result["results"]["total_non_collab_schools"] = str(len(schools) - collab)
            areas = 0
            if c_admin_user.is_admin:
                areas = len(States.objects.all())
            else:
                sales_exec = ""
                if SalesCAdminUser.objects.filter(user=c_admin_user).exists():
                    sales_exec = SalesCAdminUser.objects.select_related(
                        "user", "city", "state", "district_region", "district"
                    ).get(user=c_admin_user)
                    if sales_exec.district:
                        if not sales_exec.district_region:
                            areas = DistrictRegion.objects.filter(
                                district=sales_exec.district
                            ).count()
                    else:
                        if not sales_exec.district_region:
                            areas = District.objects.filter(
                                city=sales_exec.city
                            ).count()
                else:
                    result = {}
                    result["results"] = "no data found"
                    return Response(result, status=status.HTTP_404_NOT_FOUND)

            result["results"]["total_areas"] = areas
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class MostVisitedSchoolsView(APIView):
    def get(self, request, id):
        c_admin_user = ""
        if CAdminUser.objects.filter(id=id).exists():
            c_admin_user = CAdminUser.objects.select_related(
                "user_type", "user_ptr"
            ).get(id=id)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        schools = get_schools(c_admin_user)
        if schools:
            schools = schools.order_by("-views")[:10]
            result = {}
            result["results"] = []
            for school in schools:
                data = {}
                data["name"] = school.name
                data["id"] = school.id
                data["collab"] = school.collab
                data["views"] = school.views
                data["applications"] = SchoolApplication.objects.filter(
                    school=school
                ).count()
                result["results"].append(data)
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class SchoolReportTableView(APIView):
    pagination_class = LargeResultsSetPagination

    # pagination_class = settings.DEFAULT_PAGINATION_CLASS
    def get(self, request, id):
        # paginator = PageNumberPagination()
        c_admin_user = ""
        if CAdminUser.objects.filter(id=id).exists():
            c_admin_user = CAdminUser.objects.select_related(
                "user_type", "user_ptr"
            ).get(id=id)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        schools = get_schools(c_admin_user)
        if schools:
            result = {}
            result["results"] = []
            for school in schools:
                data = {}
                data["logo_url"] = ""
                if school.logo:
                    data["logo_url"] = str(school.logo.url)
                data["name"] = school.name
                data["id"] = school.id
                data["short_address"] = school.short_address
                data["pincode"] = ""
                data["city"] = ""
                data["district"] = ""
                data["district_region"] = ""
                if school.pincode:
                    data["pincode"] = school.pincode.pincode
                if school.school_city:
                    data["city"] = school.school_city.name
                if school.district:
                    data["district"] = school.district.name
                if school.district_region:
                    data["district_region"] = school.district_region.name
                data["collab"] = school.collab
                data["views"] = school.views
                result["results"].append(data)
            # return self.paginator.get_paginated_response(result)
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class
        return self._paginator

    # def get_paginated_response(self, data):
    #     """
    #     Return a paginated style `Response` object for the given output data.
    #     """
    #     assert self.paginator is not None
    #     return self.paginator.get_paginated_response(data)


class SchoolDetailView(APIView):
    pagination_class = LargeResultsSetPagination

    def get(self, request, id):
        collab = request.query_params.get("collab", "")
        city = request.query_params.get("city", "")
        district_region = request.query_params.get("district_region", "")
        district = request.query_params.get("district", "")
        c_admin_user = ""
        if CAdminUser.objects.filter(id=id).exists():
            c_admin_user = CAdminUser.objects.select_related(
                "user_type", "user_ptr"
            ).get(id=id)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        schools = get_schools(c_admin_user)
        if schools:
            if collab:
                #
                if collab == "True":
                    schools = schools.filter(collab=True)
                else:
                    schools = schools.filter(collab=False)
            if city:
                city_obj = City.objects.get(id=city)
                schools = schools.filter(school_city=city_obj)
                #
            if district:
                district_obj = District.objects.get(id=district)
                schools = schools.filter(district=district_obj)
                #
            if district_region:
                district_region_obj = DistrictRegion.objects.get(id=district_region)
                schools = schools.filter(district_region=district_region_obj)
                #
            # schools=schools[:10]
            result = {}
            result["results"] = []
            for school in schools:
                data = {}
                generic_user = User.objects.get(id=38741)
                if school.user.id != 38741:
                    # data["user_last_login"]=datetime.strftime(school.user.last_login,"%d/%m/%Y %H:%M:%S")
                    data["user_last_login"] = school.user.last_login
                else:
                    data["user_last_login"] = "Not found"
                data["logo_url"] = ""
                if school.logo:
                    data["logo_url"] = str(school.logo.url)
                data["name"] = school.name
                data["id"] = school.id
                data["slug"] = school.slug
                data["short_address"] = school.short_address
                data["pincode"] = ""
                data["city"] = ""
                data["district"] = ""
                data["district_region"] = ""
                if school.pincode:
                    data["pincode"] = school.pincode.pincode
                if school.school_city:
                    data["city"] = school.school_city.name
                    data["city_id"] = school.school_city.id
                if school.district:
                    data["district"] = school.district.name
                    data["district_id"] = school.district.id
                if school.district_region:
                    data["district_region"] = school.district_region.name
                    data["district_region_id"] = school.district_region.id
                data["mail"] = school.email
                data["website"] = school.website
                data["phone"] = school.phone_no
                data["poc_name"] = school.user.name
                data["poc_email"] = school.user.email
                data["views"] = school.views
                data["collab"] = school.collab
                data["notifications"] = SchoolClassNotification.objects.filter(
                    school=school
                ).count()
                data["enquiries"] = SchoolEnquiry.objects.filter(school=school).count()
                data["applications"] = SchoolApplication.objects.filter(
                    school=school
                ).count()
                result["results"].append(data)
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


# class SchoolProfileFilter(APIView):
#     def get(self,request):
#         collab=request.query_params.get('collab', '')
#         city=request.            "is_expert": self.request.user.is_expert,
# est.query_params.get('district', '')
#         district_region=request.query_params.get('district_region', '')
#


class SchoolProfileFilterView(generics.ListAPIView):
    serializer_class = serializers.SchoolProfileSerializer
    queryset = SchoolProfile.objects.all()
    pagination_class = LargeResultsSetPagination
    # filterset_fields = ['collab', 'district_region', 'district', 'school_city', 'school_state']
    filterset_class = SchoolProfileFilter


class AddSalesExecutive(APIView):
    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        designation = request.data.get("designation")
        state = request.data.get("state")
        city = request.data.get("city")
        password = request.data.get("password")
        district = request.data.get("district")
        district_region = request.data.get("district_region")
        new_user = ""
        if not validateEmail(email):
            result = {}
            result["results"] = "Invalid email address"
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            new_user = User.objects.get(email=email)
            if CAdminUser.objects.filter(user_ptr=new_user).exists():
                result = {}
                result["results"] = "CAdmin User for the user already exist:"
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        else:
            new_user = User.objects.create(name=name, email=email, username=email)
            new_user.set_password(password)
            new_user.save()
        city_obj = ""
        if City.objects.filter(id=city).exists():
            city_obj = City.objects.get(id=city)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        state_obj = ""
        if States.objects.filter(id=state).exists():
            state_obj = States.objects.get(id=state)
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        district_obj = ""
        district_region_obj = ""
        if district_region:
            if DistrictRegion.objects.filter(id=district_region).exists():
                district_region_obj = DistrictRegion.objects.get(id=district_region)
            else:
                result = {}
                result["results"] = "no data found"
                return Response(result, status=status.HTTP_404_NOT_FOUND)
        if district:
            if District.objects.filter(id=district).exists():
                district_obj = District.objects.get(id=district)
            else:
                result = {}
                result["results"] = "no data found"
                return Response(result, status=status.HTTP_404_NOT_FOUND)
        type = ""
        if UserType.objects.filter(category_name="Sales").exists():
            type = UserType.objects.get(category_name="Sales")
        else:
            result = {}
            result["results"] = "no data found"
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        c_admin_user = CAdminUser.objects.create(
            user_ptr=new_user,
            phone_no=phone,
            designation=designation,
            is_executive=True,
            user_type=type,
        )
        if district_obj and district_region_obj:
            sales_user = SalesCAdminUser.objects.create(
                user=c_admin_user,
                city=city_obj,
                state=state_obj,
                district=district_obj,
                district_region=district_region_obj,
            )
        elif district_region_obj:
            sales_user = SalesCAdminUser.objects.create(
                user=c_admin_user,
                city=city_obj,
                state=state_obj,
                district_region=district_region_obj,
            )
        elif district_obj:
            sales_user = SalesCAdminUser.objects.create(
                user=c_admin_user, city=city_obj, state=state_obj, district=district_obj
            )
        else:
            sales_user = SalesCAdminUser.objects.create(
                user=c_admin_user, city=city_obj, state=state_obj
            )
        result = {}
        result["results"] = "CAdmin User Successfully created for id: " + str(
            c_admin_user.id
        )
        return Response(result, status=status.HTTP_200_OK)


class SalesExecutiveListView(generics.ListAPIView):
    queryset = SalesCAdminUser.objects.filter(user__is_executive=True).select_related(
        "city", "district", "district_region", "user", "user__user_ptr"
    )
    serializer_class = serializers.SalesExecutiveListSerializer


class SalesExecutiveDetailView(APIView):
    def get(self, request, id):
        result = {}
        if SalesCAdminUser.objects.filter(id=id).exists():
            queryset = (
                SalesCAdminUser.objects.prefetch_related("assigned_schools")
                .select_related(
                    "city", "district", "district_region", "user", "user__user_ptr"
                )
                .get(id=id)
            )
            serializer = serializers.SalesExecutiveDetailSerializer(queryset)
            result["results"] = serializer.data
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["results"] = "Sales User Not Found with the given id"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class SchoolDetailedView(APIView):
    def get(self, request, id):
        result = {}
        if SchoolProfile.objects.filter(id=id).exists():
            school = SchoolProfile.objects.select_related(
                "user", "school_city", "district_region", "district", "pincode"
            ).get(id=id)
            data = {}
            generic_user = User.objects.get(id=38741)
            if school.user.id != 38741:
                data["user_last_login"] = school.user.last_login
            else:
                data["user_last_login"] = "Not found"
            data["logo_url"] = ""
            if school.logo:
                data["logo_url"] = str(school.logo.url)
            data["name"] = school.name
            data["id"] = school.id
            data["slug"] = school.slug
            data["short_address"] = school.short_address
            data["pincode"] = ""
            data["city"] = ""
            data["district"] = ""
            data["district_region"] = ""
            if school.pincode:
                data["pincode"] = school.pincode.pincode
            if school.school_city:
                data["city"] = school.school_city.name
                data["city_id"] = school.school_city.id
            if school.district:
                data["district"] = school.district.name
                data["district_id"] = school.district.id
            if school.district_region:
                data["district_region"] = school.district_region.name
                data["district_region_id"] = school.district_region.id
            data["mail"] = school.email
            data["website"] = school.website
            data["phone"] = school.phone_no
            data["poc_name"] = school.user.name
            data["poc_email"] = school.user.email
            data["views"] = school.views
            data["collab"] = school.collab
            data["notifications"] = SchoolClassNotification.objects.filter(
                school=school
            ).count()
            data["enquiries"] = SchoolEnquiry.objects.filter(school=school).count()
            data["applications"] = SchoolApplication.objects.filter(
                school=school
            ).count()
            result["results"] = data
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["results"] = "School Profile Not Found with the given id"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class AssignSchoolsView(APIView):
    def put(self, request, id):
        result = {}
        if SalesCAdminUser.objects.filter(id=id).exists():
            sales_user = SalesCAdminUser.objects.get(id=id)
            school_list = request.data["school_id"]
            for school_id in school_list:
                if SchoolProfile.objects.filter(id=school_id).exists():
                    school = SchoolProfile.objects.get(id=school_id)
                    sales_user.assigned_schools.add(school)
            sales_user.save()
            result["results"] = "Schools Assigned Successfully for Sales User"
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["results"] = "Sales User Not Found with the given id"
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, id):
        result = {}
        if SalesCAdminUser.objects.filter(id=id).exists():
            sales_user = SalesCAdminUser.objects.get(id=id)
            school_list = sales_user.assigned_schools.all().select_related(
                "user", "school_city", "district_region", "district", "pincode"
            )
            result["results"] = []
            for school in school_list:
                data = {}
                generic_user = User.objects.get(id=38741)
                if school.user.id != 38741:
                    # data["user_last_login"]=datetime.strftime(school.user.last_login,"%d/%m/%Y %H:%M:%S")
                    data["user_last_login"] = school.user.last_login
                else:
                    data["user_last_login"] = "Not found"
                data["logo_url"] = ""
                if school.logo:
                    data["logo_url"] = str(school.logo.url)
                data["name"] = school.name
                data["id"] = school.id
                data["slug"] = school.slug
                data["short_address"] = school.short_address
                data["pincode"] = ""
                data["city"] = ""
                data["district"] = ""
                data["district_region"] = ""
                if school.pincode:
                    data["pincode"] = school.pincode.pincode
                if school.school_city:
                    data["city"] = school.school_city.name
                    data["city_id"] = school.school_city.id
                if school.district:
                    data["district"] = school.district.name
                    data["district_id"] = school.district.id
                if school.district_region:
                    data["district_region"] = school.district_region.name
                    data["district_region_id"] = school.district_region.id
                data["mail"] = school.email
                data["website"] = school.website
                data["phone"] = school.phone_no
                data["poc_name"] = school.user.name
                data["poc_email"] = school.user.email
                data["views"] = school.views
                data["collab"] = school.collab
                data["notifications"] = SchoolClassNotification.objects.filter(
                    school=school
                ).count()
                data["enquiries"] = SchoolEnquiry.objects.filter(school=school).count()
                data["applications"] = SchoolApplication.objects.filter(
                    school=school
                ).count()
                result["results"].append(data)
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["results"] = "Sales User Not Found with the given id"
            return Response(result, status=status.HTTP_404_NOT_FOUND)


class SearchSchoolView(APIView):
    def get(self, request):
        name = request.query_params.get("school_name", "")
        sales_id = request.query_params.get("sales_id", "")
        # schools=SchoolProfile.objects.filter(name__istartswith=name)
        sales_user = SalesCAdminUser.objects.get(id=sales_id)
        schools = SchoolProfile.objects.filter(name__icontains=name).select_related(
            "user", "school_city", "district_region", "district", "pincode"
        )
        if sales_user.district_region:
            schools = schools.exclude(district_region=sales_user.district_region)
        elif sales_user.district:
            schools = schools.exclude(district=sales_user.district)
        else:
            schools = schools.exclude(school_city=sales_user.city)
        for school in sales_user.assigned_schools.all():
            schools = schools.exclude(id=school.id)
        serializer = serializers.SchoolDetailSerializer(schools, many=True)
        result = {}
        result["results"] = serializer.data
        return Response(result, status=status.HTTP_200_OK)


class CounselorExecutiveView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        result = {}
        try:
            id = request.query_params["id"]
            if id != None:
                if CounselorCAdminUser.objects.filter(id=id).exists():
                    queryset = CounselorCAdminUser.objects.get(id=id)
                    serializer = serializers.CounselorCAdminUserProfileSerializer(queryset)
                    result["results"] = serializer.data
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    result["results"] = " User Not found"
                    return Response(result, status=status.HTTP_200_OK)
            else:
                result["results"] = "Id can not be none"
                return Response(result, status=status.HTTP_200_OK)
        except:
            result["results"] = "Please provide the id"
            return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        designation = request.data.get("designation")
        cities = request.data.get("city")
        password = request.data.get("password")
        districts = request.data.get("district")
        district_region = request.data.get("district_region")
        online_schools = request.data.get("online_schools")
        boarding_schools = request.data.get("boarding_schools")
        unassigned_call_data_permission = request.data.get("unassigned_call_data_permission")
        if not validateEmail(email):
            return Response({"results": "Invalid email address"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            new_user = User.objects.get(email=email)
            if CAdminUser.objects.filter(user_ptr=new_user).exists():
                return Response({"results": "CAdmin User for the user already exist."},status=status.HTTP_400_BAD_REQUEST,)
        else:
            new_user = User.objects.create(name=name, email=email, username=email)
            new_user.set_password(password)
            new_user.save()
        type = ""
        if UserType.objects.filter(id=2).exists():
            type = UserType.objects.get(id=2)
        else:
            return Response({"results": "no data found"}, status=status.HTTP_404_NOT_FOUND)
        c_admin_user = CAdminUser.objects.create(user_ptr=new_user,phone_no=phone,designation=designation,
                is_executive=True,user_type=type)

        Counselor_user = CounselorCAdminUser.objects.create(user=c_admin_user,online_schools=online_schools,
                        boarding_schools=boarding_schools,unassigned_call_data_permission=unassigned_call_data_permission)
        city_id = []
        if cities:
            city_id = cities[0]
            city_obj = City.objects.get(id=city_id)
            Counselor_user.city.add(city_obj)
            Counselor_user.save()
        else:
            return Response({"message": "no data found ! Atleast select one city"}, status=status.HTTP_400_BAD_REQUEST,)
        # district updatation
        if districts:
            district_id =districts[0]
            if isinstance(district_id, int):
                dist_obj = District.objects.get(id=district_id)
                Counselor_user.district.add(dist_obj)
                Counselor_user.save()

        if district_region:
            district_region_id = district_region[0]
            if isinstance(district_region_id, int):
                region_obj = DistrictRegion.objects.get(id=district_region_id)
                Counselor_user.district_region.add(region_obj)
                Counselor_user.save()
        return Response({"message": "CAdmin User Successfully created"},status=status.HTTP_200_OK,)

    def patch(self, request, *agrs, **kwargs):
        try:
            id = request.query_params['id']
            type = request.query_params["type"]
            if not type:
                return Response({"result": "Provide Action Type"}, status=status.HTTP_400_BAD_REQUEST)
            if id and CounselorCAdminUser.objects.filter(id=id).exists():
                counselor_obj = CounselorCAdminUser.objects.get(id=id)
                if type=='add_cities':
                    cities = request.data.get("city")
                    if cities:
                        city_id = []
                        for city in cities:
                            val = int(city)
                            city_id.append(val)
                        for i in city_id:
                            counselor_obj.city.add(City.objects.get(id=i))
                    return Response({"result": "City(s) Added"}, status=status.HTTP_200_OK)
                elif type=='remove_cities':
                    cities = request.data.get("city")
                    if cities:
                        city_id = []
                        for city in cities:
                            val = int(city)
                            city_id.append(val)
                        for i in city_id:
                            counselor_obj.city.remove(City.objects.get(id=i))
                    return Response({"result": "City(s) Removed"}, status=status.HTTP_200_OK)
                elif type=='add_districts':
                    districts = request.data.get("district")
                    if districts:
                        district_id = []
                        for district in districts:
                            val = int(district)
                            district_id.append(val)
                        for i in district_id:
                            counselor_obj.district.add(District.objects.get(id=i))
                    return Response({"result": "District(s) Added"}, status=status.HTTP_200_OK)
                elif type=='remove_districts':
                    districts = request.data.get("district")
                    if districts:
                        district_id = []
                        for district in districts:
                            val = int(district)
                            district_id.append(val)
                        for i in district_id:
                            counselor_obj.district.remove(District.objects.get(id=i))
                    return Response({"result": "District(s) Removed"}, status=status.HTTP_200_OK)
                elif type=='add_district_regions':
                    district_region = request.data.get("district_region")
                    if district_region:
                        district_region_id=[]
                        for district_reg in district_region:
                            val = int(district_reg)
                            district_region_id.append(val)
                        for i in district_region_id:
                            counselor_obj.district_region.add(DistrictRegion.objects.get(id=i))
                    return Response({"result": "District Region(s) Added"}, status=status.HTTP_200_OK)
                elif type=='remove_district_regions':
                    district_region = request.data.get("district_region")
                    if district_region:
                        district_region_id=[]
                        for district_reg in district_region:
                            val = int(district_reg)
                            district_region_id.append(val)
                        for i in district_region_id:
                            counselor_obj.district_region.remove(DistrictRegion.objects.get(id=i))
                    return Response({"result": "District Region(s) Removed"}, status=status.HTTP_200_OK)
                elif type=='update_email':
                    def validate_email_id(email):
                        try:
                            validate_email(email)
                            return True
                        except ValidationError:
                            return False
                    new_email = request.data.get("email")
                    if validate_email_id(new_email):
                        if User.objects.filter(email=new_email).count() == 0:
                            new_email = request.data.get("email")
                            userObj = User.objects.get(id=counselor_obj.user.user_ptr.id)
                            userObj.email = new_email
                            userObj.save()
                            return Response({"result": "Counsellor's Email Updated"}, status=status.HTTP_200_OK)
                        else:
                            return Response({"result": "Email ID already exists"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"result": "Provide Valid Email ID"}, status=status.HTTP_400_BAD_REQUEST)
                elif type=='update_name':
                    name = request.data.get("name")
                    userObj = User.objects.get(id=counselor_obj.user.user_ptr.id)
                    userObj.name = name
                    userObj.save()
                    return Response({"result": "District Region(s) Removed"}, status=status.HTTP_200_OK)
                elif type=='update_password':
                    new_password = request.data.get("password")
                    userObj = User.objects.get(id=counselor_obj.user.user_ptr.id)
                    userObj.set_password(new_password)
                    userObj.save()
                    return Response({"result": "District Region(s) Removed"}, status=status.HTTP_200_OK)
                elif type=='update_online_schools':
                    online_schools = request.data.get("online_schools")
                    counselor_obj.online_schools = online_schools
                    counselor_obj.save()
                    return Response({"result": "Online Schools Updated"}, status=status.HTTP_200_OK)
                elif type=='update_boarding_schools':
                    boarding_schools = request.data.get("boarding_schools")
                    counselor_obj.boarding_schools = boarding_schools
                    counselor_obj.save()
                    return Response({"result": "Boarding Schools Updated"}, status=status.HTTP_200_OK)
                elif type=='update_account_status':
                    account_status = request.data.get("account_status")
                    userObj = User.objects.get(id=counselor_obj.user.user_ptr.id)
                    userObj.is_active = account_status
                    userObj.save()
                    return Response({"result": "Account Status Changed"}, status=status.HTTP_200_OK)
                elif type=='update_designation':
                    designation = request.data.get("designation")
                    userObj = CAdminUser.objects.get(id=counselor_obj.user.id)
                    userObj.designation = designation
                    userObj.save()
                    return Response({"result": "Designation Changed"}, status=status.HTTP_200_OK)
                elif type=='update_phone':
                    phone = request.data.get("phone")
                    userObj = CAdminUser.objects.get(id=counselor_obj.user.id)
                    userObj.phone_no = phone
                    userObj.save()
                    return Response({"result": "Phone Number Changed"}, status=status.HTTP_200_OK)
                elif type=='update_unassigned_call_data_permission':
                    unassigned_call_data_permission = request.data.get("unassigned_call_data_permission")
                    counselor_obj.unassigned_call_data_permission = unassigned_call_data_permission
                    counselor_obj.save()
                    return Response({"result": "Boarding Schools Updated"}, status=status.HTTP_200_OK)
                else:
                    return Response({"result": "Provide Valid Action Type"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"result": "Provide Valid Counsellor ID"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"result": "Something Went Wrong"},status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            id = request.query_params["id"]
            if id:
                counselor_obj = CounselorCAdminUser.objects.get(id=id)
                if counselor_obj:
                    cadmin_user_obj = CAdminUser.objects.get(id=counselor_obj.user.id)
                    if cadmin_user_obj:
                        User_obj = User.objects.get(id=cadmin_user_obj.user_ptr.id)
                        User_obj.delete()
                        cadmin_user_obj.delete()
                        counselor_obj.delete()
                        return Response({"results": "CAdmin User Successfully Deleted"},status=status.HTTP_200_OK)
            else:
                return Response({"results": "Id can not be none"}, status=status.HTTP_200_OK)
        except:
            return Response({"results": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)


class UnknownUsersEnquiryList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self, request, *args, **kwargs):
        res = {}
        enq_id = self.kwargs["id"]
        enq_data = [
            enq for enq in SchoolEnquiry.objects.filter(id=enq_id) if not enq.user
        ]
        usr_enquiry = CounselingSchoolEnquirySerializer(enq_data, many=True)
        res["enquiry"] = usr_enquiry.data
        return Response(res)


class ChildListFromUser(APIView):
    permission_classes = (IsExecutiveUser,)

    def get(self, request, *args, **kwargs):
        res = {}
        user_id = self.kwargs["id"]

        user = User.objects.filter(is_parent=True, id=user_id).first()
        enq_data = [
            enq
            for enq in SchoolEnquiry.objects.select_related("user").filter(user=user)
            if enq.user
        ]

        if Child.objects.filter(user=user).exists():
            children = Child.objects.filter(user=user)
            children_serializer = CounselingChildDataSerializer(children, many=True)
            res["children"] = children_serializer.data
        usr_enquiry = CounselingSchoolEnquirySerializer(enq_data, many=True)
        res["enquiry"] = usr_enquiry.data
        return Response(res)


class UserChildDataForCounselingList(APIView):  # for cart and form data wrt to child
    def get(self, request, *args, **kwargs):
        try:
            res = {}
            user_id = self.kwargs["id"]
            user = User.objects.filter(is_parent=True, id=user_id).first()

            child_id = request.query_params.get("child_id")
            if child_id:
                if Child.objects.filter(user=user, id=child_id).exists():
                    child = Child.objects.get(user=user, id=child_id)
                    if ChildSchoolCart.objects.filter(
                        user=user, child=child.id
                    ).exists():
                        cart = ChildSchoolCart.objects.filter(user=user, child=child.id)
                        cart_items = CounselingChildSchoolCartSerializer(
                            cart, many=True
                        )
                        res["cart_items"] = cart_items.data
                    if SchoolApplication.objects.filter(
                        user=user, child=child.id
                    ).exists():
                        app = SchoolApplication.objects.filter(
                            user=user, child=child.id
                        )
                        applications = CounselingSchoolApplicationSerializer(
                            app, many=True
                        )
                        res["applications"] = applications.data

                    return Response(res)
                else:
                    return Response(
                        data={"message": "Child details Not Found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                if ChildSchoolCart.objects.filter(user=user).exists():
                    cart = ChildSchoolCart.objects.filter(user=user)
                    cart_items = CounselingChildSchoolCartSerializer(cart, many=True)
                    res["cart_items"] = cart_items.data
                if SchoolApplication.objects.filter(user=user).exists():
                    app = SchoolApplication.objects.filter(user=user)
                    applications = CounselingSchoolApplicationSerializer(app, many=True)
                    res["applications"] = applications.data

                return Response(res)
        except:
            return Response(
                data={"message": "User not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# class CommentSectionView(APIView):
#     # permission_classes = (permissions.AllowAny,)
#     # queryset = CommentSection.objects.all()
#     # serializer_class = CommentSectionSerializer
#     # filterset_fields = [
#     #     "enquiry_action",
#     #     "child_action",
#     #     "enquiry_scheduled_time",
#     #     "child_scheduled_time",
#     # ]
#
#     def get(self, request, *args, **kwargs):
#         try:
#             id = self.kwargs["id"]
#
#             if CommentSection.objects.filter(
#                     id=id
#             ).exists():
#                 res = CommentSection.objects.get(
#                     id=id
#                 )
#                 serializer = CommentSectionSerializer(res)
#                 return Response(serializer.data)
#             else:
#                 return Response(
#                     data={"message": "Details not found."},
#                     status=status.HTTP_401_UNAUTHORIZED,
#                 )
#         except:
#             obj = CommentSection.objects.filter().order_by('-timestamp')
#             serializer = CommentSectionSerializer(obj, many=True)
#             return Response(serializer.data)
#
#     def post(self, request, *args, **kwargs):
#         data = self.request.data
#
#         user = request.user
#         serializer = CommentSectionSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.save(validated_data=data, user=user)
#         repository = CommentSection.objects.get(id=result)
#         serializer = CommentSectionSerializer(repository)
#         return Response(serializer.data)
#
#     def put(self, request, *args, **kwargs):
#         data = self.request.data
#         id = self.kwargs["id"]
#         couns_obj = CommentSection.objects.get(id=id)
#         serializer = CommentSectionSerializer(couns_obj, data=data)
#         serializer.is_valid(raise_exception=True)
#         result = serializer.update(instance=couns_obj, validated_data=data)
#         if result:
#             couns_obj = CommentSection.objects.get(id=result)
#             serializer = CommentSectionSerializer(couns_obj)
#             return Response(serializer.data)
#         else:
#             return Response(
#                 data={
#                     "message": "Detail not found."
#                 },
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )
#
#     def delete(self, request, *args, **kwargs):
#         try:
#             id = self.kwargs["id"]
#             obj = CommentSection.objects.get(id=id).delete()
#             return Response(
#                 data={"message": "Comment deleted."},
#             )
#         except:
#             return Response(
#                 data={"message": "Detail Not Found."},
#                 status=status.HTTP_401_UNAUTHORIZED,
#             )



def getUserData(users, city, district, district_region):
    res = []
    for user in users:
        if (
            SchoolEnquiry.objects.filter(user=user).exists()
            or ChildSchoolCart.objects.filter(user=user).exists()
            or SchoolApplication.objects.filter(user=user).exists()
        ):
            if city and district and district_region:
                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]

            elif city and district:
                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if data.school.school_city.id == int(city)
                    and data.school.district.id == int(district)
                    and data.user
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if data.school.school_city.id == int(city)
                    and data.school.district.id == int(district)
                    and data.user
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if data.school.school_city.id == int(city)
                    and data.school.district.id == int(district)
                    and data.user
                ]
            elif district and district_region:

                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (
                        data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (
                        data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (
                        data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
            elif city and district_region:

                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
            elif city:

                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (data.school.school_city.id == int(city) and data.user)
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (data.school.school_city.id == int(city) and data.user)
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (data.school.school_city.id == int(city) and data.user)
                ]
            elif district:

                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (data.school.district.id == int(district) and data.user)
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (data.school.district.id == int(district) and data.user)
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (data.school.district.id == int(district) and data.user)
                ]
            elif district_region:

                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if (
                        data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if (
                        data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if (
                        data.school.district_region.id == int(district_region)
                        and data.user
                    )
                ]
            else:
                enq_user_id = [
                    data.user.id
                    for data in SchoolEnquiry.objects.filter(user=user)
                    if data.user
                ]
                cart = [
                    data.user.id
                    for data in ChildSchoolCart.objects.filter(user=user)
                    if data.user
                ]
                app = [
                    data.user.id
                    for data in SchoolApplication.objects.filter(user=user)
                    if data.user
                ]
            res.append(enq_user_id + cart + app)
    return res


def getUnknownUserData(enquires, city, district, district_region):
    res = []
    for enq in enquires:
        if SchoolEnquiry.objects.filter(id=enq).exists():
            if city and district and district_region:
                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and not data.user
                    )
                ]
            elif city and district:
                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if data.school.school_city.id == int(city)
                    and data.school.district.id == int(district)
                    and not data.user
                ]
            elif district and district_region:

                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (
                        data.school.district.id == int(district)
                        and data.school.district_region.id == int(district_region)
                        and not data.user
                    )
                ]
            elif city and district_region:

                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (
                        data.school.school_city.id == int(city)
                        and data.school.district_region.id == int(district_region)
                        and not data.user
                    )
                ]
            elif city:

                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (data.school.school_city.id == int(city) and not data.user)
                ]
            elif district:

                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (data.school.district.id == int(district) and not data.user)
                ]
            elif district_region:

                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if (
                        data.school.district_region.id == int(district_region)
                        and not data.user
                    )
                ]
            else:
                enq_user_id = [
                    data.id
                    for data in SchoolEnquiry.objects.filter(id=enq)
                    if not data.user
                ]
            res.append(enq_user_id)
    return res


class UserListView(APIView, LimitOffsetPagination):
    permission_classes = (IsExecutiveUser,)

    def get(self, request, *args, **kwargs):
        from_date = request.query_params.get("from_date")  # yyyy-mm-dd
        to_date = request.query_params.get("to_date")  # yyyy-mm-dd
        city = request.query_params.get("city")
        district = request.query_params.get("district")
        district_region = request.query_params.get("district_region")
        if from_date and to_date:

            users = [
                user
                for user in User.objects.filter(is_parent=True).filter(
                    last_login__date__range=[from_date, to_date]
                )
                if user.last_login
            ]
        else:
            users = [
                user for user in User.objects.filter(is_parent=True) if user.last_login
            ]
        results = self.paginate_queryset(users, request, view=self)
        res = getUserData(results, city, district, district_region)
        result = [x for l in res for x in l]
        result = list(set(result))
        user_data = [
            {"id": user.id, "name": user.name}
            for user_id in result
            for user in User.objects.filter(id=user_id)
        ]
        return self.get_paginated_response(user_data)


class UnknownUserListView(APIView, LimitOffsetPagination):
    permission_classes = (IsExecutiveUser,)

    def get(self, request, *args, **kwargs):
        from_date = request.query_params.get("from_date")  # yyyy-mm-dd
        to_date = request.query_params.get("to_date")  # yyyy-mm-dd
        city = request.query_params.get("city")
        district = request.query_params.get("district")
        district_region = request.query_params.get("district_region")
        if from_date and to_date:
            enquires = [
                data.id
                for data in SchoolEnquiry.objects.filter(user__isnull=True).filter(
                    timestamp__date__range=[from_date, to_date]
                )
                if (
                    data.school.school_city.id == int(city)
                    and data.school.district.id == int(district)
                    and data.school.district_region.id == int(district_region)
                    and not data.user
                )
            ]
        else:
            enquires = [
                data.id for data in SchoolEnquiry.objects.filter(user__isnull=True)
            ]

        results = self.paginate_queryset(enquires, request, view=self)
        res = getUnknownUserData(results, city, district, district_region)
        result = [x for l in res for x in l]
        result = list(set(result))
        user_data = [
            {"id": enq.id, "name": enq.parent_name}
            for enq_id in result
            for enq in SchoolEnquiry.objects.filter(id=enq_id)
        ]
        return self.get_paginated_response(user_data)


class ActionSectionView(ListAPIView):  # ?category__name=Child or Enquiry
    permission_classes = (permissions.AllowAny,)
    queryset = ActionSection.objects.all()
    serializer_class = ActionSectionSerializer

    filterset_fields = [
        "category__name",
        "slug",
    ]


class CounselorExecutiveListView(APIView):
    permission_classes = (IsAdminUser,)
    def get(self, request):
        data = []
        all_counsellor = CounselorCAdminUser.objects.exclude(user__is_admin=True)
        for counsellor in all_counsellor:
            cities = None
            for city in counsellor.city.all():
                if cities:
                    cities = cities +', ' + city.name
                else:
                    cities = city.name
            data.append({
            'id':counsellor.id,
            'name':counsellor.user.user_ptr.name,
            'designation':counsellor.user.designation,
            'cities':cities,
            })
        result = {}
        result['results'] = data

        return Response(result,status=status.HTTP_200_OK)

class CACityListView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = City.objects.filter().order_by("-name")
    serializer_class = CitySerializer
    filter_backends = [SearchFilter]
    search_fields = ("name", "slug")
    pagination_class = LimitOffsetPagination


class CADistrictListView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = District.objects.filter().order_by("-name")
    serializer_class = DistrictSerializer
    filter_backends = [SearchFilter]
    search_fields = ("name", "slug")
    pagination_class = LimitOffsetPagination


class CADistrictRegionListView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = DistrictRegion.objects.filter().order_by("-name")
    serializer_class = DistrictRegionSerializer
    filter_backends = [SearchFilter]
    search_fields = ("name", "slug")
    pagination_class = LimitOffsetPagination

class DatabaseInsideSchoolsListView(APIView):
    permission_classes = (IsDatabaseAdminUser,)


    def get(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        no_facilities = request.query_params.get("no_facilities")
        no_fees = request.query_params.get("no_fees")
        admission_open = request.query_params.get("admission_open")
        city = request.query_params.get("city")
        district = request.query_params.get("district")
        district_region = request.query_params.get("district_region")
        is_verified = request.query_params.get("is_verified")
        is_featured = request.query_params.get("is_featured")
        collab = request.query_params.get("collab", None)
        incomplete_data = request.query_params.get("incomplete_data")
        try:
            if id:
                if SchoolProfile.objects.filter(
                        id=id, is_active=True
                ).exists():
                    sch_obj = SchoolProfile.objects.get(
                        id=id, is_active=True
                    )
                    serializer = SchoolProfileInsideSerializer(sch_obj)
                    return Response(serializer.data)
                else:
                    return Response(
                        data={"message": "Details Not Found."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            elif no_fees or no_facilities or admission_open:

                if city or district or district_region:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], \
                                                  AdmissionSession.objects.all().order_by('-id')[:2][0]

                    start_offset = 0
                    end_offset = 10
                    next_url = None
                    prev_url = None
                    offset = int(self.request.GET.get('offset', 10))
                    if offset == 10:
                        new_offset = offset * 2
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&city={city}&district={district}&district_region={district_region}"
                        prev_url = None
                    else:
                        new_next_offset = offset + 10
                        new_prev_offset = offset - 10
                        if new_prev_offset == 0:
                            new_prev_offset = ''
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}"
                        prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}"
                    if city and district and district_region:
                        if no_fees:
                            start_offset = offset - 10
                            end_offset = offset
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"
                            if collab:
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession)).order_by("-id")][start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_featured={is_featured}"
                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession)).order_by("-id")][start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"
                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region).order_by("-id") if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][start_offset:end_offset]
                            else:
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)

                        elif no_facilities:
                            start_offset = offset - 10
                            end_offset = offset
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                                # prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"

                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True,
                                             collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region).order_by("-id") if
                                         not Feature.objects.filter(school=sch_obj)][start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True,
                                             collab=(False if collab.startswith("f") else True))
                                            .filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region).order_by("-id") if
                                         not Feature.objects.filter(school=sch_obj)][start_offset:end_offset]
                                else:
                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True,
                                                                                                    collab=(False if collab.startswith("f") else True)).filter(
                                                                           school_city__id=city, district__id=district,
                                                                           district_region__id=district_region) if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                            else:
                                all_collab_school_no_facilities = []
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                 not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True).filter(
                                                                           school_city__id=city, district__id=district,
                                                                           district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region,is_featured=(False if is_featured.startswith("f") else True)) if
                                                 not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True).filter(
                                                                           school_city__id=city, district__id=district,
                                                                           district_region__id=district_region,is_featured=(False if is_featured.startswith("f") else True)) if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True).filter(
                                                                           school_city__id=city, district__id=district,
                                                                           district_region__id=district_region) if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]

                            if len(all_collab_school_no_facilities) >0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            start_offset = offset - 10
                            end_offset = offset
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"

                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True,collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region).order_by("-id") if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))][start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True,collab=(False if collab.startswith("f") else True))
                                            .filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district, district_region__id=district_region).order_by("-id") if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))][start_offset:end_offset]
                                else:
                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region).order_by("-id") if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][start_offset:end_offset]
                            else:
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_featured={is_featured}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                                    count = len([sch_obj for sch_obj in
                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                     school_city__id=city, district__id=district,
                                                     district_region__id=district_region) if
                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                     Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     school_city__id=city, district__id=district,
                                                                     district_region__id=district_region) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]


                            if len(all_school_admission_open) >0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                    elif city and district and not district_region:
                        start_offset = offset - 10
                        end_offset = offset
                        new_next_offset = offset + 10
                        new_prev_offset = offset - 10
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                        prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                        if no_fees:
                            start_offset = offset - 10
                            end_offset = offset
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"

                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"

                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             school_city__id=city, district__id=district) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     school_city__id=city, district__id=district) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city, district__id=district) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 school_city__id=city, district__id=district) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                        elif no_facilities:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(school_city__id=city, district__id=district)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                                else:
                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(school_city__id=city, district__id=district)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city, district__id=district) if
                                     not Feature.objects.filter(school=sch_obj)])
                                all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                   SchoolProfile.objects.filter(is_active=True).filter(
                                                                       school_city__id=city, district__id=district)
                                                                   if
                                                                   not Feature.objects.filter(school=sch_obj)][
                                                                  start_offset:end_offset]

                            if len(all_collab_school_no_facilities) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&addmission_open={admission_open}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city, district__id=district) if
                                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             school_city__id=city, district__id=district) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     school_city__id=city, district__id=district) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city, district__id=district) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 school_city__id=city, district__id=district) if
                                                             AdmmissionOpenClasses.objects.filter(
                                                                 school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]

                            if len(all_school_admission_open) > 0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                    elif city and not district and not district_region:
                        if no_fees:
                            if collab:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(school_city__id=city) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(school_city__id=city) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 school_city__id=city) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                        elif no_facilities:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                                else:
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             school_city__id=city) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True,
                                                                                                    collab=(False if collab.startswith("f") else True)).filter(
                                                                           school_city__id=city)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city) if
                                     not Feature.objects.filter(school=sch_obj)])
                                all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                   SchoolProfile.objects.filter(is_active=True).filter(
                                                                       school_city__id=city)
                                                                   if
                                                                   not Feature.objects.filter(school=sch_obj)][
                                                                  start_offset:end_offset]

                            if len(all_collab_school_no_facilities) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                            .filter(is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)).filter(school_city__id=city) if
                                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             school_city__id=city) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     school_city__id=city) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         school_city__id=city) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 school_city__id=city) if
                                                             AdmmissionOpenClasses.objects.filter(
                                                                 school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]

                            if len(all_school_admission_open) > 0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                    elif not city and district and not district_region:
                        if no_fees:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_fees={no_fees}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         district__id=district) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 district__id=district) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                        elif no_facilities:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                                else:

                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             district__id=district) if
                                         not Feature.objects.filter(school=sch_obj)])
                                    all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                       SchoolProfile.objects.filter(is_active=True,
                                                                                                    collab=(False if collab.startswith("f") else True)).filter(
                                                                           district__id=district)
                                                                       if
                                                                       not Feature.objects.filter(school=sch_obj)][
                                                                      start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&no_facilities={no_facilities}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         district__id=district) if
                                     not Feature.objects.filter(school=sch_obj)])
                                all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                   SchoolProfile.objects.filter(is_active=True).filter(
                                                                       district__id=district)
                                                                   if
                                                                   not Feature.objects.filter(school=sch_obj)][
                                                                  start_offset:end_offset]

                            if len(all_collab_school_no_facilities) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district__id=district) if
                                                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:

                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             district__id=district) if
                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_school_admission_open = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     district__id=district) if
                                                                 AdmmissionOpenClasses.objects.filter(
                                                                     school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"

                                count = len(
                                    [sch_obj for sch_obj in
                                     SchoolProfile.objects.filter(is_active=True).filter(
                                         district__id=district) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True).filter(
                                                                 district__id=district) if
                                                             AdmmissionOpenClasses.objects.filter(
                                                                 school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]

                            if len(all_school_admission_open) > 0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                    elif not city and not district and district_region:
                        if no_fees:
                            if collab:
                                start_offset = offset - 10
                                end_offset = offset
                                new_next_offset = offset + 10
                                new_prev_offset = offset - 10
                                next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}"
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"

                                    count = len(
                                        [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                                             district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True,
                                                                                              collab=(False if collab.startswith("f") else True)).filter(
                                                                     district_region__id=district_region) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(
                                                                         session=nextSession))][
                                                                start_offset:end_offset]
                            else:
                                if is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True).filter(
                                             district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     district_region__id=district_region, is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                if not is_verified and is_featured:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True).filter(
                                             district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     district_region__id=district_region, is_featured=(False if is_featured.startswith("f") else True)) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                                else:
                                    start_offset = offset - 10
                                    end_offset = offset
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&city={city}&district={district}&district_region={district_region}&admission_open={admission_open}"
                                    count = len(
                                        [sch_obj for sch_obj in
                                         SchoolProfile.objects.filter(is_active=True).filter(
                                             district_region__id=district_region) if
                                         not FeeStructure.objects.filter(school=sch_obj).filter(
                                             Q(session=currentSession) | Q(session=nextSession))])
                                    all_collab_school_no_fees = [sch_obj for sch_obj in
                                                                 SchoolProfile.objects.filter(is_active=True).filter(
                                                                     district_region__id=district_region) if
                                                                 not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                     Q(session=currentSession) | Q(session=nextSession))][
                                                                start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                        elif no_facilities:
                            count = len(
                                [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region) if
                                 not Feature.objects.filter(school=sch_obj)])
                            all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                               SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region)
                                                               if
                                                               not Feature.objects.filter(school=sch_obj)][
                                                              start_offset:end_offset]

                            if len(all_collab_school_no_facilities) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            count = len(
                                [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region) if
                                 AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                     Q(session=currentSession) | Q(session=nextSession))])
                            all_school_admission_open = [sch_obj for sch_obj in
                                                         SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(district_region__id=district_region) if
                                                         AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                             Q(session=currentSession) | Q(session=nextSession))][
                                                        start_offset:end_offset]

                            if len(all_school_admission_open) > 0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                    else:
                        if no_fees:
                            if collab:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True)
                                     if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True)
                                                             if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            if len(all_collab_school_no_fees) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                        elif no_facilities:

                            if collab:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                     not Feature.objects.filter(school=sch_obj)])
                                all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                   SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                                                   if
                                                                   not Feature.objects.filter(school=sch_obj)][
                                                                  start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))
                                     if
                                     not Feature.objects.filter(school=sch_obj)])
                                all_collab_school_no_facilities = [sch_obj for sch_obj in
                                                                   SchoolProfile.objects.filter(is_active=True,
                                                                                                collab=(False if collab.startswith("f") else True))
                                                                   if
                                                                   not Feature.objects.filter(school=sch_obj)][
                                                                  start_offset:end_offset]

                            if len(all_collab_school_no_facilities) > 0:
                                serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                                # return Response(serializer.data)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                        elif admission_open:
                            if collab:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]

                            if len(all_school_admission_open) > 0:
                                serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                                result1 = {}
                                result1['count'] = count
                                result1['next'] = next_url
                                result1['previous'] = prev_url
                                result1['results'] = serializer.data
                                return Response(result1, status=status.HTTP_200_OK)
                            else:
                                result1 = {}
                                result1['count'] = 0
                                result1['next'] = ""
                                result1['previous'] = ""
                                result1['results'] = []
                                return Response(result1, status=status.HTTP_200_OK)
                else:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]


                    if no_fees:
                        start_offset = 0
                        end_offset = 10
                        next_url = None
                        prev_url = None
                        offset = int(self.request.GET.get('offset', 10))
                        if offset == 10:
                            new_offset = offset * 2
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}"
                            prev_url = None
                        else:
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            if new_prev_offset == 0:
                                new_prev_offset = ''
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}"
                        if collab:
                            all_collab_school_no_fees = []
                            if is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True), is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True), is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            if not is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}&collab={collab}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}&collab={collab}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}&collab={collab}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}&collab={collab}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}&collab={collab}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True)) if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True)) if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                        else:
                            all_collab_school_no_fees = []
                            if is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}&is_verified={is_verified}&is_featured={is_featured}"

                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True)
                                     if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True)
                                                             if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_fees={no_fees}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_fees={no_fees}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_fees={no_fees}"

                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True)
                                     if
                                     not FeeStructure.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_collab_school_no_fees = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True)
                                                             if
                                                             not FeeStructure.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                        if len(all_collab_school_no_fees) > 0:
                            serializer = SchoolProfileInsideSerializer(all_collab_school_no_fees, many=True)
                            # return Response(serializer.data)
                            result1 = {}
                            result1['count'] = count
                            result1['next'] = next_url
                            result1['previous'] = prev_url
                            result1['results'] = serializer.data
                            return Response(result1, status=status.HTTP_200_OK)
                    elif no_facilities:

                        start_offset = 0
                        end_offset = 10
                        next_url = None
                        prev_url = None
                        offset = int(self.request.GET.get('offset', 10))
                        if offset == 10:
                            new_offset = offset * 2
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}"
                            prev_url = None
                        else:
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            if new_prev_offset == 0:
                                new_prev_offset = ''
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}"
                        if collab:
                            if is_verified and is_featured:

                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"

                                all_collab_school_no_facilities = []
                                for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True),is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True))[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)
                            if not is_verified and is_featured:

                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&collab={collab}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&collab={collab}&is_featured={is_featured}"

                                all_collab_school_no_facilities = []
                                for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True))[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)
                            else:

                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&collab={collab}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&collab={collab}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&collab={collab}"

                                all_collab_school_no_facilities = []
                                for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True))[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)
                        else:
                            all_collab_school_no_facilities = []

                            if is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"

                                for sch_obj in SchoolProfile.objects.filter(is_active=True,is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True))[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)
                            if not is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&is_featured={is_featured}"

                                for sch_obj in SchoolProfile.objects.filter(is_active=True, is_featured=(False if is_featured.startswith("f") else True))[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)
                            else:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&no_facilities={no_facilities}&is_verified={is_verified}&is_featured={is_featured}"

                                for sch_obj in SchoolProfile.objects.filter(is_active=True)[start_offset:end_offset]:
                                    count = 0

                                    if Feature.objects.filter(school=sch_obj).exists():
                                        obj = Feature.objects.filter(school=sch_obj)
                                        for fee_obj in obj:
                                            if fee_obj.exist == "Undefined":
                                                count = count + 1
                                    if count == 40:
                                        all_collab_school_no_facilities.append(sch_obj)

                        if len(all_collab_school_no_facilities) > 0:
                            serializer = SchoolProfileInsideSerializer(all_collab_school_no_facilities, many=True)
                            # return Response(serializer.data)
                            result1 = {}
                            result1['count'] = len(all_collab_school_no_facilities)
                            result1['next'] = next_url
                            result1['previous'] = prev_url
                            result1['results'] = serializer.data
                            return Response(result1, status=status.HTTP_200_OK)
                        else:
                            result1 = {}
                            result1['count'] = 0
                            result1['next'] = ""
                            result1['previous'] = ""
                            result1['results'] = []
                            return Response(result1, status=status.HTTP_200_OK)
                    elif admission_open:
                        start_offset = 0
                        end_offset = 10
                        next_url = None
                        prev_url = None
                        offset = int(self.request.GET.get('offset', 10))
                        if offset == 10:
                            new_offset = offset * 2
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}"
                            prev_url = None
                        else:
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            if new_prev_offset == 0:
                                new_prev_offset = ''
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}"
                        if collab:
                            if is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}&collab={collab}&is_verified={is_verified}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True),is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True),is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            elif not is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}&collab={collab}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                            else:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}&collab={collab}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}&collab={collab}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}&collab={collab}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=(
                                        False if collab.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, collab=(
                                                                 False if collab.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]
                        else:
                            if is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}&is_verified={is_verified}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True,is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True,is_verified=(False if is_verified.startswith("f") else True), is_featured=(False if is_featured.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][start_offset:end_offset]
                            if not is_verified and is_featured:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}&is_featured={is_featured}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}&is_featured={is_featured}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}&is_featured={is_featured}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, is_featured=(False if is_featured.startswith("f") else True)) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True, is_featured=(False if is_featured.startswith("f") else True)) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][start_offset:end_offset]
                            else:
                                start_offset = 0
                                end_offset = 10
                                next_url = None
                                prev_url = None
                                offset = int(self.request.GET.get('offset', 10))
                                if offset == 10:
                                    new_offset = offset * 2
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&admission_open={admission_open}"
                                    prev_url = None
                                else:
                                    new_next_offset = offset + 10
                                    new_prev_offset = offset - 10
                                    if new_prev_offset == 0:
                                        new_prev_offset = ''
                                    next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&admission_open={admission_open}"
                                    prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&admission_open={admission_open}"
                                count = len(
                                    [sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True) if
                                     AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                         Q(session=currentSession) | Q(session=nextSession))])
                                all_school_admission_open = [sch_obj for sch_obj in
                                                             SchoolProfile.objects.filter(is_active=True) if
                                                             AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(
                                                                 Q(session=currentSession) | Q(session=nextSession))][
                                                            start_offset:end_offset]

                        if len(all_school_admission_open) > 0:
                            serializer = SchoolProfileInsideSerializer(all_school_admission_open, many=True)
                            result1 = {}
                            result1['count'] = count
                            result1['next'] = next_url
                            result1['previous'] = prev_url
                            result1['results'] = serializer.data
                            return Response(result1, status=status.HTTP_200_OK)
                        else:
                            result1 = {}
                            result1['count'] = 0
                            result1['next'] = ""
                            result1['previous'] = ""
                            result1['results'] = []
                            return Response(result1, status=status.HTTP_200_OK)
                    else:
                        pass

            else:
                if incomplete_data:
                    start_offset = 0
                    end_offset = 10
                    next_url = None
                    prev_url = None
                    offset = int(self.request.GET.get('offset', 10))
                    if offset == 10:
                        new_offset = offset * 2
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&incomplete_data={incomplete_data}"
                        prev_url = None
                    else:
                        new_next_offset = offset + 10
                        new_prev_offset = offset - 10
                        if new_prev_offset == 0:
                            new_prev_offset = ''
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&incomplete_data={incomplete_data}"
                        prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&incomplete_data={incomplete_data}"
                        # incomplete_data_list = ["email", "website", "about", "district", "region", "city", "state", "country", "board",
                        #                         "class_relation", "board", "short_address", "street_address"]

                    if collab:
                        start_offset = 0
                        end_offset = 10
                        next_url = None
                        prev_url = None
                        offset = int(self.request.GET.get('offset', 10))
                        if offset == 10:
                            new_offset = offset * 2
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}&incomplete_data={incomplete_data}&collab={collab}"
                            prev_url = None
                        else:
                            new_next_offset = offset + 10
                            new_prev_offset = offset - 10
                            if new_prev_offset == 0:
                                new_prev_offset = ''
                            next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}&incomplete_data={incomplete_data}&collab={collab}"
                            prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}&incomplete_data={incomplete_data}&collab={collab}"
                        sch_obj = SchoolProfile.objects.filter(is_active=True, collab=(False if collab.startswith("f") else True)).filter(
                            Q(email__isnull=True) | Q(website__isnull=True) | Q(description__isnull=True) | Q(district__isnull=True) | Q(district_region__isnull=True) | Q(school_city__isnull=True)
                            | Q(school_state__isnull=True) | Q(school_country__isnull=True) | Q(school_boardss__isnull=True) | Q(class_relation__isnull=True) | Q(short_address__isnull=True)
                            | Q(street_address__isnull=True)
                            ).order_by("-id")[start_offset:end_offset]
                    else:
                        sch_obj = SchoolProfile.objects.filter(is_active=True).filter(
                            Q(email__isnull=True) | Q(website__isnull=True) | Q(description__isnull=True) | Q(
                                district__isnull=True) | Q(district_region__isnull=True) | Q(school_city__isnull=True)
                            | Q(school_state__isnull=True) | Q(school_country__isnull=True) | Q(
                                school_boardss__isnull=True) | Q(class_relation__isnull=True) | Q(
                                short_address__isnull=True)
                            | Q(street_address__isnull=True)
                        ).order_by("-id")[start_offset:end_offset]
                else:
                    start_offset = 0
                    end_offset = 10
                    next_url = None
                    prev_url = None
                    offset = int(self.request.GET.get('offset', 10))
                    if offset == 10:
                        new_offset = offset * 2
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_offset)}"
                        prev_url = None
                    else:
                        new_next_offset = offset + 10
                        new_prev_offset = offset - 10
                        if new_prev_offset == 0:
                            new_prev_offset = ''
                        next_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_next_offset)}"
                        prev_url = f"api/v1/admin_custom/database-inside-school-list/?offset={str(new_prev_offset)}"
                    sch_obj = SchoolProfile.objects.filter(is_active=True).order_by("-id")[start_offset:end_offset]
                # serializer = SchoolProfileInsideSerializer(sch_obj, many=True)
                serializer = SchoolProfileInsideSerializer(list(set(sch_obj)), many=True)
                result1 = {}
                result1['count'] = len(serializer.data)
                result1['next'] = next_url
                result1['previous'] = prev_url
                result1['results'] = serializer.data
                return Response(result1, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data={"message": str(e)},status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        data = self.request.data
        slug = request.query_params.get("slug")
        sch_obj = SchoolProfile.objects.get(slug=slug, is_active=True)
        serializer = SchoolProfileInsideSerializer(sch_obj, data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(instance=sch_obj, validated_data=data)
        if result:
            sch_obj = SchoolProfile.objects.get(slug=result, is_active=True)
            serializer = SchoolProfileInsideSerializer(sch_obj)
            return Response(serializer.data)
        else:
            return Response(data={"message": "Detail not found."},status=status.HTTP_401_UNAUTHORIZED)

class ViewedParentPhoneNumberBySchoolView(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)

    def post(self, request, slug, type, id):
        sch_obj = SchoolProfile.objects.get(slug=slug)
        if type == 'leads':
            user_obj =LeadGenerated.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, lead=user_obj)
        elif type == 'visits':
            user_obj =VisitScheduleData.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, visit=user_obj)
        elif type == 'enquiry':
            user_obj =SchoolEnquiry.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, enquiry=user_obj)
        elif type == 'parent_called':
            user_obj =SchoolContactClickData.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, parent_called=user_obj)
        elif type == 'school_view':
            user_obj =SchoolView.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, school_view=user_obj)
        elif type == 'school_action_on_enquiry':
            user_obj =SchoolPerformedActionOnEnquiry.objects.get(enquiry__id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, school_performed_action_on_enquiry=user_obj)
        elif type == 'ongoing_applications':
            user_obj = ChildSchoolCart.objects.get(id=id)
            ViewedParentPhoneNumberBySchool.objects.create(school=sch_obj, ongoing_application=user_obj)
        return Response(f"{sch_obj.name} can now access this user phone numbers.")
