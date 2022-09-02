import csv
from genericpath import exists
import itertools
import math
import calendar
from datetime import datetime,timedelta,date,time
from pickle import NONE
from allauth.account import app_settings as allauth_settings
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse, JsonResponse
from django.utils import timezone
from rest_auth.serializers import JWTSerializer
from rest_framework import response
from rest_framework.exceptions import APIException
from django.utils.encoding import force_text
import pytz
from uuid import UUID
from django_elasticsearch_dsl_drf.constants import (LOOKUP_FILTER_GEO_DISTANCE,
                                                    MATCHING_OPTION_MUST,
                                                    SUGGESTER_COMPLETION,
                                                    LOOKUP_QUERY_LTE,
                                                    LOOKUP_FILTER_TERMS,
                                                    LOOKUP_FILTER_RANGE,
                                                    LOOKUP_FILTER_PREFIX,
                                                    LOOKUP_FILTER_WILDCARD,
                                                    LOOKUP_QUERY_IN,
                                                    LOOKUP_QUERY_GT,
                                                    LOOKUP_QUERY_GTE,
                                                    LOOKUP_QUERY_LT,
                                                    LOOKUP_QUERY_EXCLUDE,)
from django_elasticsearch_dsl_drf.filter_backends import (
    CompoundSearchFilterBackend, DefaultOrderingFilterBackend,
    FilteringFilterBackend, GeoSpatialFilteringFilterBackend,FacetedSearchFilterBackend,
    GeoSpatialOrderingFilterBackend, HighlightBackend, SuggesterFilterBackend,
    NestedFilteringFilterBackend, OrderingFilterBackend, SearchFilterBackend,IdsFilterBackend)
from django_elasticsearch_dsl_drf.pagination import LimitOffsetPagination
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch import Elasticsearch
from notifications.models import Notification
from notifications.signals import notify
from rest_auth.registration.views import RegisterView
from rest_framework import generics, permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.api.v1.serializers import TokenSerializer
from admission_forms.api.v1.serializers import (
    SchoolApplicationDetailSerializer, SchoolApplicationListSerializer, ApplicationStatusSerializer, ApplicationStatusLogSerializer, ApplicationStatusLogCreateSerializer,CopyObjectSerializer)
from admission_forms.filters import SchoolApplicationFilter
from admission_forms.models import SchoolApplication, ApplicationStatus, ApplicationStatusLog,FormReceipt,CommonRegistrationFormAfterPayment
from schools.api.v1.serializers import SchoolDocumentSerializer, SchoolUploadCsvSerializer, AdmissionSessionsSerializer, AdmissionPageContentSerializer, SchoolEnquirySerializer, HomePageSchoolSerializer
from schools.documents import SchoolProfileDocument
from schools.filters import RegionFilter, StateFilter, CityFilter, DistrictFilter, DistrictRegionFilter, AgeCiteriaFilter, FeeStructureFilter, AdmissionOpenClassesFilter, AdmissionPageContentFilter
from schools.mixins import SchoolPerformCreateUpdateMixin
from schools.models import *
from schools.permissions import (HasSchoolChildModelPermissionOrReadOnly,
                                 HasSchoolObjectPermission, IsSchool,
                                 IsSchoolOrReadOnly, SchoolDashboardPermission,
                                 SchoolEnquiryPermission, SchoolViewPermission, SchoolContactClickDataPermission, BoardingSchoolExtendProfilePermissions)
from schools.resources import *
from schools.tasks import send_school_code_request_mail,add_selected_child_data_from_csv
from schools.utils import (default_required_admission_form_fields,
                           default_required_child_fields,
                           default_required_father_fields,
                           default_required_guardian_fields,
                           default_required_mother_fields,
                           get_year_value_for_seo,
                           convert_timedelta,
                           get_boarding_school_faqs, remove_unnecessary_json_data)

from . import serializers
from parents.permissions import (IsParent)
from backend.logger import info_logger,error_logger
import pandas as pd
from rest_framework.parsers import FileUploadParser
import json
from rest_framework.decorators import api_view
from childs.models import Child
from articles.models import ExpertArticle
from news.models import News
from rest_framework.permissions import BasePermission, SAFE_METHODS
import requests
from admin_custom.models import AdmissionDoneData,LeadGenerated,VisitScheduleData

class SchoolRegisterView(RegisterView):
    serializer_class = serializers.SchoolRegisterSerializer

    def get_response_data(self, user):
        if (
            allauth_settings.EMAIL_VERIFICATION
            == allauth_settings.EmailVerificationMethod.MANDATORY
        ):
            return {"detail": _("Verification e-mail sent.")}

        if getattr(settings, "REST_USE_JWT", False):
            data = {"user": user, "token": self.token}
            return JWTSerializer(data).data
        else:
            return TokenSerializer(user.auth_token.first()).data


class SchoolProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.SchoolProfileSerializer
    lookup_field = "slug"
    permission_classes = [
        IsSchoolOrReadOnly,
    ]

    def get_queryset(self):
        queryset = SchoolProfile.objects.all().select_related(
            "school_type",
            "school_board",
            # "region",
            # "state"
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            ).prefetch_related(
            Prefetch(
                "admmissionopenclasses_set",
                queryset=AdmmissionOpenClasses.objects.all().select_related("class_relation").order_by('class_relation__rank'))).prefetch_related(
                "profile_views",
                "school_boardss",
                "class_relation",
                "schooladmissionformfee_set",)
        return queryset

    def set_form_price_for_school(self,form_price,school):
        for class_relation in school.class_relation.all():
            if SchoolAdmissionFormFee.objects.filter(class_relation=class_relation,school_relation=school).exists():
                formItem = SchoolAdmissionFormFee.objects.filter(class_relation=class_relation,school_relation=school)
                for feesItem in formItem:
                    feesItem.form_price=form_price
                    feesItem.save()
            else:
                form_fee_obj,boolean = SchoolAdmissionFormFee.objects.get_or_create(class_relation=class_relation,school_relation=school)
                form_fee_obj.form_price=form_price
                form_fee_obj.save()

    def set_required_optional_application_fields_for_school(self, data, school):
        new_obj = RequiredOptionalSchoolFields.objects.create(school=school)
        new_obj.required_admission_form_fields = new_obj.school.required_admission_form_fields
        new_obj.required_child_fields = new_obj.school.required_child_fields
        new_obj.required_father_fields = new_obj.school.required_father_fields
        new_obj.required_mother_fields = new_obj.school.required_mother_fields
        new_obj.required_guardian_fields = new_obj.school.required_guardian_fields
        new_obj.save()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.SchoolProfileSerializer
        if self.request.method in ["PUT", "PATCH"]:
            school = SchoolProfile.objects.get(user=self.request.user)
            if 'form_price' in self.request.data:
                self.set_form_price_for_school(form_price=self.request.data['form_price'], school=school)
            if 'required_admission_form_fields' in self.request.data or 'required_child_fields' in self.request.data or 'required_father_fields' in self.request.data or 'required_mother_fields' in self.request.data or 'required_guardian_fields' in self.request.data:
                self.set_required_optional_application_fields_for_school(data=remove_unnecessary_json_data(self.request.data), school=school)
            return serializers.SchoolProfileUpdateSerializer


class SchoolGalleryView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    serializer_class = serializers.GallerySerializer
    permission_classes = [
        HasSchoolChildModelPermissionOrReadOnly,
    ]

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        queryset = Gallery.objects.filter(
            is_active=True).filter(school__slug=slug)
        return queryset

@api_view(['GET'])
def school_fee_stucture_min_max_api(request,**kwargs):
    school_slug = kwargs.get("slug",'')

    if school_slug == '':
        return Response({'error':'Pass A school Slug'})

    if not  SchoolProfile.objects.filter(slug=school_slug).exists():
        return Response({
            'error':'School Does Not Exist'
        })

    school = SchoolProfile.objects.get(slug=school_slug)
    fees_structure =  FeeStructure.objects.filter(school = school)

    final_list = []
    for j in fees_structure:
        final_list.append(j.fee_price)
    if final_list:
        final_list = [i for i in final_list if i]
        return Response({
             'school':school.name,
             'minimum':round(min(final_list)) if final_list else 0,
            'maximum':round(max(final_list)) if final_list else 0
             })
    else:
        return Response({'school':school.name,
                          'minimum':0,
                          'maximux':0
                          })


class SchoolGalleryDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.GallerySerializer
    permission_classes = [
        HasSchoolChildModelPermissionOrReadOnly,
    ]
    lookup_field = "pk"

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        queryset = Gallery.objects.filter(
            is_active=True).filter(school__slug=slug)
        return queryset

#
class SchoolBrowseSearchView(APIView):
    def get(self, request, format=False):
        elastic_host = "http://localhost:9200"
        if hasattr(settings, "ELASTICSEARCH_DSL"):
            elastic_host = settings.ELASTICSEARCH_DSL["default"]["hosts"]
            http_auth = settings.ELASTICSEARCH_DSL["default"]["http_auth"]
        es = Elasticsearch([f"http://{elastic_host}"], http_auth=http_auth)

        page_size = self.request.GET.get("page_size", 10)
        offset_size = self.request.GET.get("offset_size", 0)

        school_type_slug = self.request.GET.get("school_type_slug", None)
        region_slug = self.request.GET.get("region_slug", None)
        format_slug = self.request.GET.get("format_slug", None)
        state_slug = self.request.GET.get("state_slug", None)
        school_board_slug = self.request.GET.get("school_board_slug", None)
        school_category = self.request.GET.get("school_category", None)
        distance = self.request.GET.get("distance", None)
        latitude = self.request.GET.get("latitude", None)
        longitude = self.request.GET.get("longitude", None)
        class_relation_slug = self.request.GET.get("class_relation_slug", None)
        fee_price_gte = self.request.GET.get("fee_price_gte", 0)
        fee_price_lte = self.request.GET.get("fee_price_lte", 10000000)
        admission_open_class = self.request.GET.get(
            "admission_open_class", None)

        body = {}

        school_name = self.request.GET.get("school_name", None)

        body["query"] = {}

        body["query"]["bool"] = {}
        body["query"]["bool"]["must"] = []
        body["query"]["bool"]["must"].append(
            {"match_phrase": {"is_active": True}})
        body["query"]["bool"]["must"].append(
            {"match_phrase": {"is_verified": True}})
        body["track_scores"] = True
        body["sort"] = [{"global_rank": {"order": "desc"}}, {
            "admissionclasses_open_count": {"order": "desc"}} , {"total_views": {"order": "desc"}}]

        if school_name:
            body["query"]["bool"]["must"].append(
                [
                    {
                        "simple_query_string": {
                            "query": school_name + "~5",
                            "fields": ["name^3"]
                        }
                    },
                ]
            )
            body["highlight"] = {
                "pre_tags": ["<b>"],
                "post_tags": ["</b>"],
                "fields": {"name": {}, },
            }

        if school_type_slug:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"school_type.slug": school_type_slug}})

        if region_slug:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"region.slug": region_slug}})
            body["sort"] = [{"region_rank": {"order": "desc"}}, {
                "admissionclasses_open_count": {"order": "desc"}} , {"total_views": {"order": "desc"}}]

        if format_slug:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"school_format.slug": format_slug}})

        if state_slug:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"state.slug": state_slug}})

        if school_board_slug:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"school_board.slug": school_board_slug}})

        if school_category:
            body["query"]["bool"]["must"].append(
                {"match_phrase": {"school_category": school_category}})

        if class_relation_slug or int(fee_price_lte) < 10000000:
            nested_query = {}
            nested_query["nested"] = {}
            nested_query["nested"]["path"] = "school_fee_structure"
            nested_query["nested"]["query"] = {}
            nested_query["nested"]["query"]["bool"] = {}
            nested_query["nested"]["query"]["bool"]["must"] = []
            if class_relation_slug:
                nested_query["nested"]["query"]["bool"]["must"].append({
                    "match": {
                        "school_fee_structure.class_relation.slug": class_relation_slug
                    }
                }
                )

            if int(fee_price_lte) < 10000000:
                nested_query["nested"]["query"]["bool"]["must"].append({
                    "range": {
                        "school_fee_structure.fee_price": {
                            "gte": int(fee_price_gte),
                            "lte": int(fee_price_lte)
                        }
                    }
                }
                )

            body["query"]["bool"]["must"].append(nested_query)

        if admission_open_class:
            nested_query = {}
            nested_query["nested"] = {}
            nested_query["nested"]["path"] = "admmissionopenclasses_set"
            nested_query["nested"]["query"] = {}
            nested_query["nested"]["query"]["bool"] = {}
            nested_query["nested"]["query"]["bool"]["must"] = []
            nested_query["nested"]["query"]["bool"]["must"].append({
                "match": {
                    "admmissionopenclasses_set.class_relation.id": admission_open_class
                }
            })

            body["query"]["bool"]["must"].append(nested_query)

        if distance and latitude and longitude:
            body["query"]["bool"]["filter"] = {}
            body["query"]["bool"]["filter"]["geo_distance"] = {}
            body["query"]["bool"]["filter"]["geo_distance"]["distance"] = f"{distance}km"
            body["query"]["bool"]["filter"]["geo_distance"]["geocoords"] = {}
            body["query"]["bool"]["filter"]["geo_distance"]["geocoords"]["lat"] = latitude
            body["query"]["bool"]["filter"]["geo_distance"]["geocoords"]["lon"] = longitude
            body["sort"].append({"_geo_distance": {"order": "asc", "geocoords": f"{latitude},{longitude}"}})

        # import json
        # print(json.dumps(body, indent=4))

        res = es.search(
            index="prod-school-profile",
            size=page_size,
            from_=offset_size,
            # _source=[
            #     "title",
            #     "description",
            #     "timestamp",
            #     "slug",
            #     "thumbnail",
            #     "views",
            #     "board",
            #     "sub_category",
            #     "id",
            # ],
            body=body,
        )
        return Response(res, status=status.HTTP_200_OK)


class SchoolTypeView(generics.ListAPIView):
    serializer_class = serializers.SchoolTypeSerializer
    queryset = SchoolType.objects.all().order_by("order_rank")


class SchoolBoardView(generics.ListAPIView):
    serializer_class = serializers.SchoolBoardSerializer
    queryset = SchoolBoard.objects.all()


class RegionView(generics.ListAPIView):
    serializer_class = serializers.RegionSerializer
    queryset = Region.objects.filter(active=True).order_by("rank")
    filterset_class = RegionFilter


class SchoolFormatView(generics.ListAPIView):
    serializer_class = serializers.SchoolFormatSerializer
    queryset = SchoolFormat.objects.all()


class StateView(generics.ListAPIView):
    serializer_class = serializers.StateSerializer
    queryset = State.objects.all()


class CountryView(generics.ListAPIView):
    serializer_class = serializers.CountrySerializer
    queryset = Country.objects.all()

class StatesView(generics.ListAPIView):
    serializer_class = serializers.StatesSerializer
    queryset = States.objects.all()
    filterset_class = StateFilter

class CityView(generics.ListAPIView):
    serializer_class = serializers.CitySerializer
   # queryset = City.objects.all().filter(params__Count__gt=0).order_by('-params__Count')
    filterset_class = CityFilter

    def get_queryset(self):
        is_featured =self.request.GET.get("is_featured",None)
        if is_featured:
            return City.objects.all().filter(params__Count__gt=0,is_featured=is_featured).order_by('-params__Count')
        return City.objects.all().filter(params__Count__gt=0).order_by('-params__Count')


class DistrictView(generics.ListAPIView):
    serializer_class = serializers.DistrictSerializer
    queryset = District.objects.all().filter(params__Count__gt=0).order_by('-params__official_count')
    filterset_class = DistrictFilter


class DistrictRegionView(generics.ListAPIView):
    serializer_class = serializers.DistrictRegionSerializer
    queryset = DistrictRegion.objects.all().filter(params__Count__gt=0).order_by('-params__official_count')
    filterset_class = DistrictRegionFilter


class SchoolClassesView(generics.ListAPIView):
    serializer_class = serializers.SchoolClassesSerializer
    queryset = SchoolClasses.objects.filter(active=True).order_by("rank")

    # def get_queryset(self):
    #     data = []
    #     res = SchoolClasses.objects.filter(active=True)
    #     multi_relation_ids = [relation.unique_class_relation.id for relation in SchoolMultiClassRelation.objects.filter()]
    #     for result in res:
    #         if result.id in multi_relation_ids:
    #             multi_relation = SchoolMultiClassRelation.objects.get(unique_class_relation=result.id)
    #             obj_filter = multi_relation.multi_class_relation.filter()
    #             for multi_obj in obj_filter:
    #                 if SchoolClasses.objects.get(id=multi_obj.id):
    #                     data.append(multi_obj.id)
    #     data = set(data) - set(multi_relation_ids)
    #     queryset = SchoolClasses.objects.filter(active=True).exclude(id__in=data).order_by("rank")
    #     return queryset

class ActivityTypeView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        school = generics.get_object_or_404(SchoolProfile, slug=self.kwargs.get("slug"))
        queryset = ActivityType.objects.filter(
            school=school).prefetch_related("activities")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.ActivityTypeSerializer
        if self.request.method == "POST":
            return serializers.ActivityTypeCreateSerializer


class ActivityTypeDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = ActivityType.objects.filter(
            school=school).prefetch_related("activities")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.ActivityTypeSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.ActivityTypeCreateSerializer


class ActivityView(generics.CreateAPIView):
    serializer_class = serializers.ActivitySerializer


class ActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ActivitySerializer
    lookup_field = "pk"

    def get_queryset(self):
        school = generics.get_object_or_404(SchoolProfile, slug=self.kwargs.get("slug"))
        queryset = Activity.objects.filter(activity_type__school=school)
        return queryset


class FeeStructureView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    permission_classes = [IsSchoolOrReadOnly, ]
    filterset_class = FeeStructureFilter
    def get_queryset(self):
        if SchoolProfile.objects.filter(slug=self.kwargs.get("slug")).exists():
            school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
            queryset = FeeStructure.objects.filter(school=school).select_related(
                "class_relation","stream_relation").prefetch_related("fees_parameters").order_by("class_relation__rank")
            return queryset
        else:
            school = SchoolProfile.objects.get(id=1346)
            queryset = FeeStructure.objects.filter(school=school).select_related(
                "class_relation","stream_relation").prefetch_related("fees_parameters").order_by("class_relation__rank")
            return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.FeeStructureSerializer
        if self.request.method == "POST":
            return serializers.FeeStructureCreateUpdateSeirializer



class FeeStructureDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasSchoolObjectPermission, ]
    lookup_field = "pk"

    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = FeeStructure.objects.filter(school=school).select_related(
            "class_relation","stream_relation").prefetch_related("fees_parameters").order_by("class_relation__rank")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.FeeStructureSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.FeeStructureCreateUpdateSeirializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in instance._prefetched_objects_cache['fees_parameters']:
            i.delete()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeeParameterobjectDelete(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasSchoolObjectPermission, ]
    lookup_field = "pk"
    serializer_class = serializers.SchoolFeesParametersSerializer

    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = SchoolFeesParameters.objects.filter(school=school)
        return queryset


class FeeHeadDetailViews(generics.ListCreateAPIView):
    serializer_class=serializers.SchoolFeesTypeSerializer
    def get_queryset(self):
        queryset = SchoolFeesType.objects.all()
        return queryset

class FeeStructureStreamsDetailView(generics.ListCreateAPIView):
    serializer_class=serializers.SchoolStreamSerializer
    def get_queryset(self):
        queryset = SchoolStream.objects.all()
        return queryset


class FeeStructureClassFilterView(generics.ListCreateAPIView):
    permission_classes = [IsSchoolOrReadOnly, ]
    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = FeeStructure.objects.filter(school=school,class_relation=self.kwargs.get("class_id")).select_related("stream_relation")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.FeeStructureSerializer



class FeeStructureStreamDetailView(SchoolPerformCreateUpdateMixin,generics.GenericAPIView):
    permission_classes = [HasSchoolObjectPermission, ]

    def get(self, request, slug,pk,stream_id):
        try:
            school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
            self.queryset = FeeStructure.objects.filter(school=school,class_relation=self.kwargs.get("pk"),stream_relation=self.kwargs.get("stream_id"))
            self.serializer=self.get_serializer(self.queryset,many=True)
            if not self.serializer.data:
               raise CustomValidation('Data For Given id do not exist,check either class id exist or stream id', 'data', status_code=status.HTTP_404_NOT_FOUND)
        except FeeStructure.DoesNotExist:
             raise CustomValidation('Data For Given id do not exist', 'data', status_code=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer.data)

    def put(self,request, slug,pk,stream_id):
        try:
            school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
            self.instance =  FeeStructure.objects.filter(school=school,class_relation=self.kwargs.get("pk"),stream_relation=self.kwargs.get("stream_id")).first()
            self.serializer = self.get_serializer(self.instance, data=request.data)
            self.serializer.is_valid(raise_exception=True)
            self.serializer.save()
        except FeeStructure.DoesNotExist:
             raise CustomValidation('Data For Given id do not exist', 'data', status_code=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": status.HTTP_202_ACCEPTED,
            "Message":"Data Updated"
        })

    def patch(self,request, slug,pk,stream_id):
        try:
            school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
            self.instance =  FeeStructure.objects.filter(school=school,class_relation=self.kwargs.get("pk"),stream_relation=self.kwargs.get("stream_id")).first()
            self.serializer = self.get_serializer(self.instance, data=request.data,partial=True)
            self.serializer.is_valid(raise_exception=True)
            self.serializer.save()
        except FeeStructure.DoesNotExist:
             raise CustomValidation('Data For Given id do not exist', 'data', status_code=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": status.HTTP_202_ACCEPTED,
            "Message":"Data Updated"
        })

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.FeeStructureSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.FeeStructureCreateUpdateSerializer


class SchoolPointCreateView(SchoolPerformCreateUpdateMixin, generics.CreateAPIView):
    serializer_class = serializers.SchoolPointCreateSerializer
    permission_classes = [IsSchoolOrReadOnly, ]
    queryset = SchoolPoint.objects.all()


class SchoolPointUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.SchoolPointCreateSerializer
    permission_classes = [SchoolDashboardPermission, ]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        return generics.get_object_or_404(queryset, school=school)

    def get_queryset(self):
        queryset = SchoolPoint.objects.all()
        return queryset

    def perform_update(self, serializer):
        school_id = self.request.user.current_school
        serializer.save(school_id=school_id)


class DistancePointView(generics.ListCreateAPIView):
    serializer_class = serializers.DistancePointSerializer
    #permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = DistancePoint.objects.filter(
            school=school).order_by("start")
        return queryset

    def perform_create(self, serializer):
        school_id = self.request.user.current_school
        serializer.save(school_id=school_id)


class DistancePointDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.DistancePointSerializer
    lookup_field = "pk"
    permission_classes = [HasSchoolObjectPermission]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = DistancePoint.objects.filter(school=school)
        return queryset

    def perform_update(self, serializer):
        school_id = self.request.user.current_school
        serializer.save(school_id=school_id)


class SchoolBasicProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [
        IsSchool,
    ]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return generics.get_object_or_404(
            queryset, pk=int(
                self.request.user.current_school))

    def get_queryset(self):
        queryset = SchoolProfile.objects.all().select_related(
            "school_type",
            "school_board",
            # "region",
            # "state"
            "school_country",
            "school_state",
            "school_city",
            "district",
            "district_region",
            ).prefetch_related(
            Prefetch(
                "admmissionopenclasses_set",
                queryset=AdmmissionOpenClasses.objects.all().select_related("class_relation"))).prefetch_related(
                "profile_views",
                "class_relation",
                "school_boardss",)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.SchoolProfileSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.SchoolDashboardProfileUpdateSerializer

class GetAdmmissionOpenClassesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            id = self.kwargs["id"]
            if AdmmissionOpenClasses.objects.filter(
                    id=id
            ).exists():
                cls = AdmmissionOpenClasses.objects.get(
                    id=id
                )
                serializer = serializers.AdmmissionOpenClassesSerializer(cls)
                return Response(serializer.data)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except:
            try:
                slug = self.kwargs.get("slug", None)
                session = request.query_params.get("session", "")
                school = generics.get_object_or_404(SchoolProfile, slug=slug)
                data = []
                if session:
                    results = [cls for cls in AdmmissionOpenClasses.objects.filter(school=school, session=session)]
                    multi_relation_ids = [multi.id for relation in SchoolMultiClassRelation.objects.filter()
                                          for multi in relation.multi_class_relation.filter()]
                    data1 = []
                    # results = self.paginate_queryset(res, request, view=self)
                    for result in results:
                        if result.class_relation.id in multi_relation_ids:
                            multi_relation = SchoolMultiClassRelation.objects.get(multi_class_relation__id=result.class_relation.id)
                            obj_filter = multi_relation.multi_class_relation.filter()

                            for multi_obj in obj_filter:
                                if data1:
                                    ids = [val['class_relation']['id'] for val in data1]
                                    if multi_obj.id not in ids:
                                        if SchoolClasses.objects.filter(id=multi_obj.id).exists() and AdmmissionOpenClasses.objects.filter(session=session, school=school, class_relation__id=result.class_relation.id).exists():
                                            data1.append(
                                                {"id":[m.id for m in AdmmissionOpenClasses.objects.filter(session=session, school=school, class_relation__id=result.class_relation.id)][0]
                                                    ,"class_relation":{
                                                    "id":multi_obj.id,"name":multi_obj.name, "slug": multi_obj.slug,
                                                    "rank": multi_obj.rank},  "admission_open": result.admission_open,
                                                    "form_limit": result.form_limit,
                                                    "available_seats": result.available_seats,
                                                    "session": result.session,
                                                    "last_date": result.last_date
                                                          })
                                            data.append(multi_obj.id)
                                else:
                                    if SchoolClasses.objects.filter(id=multi_obj.id).exists() and AdmmissionOpenClasses.objects.filter(session=session, school=school, class_relation__id=multi_obj.id).exists():
                                        data1.append(
                                            {"id":[m.id for m in AdmmissionOpenClasses.objects.filter(session=session, school=school, class_relation__id=multi_obj.id)][0]
                                                ,"class_relation":{
                                                "id":multi_obj.id,"name":multi_obj.name, "slug": multi_obj.slug,
                                                "rank": multi_obj.rank},  "admission_open": result.admission_open,
                                                "form_limit": result.form_limit,
                                                "available_seats": result.available_seats,
                                                "session": result.session,
                                                "last_date": result.last_date
                                                      })
                                        data.append(multi_obj.id)
                    if len(set(data)) > len(set(multi_relation_ids)):
                        data = list(set(data) - set(multi_relation_ids))
                    else:
                        data = list(set(multi_relation_ids) - set(data))
                    ress = AdmmissionOpenClasses.objects.filter(session=session, school=school).exclude(class_relation__id__in=data)
                    serializer = serializers.AdmmissionOpenClassesSerializer(ress, many=True)
                    old_result = serializer.data + data1
                    new_dict_list = [dict(d) for d in old_result]
                    new_inner_dict_list = [{"id":d["id"], "class_relation": dict(d["class_relation"]),
                                            "admission_open":d["admission_open"], "form_limit":d["form_limit"],
                                            "available_seats":d["available_seats"], "session":d["session"],
                                            "last_date":d["last_date"]} for d in new_dict_list]
                    res_list = []
                    class_ids =list(set([da['class_relation']['id'] for da in new_inner_dict_list]))
                    for lst in new_inner_dict_list:
                        for cls in class_ids:
                            if cls == lst['class_relation']['id']:
                                res_list.append(lst)
                                class_ids.remove(cls)
                else:
                    results = [cls for cls in AdmmissionOpenClasses.objects.filter(school=school)]
                    multi_relation_ids = [multi.id for relation in SchoolMultiClassRelation.objects.filter()
                                          for multi in relation.multi_class_relation.filter()]
                    data1 = []
                    # results = self.paginate_queryset(res, request, view=self)
                    for result in results:
                        if result.class_relation.id in multi_relation_ids:
                            multi_relation = SchoolMultiClassRelation.objects.get(
                                multi_class_relation__id=result.class_relation.id)
                            obj_filter = multi_relation.multi_class_relation.filter()

                            for multi_obj in obj_filter:
                                if data1:
                                    ids = [val['class_relation']['id'] for val in data1]
                                    if multi_obj.id not in ids:
                                        if SchoolClasses.objects.filter(id=multi_obj.id).exists() and AdmmissionOpenClasses.objects.filter(session=session, school=school, class_relation__id=result.class_relation.id).exists():
                                            data1.append(
                                                {"id": [m.id for m in
                                                        AdmmissionOpenClasses.objects.filter(school=school,
                                                                                             class_relation__id=result.class_relation.id)][
                                                    0]
                                                    , "class_relation": {
                                                    "id": multi_obj.id, "name": multi_obj.name, "slug": multi_obj.slug,
                                                    "rank": multi_obj.rank}, "admission_open": result.admission_open,
                                                 "form_limit": result.form_limit,
                                                 "available_seats": result.available_seats,
                                                 "session": result.session,
                                                 "last_date": result.last_date
                                                 })
                                            data.append(multi_obj.id)
                                else:
                                    if SchoolClasses.objects.filter(
                                            id=multi_obj.id).exists() and AdmmissionOpenClasses.objects.filter(session=session,
                                                                                                               school=school,
                                                                                                               class_relation__id=multi_obj.id).exists():
                                        data1.append(
                                            {"id": [m.id for m in
                                                    AdmmissionOpenClasses.objects.filter(school=school,
                                                                                         class_relation__id=multi_obj.id)][
                                                0]
                                                , "class_relation": {
                                                "id": multi_obj.id, "name": multi_obj.name, "slug": multi_obj.slug,
                                                "rank": multi_obj.rank}, "admission_open": result.admission_open,
                                             "form_limit": result.form_limit,
                                             "available_seats": result.available_seats,
                                             "session": result.session,
                                             "last_date": result.last_date
                                             })
                                        data.append(multi_obj.id)
                    if len(set(data)) > len(set(multi_relation_ids)):
                        data = list(set(data) - set(multi_relation_ids))
                    else:
                        data = list(set(multi_relation_ids) - set(data))
                    ress = AdmmissionOpenClasses.objects.filter(school=school).exclude(
                        class_relation__id__in=data)
                    serializer = serializers.AdmmissionOpenClassesSerializer(ress, many=True)
                    old_result = serializer.data + data1
                    new_dict_list = [dict(d) for d in old_result]
                    new_inner_dict_list = [{"id": d["id"], "class_relation": dict(d["class_relation"]),
                                            "admission_open": d["admission_open"], "form_limit": d["form_limit"],
                                            "available_seats": d["available_seats"], "session": d["session"],
                                            "last_date": d["last_date"]} for d in new_dict_list]
                    res_list = []
                    class_ids = list(set([da['class_relation']['id'] for da in new_inner_dict_list]))
                    for lst in new_inner_dict_list:
                        for cls in class_ids:
                            if cls == lst['class_relation']['id']:
                                res_list.append(lst)
                                class_ids.remove(cls)
                resp = {"count": len(res_list),
                            "next":"",
                            "previous":"",
                            "results":res_list}
                return Response(resp)
            # return self.get_paginated_response(res_list)
            except Exception as e:
                return Response(
                    data={"message": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class AdmmissionOpenClassesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # try:
        slug = self.kwargs.get("slug", None)
        session = self.request.query_params.get("session", None)
        if session:
            if AdmmissionOpenClasses.objects.filter(school__slug=slug, session=session).exists():
                cls = AdmmissionOpenClasses.objects.filter(
                    school__slug=slug, session=session
                )
                serializer = serializers.AdmmissionOpenClassesSerializer(cls, many=True)
                res_list=serializer.data
                resp = {"count": len(res_list),
                        "next": "",
                        "previous": "",
                        "results": res_list}
                return Response(resp)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_200_OK,
                )
        else:
            if AdmmissionOpenClasses.objects.filter(school__slug=slug).exists():
                cls = AdmmissionOpenClasses.objects.filter(
                    school__slug=slug
                )
                serializer = serializers.AdmmissionOpenClassesSerializer(cls, many=True)
                res_list = serializer.data
                resp = {"count": len(res_list),
                        "next": "",
                        "previous": "",
                        "results": res_list}
                return Response(resp)
            else:
                return Response(
                    data={"message": "Details Not Found."},
                    status=status.HTTP_200_OK,
                )

    def post(self, request, *args, **kwargs):
        data = self.request.data
        serializer = serializers.AdmmissionOpenClassesSerializer(data=data)
        data['school_slug'] = self.kwargs.get("slug", None)
        serializer.is_valid(raise_exception=True)
        result = serializer.save(validated_data=data)
        cls = AdmmissionOpenClasses.objects.get(id=result)
        serializer = serializers.AdmmissionOpenClassesSerializer(cls)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        data = self.request.data
        id = self.kwargs.get("id", None)
        slug = self.kwargs.get("slug", None)
        cls = AdmmissionOpenClasses.objects.get(school__slug=slug, id=id)
        serializer = serializers.AdmmissionOpenClassesSerializer(cls, data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(instance=cls, validated_data=data)
        if result:
            open_cls = AdmmissionOpenClasses.objects.get(id=result)
            serializer = serializers.AdmmissionOpenClassesSerializer(open_cls)
            return Response(serializer.data)
        else:
            return Response(
                data={
                    "message": "Detail not found."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


    #
    # def get_queryset(self):
    #     slug = self.kwargs.get("slug", None)
    #     school = generics.get_object_or_404(SchoolProfile, slug=slug)
    #     queryset = AdmmissionOpenClasses.objects.filter(school=school)
    #     print("queryset---------->", queryset)
    #     return queryset


class AdmmissionOpenClassesDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.AdmmissionOpenClassesSerializer
    #permission_classes = [HasSchoolChildModelPermissionOrReadOnly]
    lookup_field = "pk"

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = AdmmissionOpenClasses.objects.filter(school=school)
        return queryset


class AdmissionFormOptionalKeysView(APIView):

    def get(self, request, format=False):
        response = {}
        response["default_required_admission_form_fields"] = default_required_admission_form_fields().keys()
        response["default_required_child_fields"] = default_required_child_fields().keys()
        response["default_required_father_fields"] = default_required_father_fields().keys()
        response["default_required_mother_fields"] = default_required_mother_fields().keys()
        response["default_required_guardian_fields"] = default_required_guardian_fields(
        ).keys()
        return Response(response, status=status.HTTP_200_OK)


class SchoolApplicationListView(generics.ListAPIView):
    serializer_class = SchoolApplicationListSerializer
    filterset_class = SchoolApplicationFilter

    def get_queryset(self):
        return SchoolApplication.objects.select_related(
            "child", "form").filter(
            school__pk=self.request.user.current_school)


class SchoolApplicationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SchoolApplicationDetailSerializer

    def get_queryset(self):
        return SchoolApplication.objects.select_related(
            "child", "form").filter(
            school__pk=self.request.user.current_school)

class ApplicationStatusListView(generics.ListAPIView):
    serializer_class = ApplicationStatusSerializer
    filterset_fields = ('type',)

    def get_queryset(self):
        return ApplicationStatus.objects.all().order_by('rank')

class ApplicationStatusLogCreateView(APIView):
    serializer_class = ApplicationStatusLogCreateSerializer
    permission_classes = [IsSchool]

    def post(self,request, *args, **kwargs):
        serializer = ApplicationStatusLogCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({}, status=status.HTTP_200_OK)
        else:
            error_logger(f"{self.__class__.__name__} Serializer Invalid for userid {self.request.user.id}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class SchoolOngoingApplicationsListView(generics.ListAPIView):
    serializer_class = serializers.SchoolOngoingApplicationsSerializer
    permission_classes = [SchoolViewPermission]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = ChildSchoolCart.objects.filter(school=school).order_by("-timestamp")
        return queryset

class SchoolViewsListView(generics.ListAPIView):
    serializer_class = serializers.SchoolViewSerializer
    permission_classes = [SchoolViewPermission]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = SchoolView.objects.filter(school=school).order_by('-timestamp')
        # if('shortlisted' in self.request.GET and self.request.GET.get('shortlisted')=='yes'):
        #     list_of_ids=[]
        #     for obj in queryset:
        #             if ChildSchoolCart.objects.filter(child__user=obj.user, school=school).exists():
        #                 list_of_ids.append(obj.id)
        #     queryset = SchoolView.objects.filter(id__in = list_of_ids)
        return queryset

class SchoolViewsMonthWiseView(APIView):
    permission_classes = [SchoolViewPermission]

    def get(self,request,slug):
        slug = self.kwargs.get("slug",None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        month = datetime.now().date().month +1
        year = datetime.now().date().year
        views={}
        for i in range(0,5):
            month = month -1
            if(month==0):
                month=12
                year-=1
            if('shortlisted' in request.GET and request.GET.get('shortlisted')=='yes'):
                users = SchoolView.objects.filter(school=school,updated_at__month=month,updated_at__year=year,).values_list('user')
                cnt = 0
                for user in users:
                    if ChildSchoolCart.objects.filter(child__user=user, school=school).exists():
                        cnt+=1
                views[calendar.month_name[month]] = cnt
            else:
                views[calendar.month_name[month]]= SchoolView.objects.filter(school=school,updated_at__month=month,updated_at__year=year).count()
        return Response(views,status=status.HTTP_200_OK)

class SchoolEnquiryView(generics.ListCreateAPIView):
    serializer_class = serializers.SchoolEnquirySerializer
    queryset = SchoolEnquiry.objects.all()

    permission_classes = [SchoolEnquiryPermission, ]

    def perform_create(self, serializer):
        slug = self.kwargs.get("slug", None)
        source = self.request.GET.get("source",'General').lower()
        ad_source  = self.request.GET.get("ad_value",'')
        if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
            ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
        else:
            ad_source =''
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        if self.request.user.is_authenticated:
            if self.request.user.ad_source and self.request.user.ad_source != "":
                ad_source = self.request.user.ad_source
            serializer.save(user=self.request.user, school=school,source=source, ad_source=ad_source)
        else:
            serializer.save(school=school,source=source,ad_source=ad_source)

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        if self.request.user.is_school:
            school_id = self.request.user.current_school
            queryset = SchoolEnquiry.objects.filter(
                school__id=school_id, school__slug=slug).order_by("-timestamp")
        else:
            queryset = SchoolEnquiry.objects.none()
        return queryset


class FormsSubmittedWeeklyView(APIView):
    permission_classes = [IsSchool, ]

    def get(self, request, **kwargs):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        school_id = self.request.user.current_school
        if school_id == school.id:
            total = SchoolApplication.objects.filter(
                school__slug=slug).count()
            res = {}
            res["total"] = total
            res["results"] = []
            num_weeks = 5
            day_of_week = timezone.now().date().weekday()
            from_date = timezone.now().date() - timezone.timedelta(days=day_of_week)
            to_date = timezone.now().date()
            for week in reversed(range(num_weeks)):
                if week == (num_weeks - 1):
                    count = SchoolApplication.objects.filter(
                        school__slug=slug).filter(
                        timestamp__date__range=[
                            from_date, to_date]).count()
                    res["results"].append(
                        {'week': week, 'count': count, 'from': from_date, 'to': to_date})
                else:
                    to_date = from_date - timezone.timedelta(days=1)
                    from_date = from_date - timezone.timedelta(days=7)
                    count = SchoolApplication.objects.filter(
                        school__slug=slug).filter(
                        timestamp__date__range=[
                            from_date, to_date]).count()
                    res["results"].append(
                        {'week': week, 'count': count, 'from': from_date, 'to': to_date})
            return Response(res)
        else:
            error_logger(f"{self.__class__.__name__} Permission Error for userid {request.user.id}")
            res = {"detail": "You do not have permission to perform this action."}
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)


def combined_address(data):
    return str(data.form.short_address)+" "+str(data.form.street_address)+" "+str(data.form.city)+" "+str(data.form.state)+" "+str(data.form.pincode)



class ExcelExportDOEView(APIView):
    permission_classes = [
        IsSchoolOrReadOnly,
    ]
    def get(self, request, format=None):
        apps = SchoolApplication.objects.select_related(
            "child", "form").filter(
            school__pk=self.request.user.current_school)

        if 'apply_for' in request.GET and request.GET.get('apply_for'):
            if request.GET['apply_for'] == '21':
                apps = apps.filter(apply_for__in=['21','12'])
            elif request.GET['apply_for'] == '24':
                apps = apps.filter(apply_for__in=['24','13'])
            else:
                apps = apps.filter(apply_for=request.GET['apply_for'])
        if 'start_date' in request.GET and request.GET.get('start_date'):
            apps = apps.filter(timestamp__date__gte=request.GET['start_date'])
        if 'end_date' in request.GET and request.GET.get('end_date'):
            apps = apps.filter(timestamp__date__lte=request.GET['end_date'])
        if 'session' in request.GET and request.GET.get('session'):
            apps = apps.filter(registration_data__session=request.GET['session'])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="All Forms DOE.csv"'
        writer = csv.DictWriter(
            response,
            fieldnames=[
                'SNo',
                'Schid',
                'StudentName',
                'DateofBirth',
                'Year',
                'Month',
                'Day',
                'ClassApplied',
                'Gender',
                'MotherName',
                'FatherName',
                'ResiAddress',
                'RegistrationNo',
                'Criteria1',
                'Point1',
                'Criteria2',
                'Point2',
                'Criteria3',
                'Point3',
                'Criteria4',
                'Point4',
                'Criteria5',
                'Point5',
                'Criteria6',
                'Point6',
                'Criteria7',
                'Point7',
                'Criteria8',
                'Point8',
                'Criteria9',
                'Point9',
                'Criteria10',
                'Point10',
                'Criteria11',
                'Point11',
                'Criteria12',
                'Point12',
                'Criteria13',
                'Point13',
                'Criteria14',
                'Point14',
                'Criteria15',
                'Point15',
                'Criteria16',
                'Point16',
                'Criteria17',
                'Point17',
                'Criteria18',
                'Point18',
                'Criteria19',
                'Point19',
                'Criteria20',
                'Point20'
                ])
        writer.writeheader()
        count = 1
        for i in apps:
            count =count + 1
            from dateutil.relativedelta import relativedelta
            def child_age(dob):
                applied_year = datetime(year=int(i.registration_data.session.split('-')[0]), month=int('03'), day=int('31')).year
                check_date = timezone.datetime(applied_year, 3, 31).date()
                return relativedelta(check_date,dob)

            def child_age_str(dob):
                total = child_age(dob)
                if total.__nonzero__():
                    return total
                return None

            def dob_format(dob):
                stringDate = str(dob).split('-')
                check_zero = lambda zero_check: int(list(zero_check)[1]) if '0' is int(list(zero_check)[0]) else int(zero_check)

                formated_date = date(int(stringDate[0]),check_zero(stringDate[1]), check_zero(stringDate[2]))
                return formated_date

            value_check = lambda point_check: point_check if point_check else '0'

            if  i.child.orphan:
                half_data = {
                'SNo' : count-1,
                'Schid':'',
                'StudentName':i.registration_data.child_name.title(),
                'DateofBirth': dob_format(i.registration_data.child_date_of_birth),
                'Year':child_age_str(i.registration_data.child_date_of_birth).years,
                'Month':child_age_str(i.registration_data.child_date_of_birth).months,
                'Day':child_age_str(i.registration_data.child_date_of_birth).days,
                # 'ClassApplied':i.apply_for.name,
                'Gender':i.registration_data.child_gender.title(),
                'MotherName':'',
                'FatherName':'',
                'ResiAddress':combined_address(i),
                'RegistrationNo':i.uid,
                }
                for cls in i.school.class_relation.filter():
                    multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(
                        multi_class_relation__id=i.child.class_applying_for.id).first()
                    if multi_obj:
                        if cls.id == i.child.class_applying_for.id:
                            half_data["ClassApplied"] = i.child.class_applying_for.name
                        else:
                            half_data["ClassApplied"] = i.child.class_applying_for.name + "/" + cls.name
                    else:
                        half_data["ClassApplied"] = i.child.class_applying_for.name
                points_data = {}
                school_all_points = SchoolPoint.objects.filter(school=i.school)
                school_distance_point = DistancePoint.objects.filter(school=i.school)
                point_loop_number = 1
                for item in school_distance_point:
                    if not item.point == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = str(item.start) + ' - ' + str(item.end) + ' KM'
                        points_data[key_name] = key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        child_point_for_item = 0
                        if item.point == i.distance_points:
                            child_point_for_item = item.point
                        points_data[key_point_name] = child_point_for_item
                        point_loop_number = point_loop_number + 1

                for item in school_all_points:
                    if not item.single_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_child_points)
                        point_loop_number = point_loop_number + 1
                    if not item.siblings_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Siblings Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.siblings_studied_points)
                        point_loop_number = point_loop_number + 1
                    if not item.parent_alumni_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Parent Alumni Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.parents_alumni_points)
                        point_loop_number = point_loop_number + 1
                    if not item.staff_ward_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Staff Ward Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.staff_ward_points)
                        point_loop_number = point_loop_number + 1
                    if not item.first_born_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'First Born Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.first_born_child_points)
                        point_loop_number = point_loop_number + 1
                    if not item.first_girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'First Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.first_girl_child_points)
                        point_loop_number = point_loop_number + 1
                    if not item.single_girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_girl_child_points)
                        point_loop_number = point_loop_number + 1
                    if not item.is_christian_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Christian Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.christian_points)
                        point_loop_number = point_loop_number + 1
                    if not item.girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.girl_child_point)
                        point_loop_number = point_loop_number + 1
                    if not item.single_parent_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Parent Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_parent_point)
                        point_loop_number = point_loop_number + 1
                    if not item.minority_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Minority Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.minority_points)
                        point_loop_number = point_loop_number + 1
                    if not item.student_with_special_needs_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Children With Special Needs Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.student_with_special_needs_points)
                        point_loop_number = point_loop_number + 1
                    if not item.children_of_armed_force_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Children of Armed Forces Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.children_of_armed_force_points)
                        point_loop_number = point_loop_number + 1
                    if not item.transport_facility_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Transport Facility Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.transport_facility_points)
                        point_loop_number = point_loop_number + 1
                    if not item.state_transfer_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Inter State Transfer Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.state_transfer_points)
                        point_loop_number = point_loop_number + 1

                while point_loop_number <= 20 :
                    key_name = 'Criteria'+str(point_loop_number)
                    points_data[key_name]=''
                    key_point_name = 'Point'+str(point_loop_number)
                    points_data[key_point_name]=''
                    point_loop_number = point_loop_number + 1
                data = half_data.copy()
                data.update(points_data)
                writer.writerow(data)
            else:
                half_data = {
                'SNo' : count-1,
                'Schid':'',
                'StudentName':i.registration_data.child_name.title(),
                'DateofBirth': dob_format(i.registration_data.child_date_of_birth),
                'Year':child_age_str(i.registration_data.child_date_of_birth).years,
                'Month':child_age_str(i.registration_data.child_date_of_birth).months,
                'Day':child_age_str(i.registration_data.child_date_of_birth).days,
                # 'ClassApplied':i.apply_for.name,
                'Gender':i.registration_data.child_gender.title(),
                'MotherName':i.registration_data.father_name.title(),
                'FatherName':i.registration_data.mother_name.title(),
                'ResiAddress':combined_address(i),
                'RegistrationNo':i.uid,
                }
                for cls in i.school.class_relation.filter():
                    multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(
                        multi_class_relation__id=i.child.class_applying_for.id).first()
                    if multi_obj:
                        if cls.id == i.child.class_applying_for.id:
                            half_data["ClassApplied"] = i.child.class_applying_for.name
                        else:
                            half_data["ClassApplied"] = i.child.class_applying_for.name + "/" + cls.name
                    else:
                        half_data["ClassApplied"] = i.child.class_applying_for.name
                points_data = {}
                school_all_points = SchoolPoint.objects.filter(school=i.school)
                school_distance_point = DistancePoint.objects.filter(school=i.school)
                point_loop_number = 1
                for item in school_distance_point:
                    if not item.point == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = str(item.start) + ' - ' + str(item.end) + ' KM'
                        points_data[key_name] = key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        child_point_for_item = 0
                        if item.point == i.distance_points:
                            child_point_for_item = item.point
                        points_data[key_point_name] = child_point_for_item
                        point_loop_number = point_loop_number + 1
                for item in school_all_points:
                    if not item.single_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_child_points)
                        point_loop_number = point_loop_number + 1
                    if not item.siblings_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Siblings Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.siblings_studied_points)
                        point_loop_number = point_loop_number + 1
                    if not item.parent_alumni_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Parent Alumni Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.parents_alumni_points)

                        point_loop_number = point_loop_number + 1
                    if not item.staff_ward_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Staff Ward Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.staff_ward_points)

                        point_loop_number = point_loop_number + 1
                    if not item.first_born_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'First Born Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.first_born_child_points)

                        point_loop_number = point_loop_number + 1
                    if not item.first_girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'First Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.first_girl_child_points)

                        point_loop_number = point_loop_number + 1
                    if not item.single_girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_girl_child_points)

                        point_loop_number = point_loop_number + 1
                    if not item.is_christian_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Christian Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.christian_points)

                        point_loop_number = point_loop_number + 1
                    if not item.girl_child_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Girl Child Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.girl_child_point)

                        point_loop_number = point_loop_number + 1
                    if not item.single_parent_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Single Parent Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.single_parent_point)

                        point_loop_number = point_loop_number + 1
                    if not item.minority_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Minority Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.minority_points)

                        point_loop_number = point_loop_number + 1
                    if not item.student_with_special_needs_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Children With Special Needs Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.student_with_special_needs_points)

                        point_loop_number = point_loop_number + 1
                    if not item.children_of_armed_force_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Children of Armed Forces Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.children_of_armed_force_points)

                        point_loop_number = point_loop_number + 1
                    if not item.transport_facility_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Transport Facility Points'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.transport_facility_points)

                        point_loop_number = point_loop_number + 1
                    if not item.father_covid_vacination_certifiacte_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Father Covid Vaccination Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.father_covid_vacination_certifiacte_points)

                        point_loop_number = point_loop_number + 1
                    if not item.mother_covid_vacination_certifiacte_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Mother Covid Vaccination Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.mother_covid_vacination_certifiacte_points)

                        point_loop_number = point_loop_number + 1
                    if not item.mother_covid_19_frontline_warrior_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Mother Covid19 Frontline Warrior Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.mother_covid_19_frontline_warrior_points)

                        point_loop_number = point_loop_number + 1
                    if not item.father_covid_19_frontline_warrior_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Father Covid19 Frontline Warrior Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.father_covid_19_frontline_warrior_points)

                        point_loop_number = point_loop_number + 1
                    if not item.state_transfer_points == 0:
                        key_name = 'Criteria'+str(point_loop_number)
                        key_value = 'Inter State Transfer Point'
                        points_data[key_name]=key_value
                        key_point_name = 'Point'+str(point_loop_number)
                        points_data[key_point_name]=value_check(i.state_transfer_points)

                        point_loop_number = point_loop_number + 1

                while point_loop_number <= 20:
                    key_name = 'Criteria'+str(point_loop_number)
                    points_data[key_name]=''
                    key_point_name = 'Point'+str(point_loop_number)
                    points_data[key_point_name]=''
                    point_loop_number = point_loop_number + 1
                data = half_data.copy()
                data.update(points_data)
                writer.writerow(data)
        return response


def check_url(obj):
    if obj:
        return obj.url
    else:
        return ""


def check_obj(obj):
    if obj:
        return obj.name
    else:
        return ""

def get_category(obj):
    if 'category' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.category
    else:
        return ''

def get_bloodgrp(obj):
    if 'blood_group' in obj.school.required_child_fields.keys():
        return obj.registration_data.child_blood_group
    else:
        return ''

def get_family_photo(obj):
    if 'family_photo' in  obj.school.required_admission_form_fields.keys():
        if obj.registration_data.family_photo:
            return obj.registration_data.family_photo.url
    else:
        return ''

def get_transfer_date(obj):
    if 'transfer_date' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.transfer_date
    else:
        return ''

def get_transfer_no(obj):
    if 'transfer_number' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.transfer_date
    else:
        return ''

def get_last_school_name(obj):
    if 'last_school_name' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.last_school_name
    else:
        return ''

def get_last_school_board(obj):
    if 'last_school_board' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.last_school_board:
            return obj.registration_data.last_school_board.name
    else:
        return ''

def get_last_school_class(obj):
    if 'last_school_class' in  obj.school.required_admission_form_fields.keys():
        if obj.registration_data.last_school_class:
            return obj.registration_data.last_school_class.name
    else:
        return ''

def get_last_school_address(obj):
    if 'last_school_address' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.last_school_address
    else:
        return ''

def get_transfer_certificate(obj):
    if 'transfer_certificate' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.transfer_certificate:
            return obj.registration_data.transfer_certificate.url
    else:
        return ''

def get_reason_of_leaving(obj):
    if 'reason_of_leaving' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.reason_of_leaving
    else:
        return ''

def get_report_card(obj):
    if 'report_card' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.report_card:
            return obj.registration_data.report_card.url
    else:
        return ''

def get_last_school_percentage(obj):
    if 'last_school_result_percentage' in obj.school.required_admission_form_fields.keys():
        return obj.registration_data.last_school_result_percentage
    else:
        return ''

def get_distance_affidavit(obj):
    if 'distance_affidavit' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.distance_affidavit:
            return obj.registration_data.distance_affidavit.url
    else:
        return ''

def get_baptism_certificate(obj):
    if 'baptism_certificate' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.baptism_certificate:
            return obj.registration_data.baptism_certificate.url
    else:
        return ''

def get_parent_sign(obj):
    if 'parent_signature_upload' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.baptism_certificate:
            return obj.registration_data.parent_signature_upload.url
    else:
        return ''

def get_differently_abled_proof(obj):
    if 'differently_abled_proof' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.differently_abled_proof:
            return obj.registration_data.differently_abled_proof.url
        else:
            return ''

def get_cast_category_certificate(obj):
    if 'caste_category_certificate' in obj.school.required_admission_form_fields.keys():
        if obj.registration_data.caste_category_certificate:
            return obj.registration_data.caste_category_certificate.url
        else:
            return ''

def get_child_addhar_no(obj):
    if 'blood_group' in obj.school.required_child_fields.keys():
        return obj.registration_data.child_blood_group
    else:
        return ''


def get_child_addhar_no(obj):
    if 'aadhaar_card_number' in obj.school.required_child_fields.keys():
        return obj.registration_data.child_aadhaar_number
    else:
        return ''

def get_vaccination_card(obj):
    if 'vaccination_card' in obj.school.required_child_fields.keys():
        if obj.registration_data.child_vaccination_card:
            return obj.registration_data.child_vaccination_card.url
    else:
        return ''

def get_child_addhar_card_proof(obj):
    if 'aadhaar_card_proof' in obj.school.required_child_fields.keys():
        if obj.registration_data.child_aadhaar_card_proof:
            return obj.registration_data.child_aadhaar_card_proof.url
    else:
        return ''

def get_child_minoriy_proof(obj):
    if 'child minority proof' in obj.school.required_child_fields.keys():
        if obj.registration_data.child_minority_proof:
            return obj.registration_data.child_minority_proofs.url
    else:
        return ''

def get_child_first_child_affidavit(obj):
    if 'first_child_affidavit' in obj.school.required_child_fields.keys():
        if obj.registration_data.child_minority_proof:
            return obj.registration_data.first_child_affidavit.url
    else:
        return ''

def get_staff_ward_status(staff,parent_ward_school,school):
    if 'staff_ward' in school.required_admission_form_fields.keys():
        if staff and parent_ward_school == school:
            return 'Yes'
        else:
            return ''
    else:
        return ''

def get_staff_ward_department(staff,parent_ward_school,school,department):
    if 'staff_ward' in school.required_admission_form_fields.keys():
        if staff and parent_ward_school == school:
            return department
        else:
            return ''
    else:
        return ''

def get_staff_ward_tenure(staff,parent_ward_school,school,tenure):
    if 'staff_ward' in school.required_admission_form_fields.keys():
        if staff and parent_ward_school == school:
            return tenure
        else:
            return ''
    else:
        return ''

def get_staff_ward_type(staff,parent_ward_school,school,type):
    if 'staff_ward' in school.required_admission_form_fields.keys():
        if staff and parent_ward_school == school:
            return type
        else:
            return ''
    else:
        return ''

class ExcelExportAllView(APIView):
    permission_classes = [
        IsSchoolOrReadOnly,
    ]

    def get(self, request, format=None):
        apps = SchoolApplication.objects.select_related(
            "child", "form", "registration_data").filter(
            school__pk=self.request.user.current_school)

        if 'apply_for' in request.GET and request.GET.get('apply_for'):
            if request.GET['apply_for'] == '21':
                apps = apps.filter(apply_for__in=['21','12'])
            elif request.GET['apply_for'] == '24':
                apps = apps.filter(apply_for__in=['24','13'])
            else:
                apps = apps.filter(apply_for=request.GET['apply_for'])
        if 'start_date' in request.GET and request.GET.get('start_date'):
            apps = apps.filter(timestamp__date__gte=request.GET['start_date'])
        if 'end_date' in request.GET and request.GET.get('end_date'):
            apps = apps.filter(timestamp__date__lte=request.GET['end_date'])
        if 'session' in request.GET and request.GET.get('session'):
            apps = apps.filter(registration_data__session=request.GET['session'])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="All Forms List.csv"'
        writer = csv.DictWriter(
            response,
            fieldnames=[
                'Form Id',
                'Session',
                'Date Received',
                'Points',
                'Distance Points',
                "Single Child Points",
                "First Born Child Points",
                'Siblings Points',
                "Christian Child Points",
                "Parent Alumni Points",
                "Staff Ward Points",
                "Single Girl Child Points",
                "First Girl Child Points",
                "Girl Child Points",
                "Single Parent Points",
                "Minority Points",
                "Children of Armed Forces Points",
                "Children With Special Needs Points",
                "Transport Facility Points",
                'Name',
                "Applying For",
                "Date of Birth",
                "Child Age",
                'Short Address',
                'Address',
                'City',
                'State',
                'Zipcode',
                'Combined Address',
                'Gender',
                'Category',
                'Email',
                'Phone No',
                'Blood Group',
                'Religion',
                'Nationality',
                'Father\'s Name',
                'Father\'s Age',
                'Father\'s Phone No',
                'Father\'s Email',
                'Guardian\'s Name',
                'Guardian\'s Age',
                'Guardian\'s Phone No',
                'Guardian\'s Email',
                'Mother\'s Name',
                'Mother\'s Age',
                'Mother\'s Phone No',
                'Mother\'s Email',
                'Father\'s Photo',
                'Guardian\'s Photo',
                'Mother\'s Photo',
                'Child\'s Photo',
                'Child\'s Aadhaar number',
                'Child\'s Aadhaar Proof',
                'Child\'s blood Group',
                'Child\'s Birth certificate',
                'Childs\'s Address proof',
                'Childs\'s Address proof2',
                'First child affidavit',
                'Childs\'s Vaccination card',
                'Minority proof',
                'Sibling1 Alumni Name',
                'Sibling1 Alumni School Name',
                'Sibling2 Alumni Name',
                'Sibling2 Alumni School Name',
                'Sibling1 Alumni Proof',
                'Sibling2 Alumni Proof',

                'family_photo',
                'Distance_affidavit',
                'Baptism_certificate',
                'Parent_signature_upload',
                'Differently_abled_proof',
                'Caste_category_certificate',
                'Transport_facility_required',
                'Father\'s Company Name',
                'Father\'s Aadhaar Number',
                'Father\'s Transferable Job',
                'Father\'s Special Ground',
                'Father\'s Designation',
                "Father\'s Profession",
                "Father\'s Special Ground proof",
                "Father\'s aadhar card",
                "Father\'s Pan_card_proof",
                "Father\'s Income",
                "Father\'s Bio",
                "Father\'s Education",
                "Father\'s Institue",
                "Father\'s Course",
                "Father\'s Occupation",
                "Father\'s Office_address",
                "Father\'s Office_number",
                "Father\'s Alumni_school_name",
                "Father\'s Alumni_year_of_passing",
                "Father\'s Passing_class",
                "Father\'s Alumni_proof",
                "Father\'s Staff Ward",
                "Father\'s Staff Ward Department",
                "Father\'s Type of Staff Ward ",
                "Father\'s Staff Ward Tenure",
                'Mother\'s Company Name',
                'Mother\'s Aadhaar Number',
                'Mother\'s Transferable Job',
                'Mother\'s Special Ground',
                'Mother\'s Designation',
                "Mother\'s Profession",
                "Mother\'s Special Ground proof",
                "Mother\'s Parent aadhar card",
                "Mother\'s Pan_card_proof",
                "Mother\'s Income",
                "Mother\'s Bio",
                "Mother\'s Education",
                "Mother\'s Institue",
                "Mother\'s Course",
                "Mother\'s Occupation",
                "Mother\'s Office_address",
                "Mother\'s Office_number",
                "Mother\'s Alumni_school_name",
                "Mother\'s Alumni_year_of_passing",
                "Mother\'s Passing_class",
                "Mother\'s Alumni_proof",
                "Mother\'s Staff Ward",
                "Mother\'s Staff Ward Department",
                "Mother\'s Type of Staff Ward ",
                "Mother\'s Staff Ward Tenure",
                'Guardian\'s Company Name',
                'Guardian\'s Aadhaar Number',
                'Guardian\'s Transferable Job',
                'Guardian\'s Special Ground',
                'Guardian\'s Designation',
                "Guardian\'s Profession",
                "Guardian\'s Special Ground proof",
                "Guardian\'s Parent aadhar card",
                "Guardian\'s Pan_card_proof",
                "Guardian\'s Income",
                "Guardian\'s Bio",
                "Guardian\'s Education",
                "Guardian\'s Institue",
                "Guardian\'s Course",
                "Guardian\'s Occupation",
                "Guardian\'s Office_address",
                "Guardian\'s Office_number",
                "Guardian\'s Alumni_school_name",
                "Guardian\'s Alumni_year_of_passing",
                "Guardian\'s Passing_class",
                "Guardian\'s Alumni_proof",
                "Guardian\'s Staff Ward",
                "Guardian\'s Staff Ward Department",
                "Guardian\'s Type of Staff Ward ",
                "Guardian\'s Staff Ward Tenure",
                "Last School Name",
                "Last School board",
                "last school_address",
                "last school_class",
                "transfer certificate",
                "reason of leaving",
                "report card",
                "last school result percentage",
                "transfer number",
                "transfer date",
                ])
        writer.writeheader()

        for i in apps:
            half_data = {}
            if i.child.orphan:
                for cls in i.school.class_relation.filter():
                    multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(
                        multi_class_relation__id=i.apply_for.id).first()
                    if multi_obj:
                        if cls.id == i.apply_for.id:
                            half_data["ClassApplied"] = i.apply_for.name
                        else:
                            half_data["ClassApplied"] = i.apply_for.name + "/" + cls.name
                    else:
                        half_data["ClassApplied"] = i.apply_for.name
                writer.writerow({
                'Form Id':i.uid,
                'Date Received':i.timestamp,
                'Session':i.registration_data.session,
                "Applying For": half_data["ClassApplied"],
                "Points": i.total_points,
                'Distance Points': i.distance_points,
                "Single Child Points": i.single_child_points,
                "First Born Child Points": i.first_born_child_points,
                'Siblings Points': i.siblings_studied_points,
                "Christian Child Points": i.christian_points,
                "Parent Alumni Points": i.parents_alumni_points,
                "Staff Ward Points": i.staff_ward_points,
                "Single Girl Child Points": i.single_girl_child_points,
                "First Girl Child Points": i.first_girl_child_points,
                "Girl Child Points": i.girl_child_point,
                "Single Parent Points": i.single_parent_point,
                "Minority Points": i.minority_points,
                "Children of Armed Forces Points": i.children_of_armed_force_points,
                "Children With Special Needs Points": i.student_with_special_needs_points,
                "Transport Facility Points": i.transport_facility_points,

                'Name':i.registration_data.child_name,
                # "Applying For":i.apply_for.name,
                "Date of Birth":i.registration_data.child_date_of_birth,
                "Child Age":i.registration_data.child_age_str,
                'Short Address':i.registration_data.short_address,
                'Address':i.registration_data.street_address,
                'City':i.registration_data.city,
                'State':i.registration_data.state,
                'Zipcode':i.registration_data.pincode,
                'Combined Address':combined_address(i),
                'Gender':i.registration_data.child_gender,
                'Category':get_category(i),
                'Email':i.registration_data.user.email,
                'Phone No':i.registration_data.father_phone,
                'Blood Group':get_bloodgrp(i),
                'Religion':i.registration_data.child_religion,
                'Nationality':i.registration_data.child_nationality,

                'Child\'s Photo':check_url(i.registration_data.child_photo),
                'Child\'s Aadhaar number':get_child_addhar_no(i),
                'Child\'s Aadhaar Proof':get_child_addhar_card_proof(i),
                'Child\'s blood Group':i.registration_data.child_blood_group,
                'Child\'s Birth certificate':i.registration_data.child_birth_certificate,
                'Childs\'s Address proof':i.registration_data.child_address_proof,
                'Childs\'s Address proof2':i.registration_data.child_address_proof2,
                'First child affidavit':get_child_first_child_affidavit(i),
                'Childs\'s Vaccination card':get_vaccination_card(i),

                'Minority proof':get_child_minoriy_proof(i),
                'Sibling1 Alumni Name':i.registration_data.sibling1_alumni_name,
                'Sibling1 Alumni School Name':check_obj(i.registration_data.sibling1_alumni_school_name),
                'Sibling2 Alumni Name':i.registration_data.sibling2_alumni_name,
                'Sibling2 Alumni School Name':check_obj(i.registration_data.sibling2_alumni_school_name),
                'Sibling1 Alumni Proof':check_url(i.registration_data.sibling1_alumni_proof),
                'Sibling2 Alumni Proof':check_url(i.registration_data.sibling2_alumni_proof),

                'family_photo':get_family_photo(i),
                'Distance_affidavit':get_distance_affidavit(i),
                'Baptism_certificate':get_baptism_certificate(i),
                'Parent_signature_upload':get_parent_sign(i),
                'Differently_abled_proof':get_differently_abled_proof(i),
                'Caste_category_certificate':get_cast_category_certificate(i),
                'Transport_facility_required':i.registration_data.transport_facility_required,
                "Last School Name":get_last_school_name(i),
                "Last School board":get_last_school_board(i),
                "last school_address":get_last_school_address(i),
                "last school_class":get_last_school_class(i),
                "transfer certificate":get_transfer_certificate(i),
                "reason of leaving":get_reason_of_leaving(i),
                "report card":get_report_card(i),
                "last school result percentage":get_last_school_percentage(i),
                "transfer number":get_transfer_no(i),
                "transfer date":get_transfer_date(i),

                # 'Father\'s Name':i.registration_data.father_name,
                # 'Father\'s Age':i.registration_data.father_age,
                # 'Father\'s Phone No':i.registration_data.father_phone,
                # 'Father\'s Email':i.registration_data.father_email,
                # 'Father\'s Photo':check_url(i.registration_data.father_photo),
                # 'Father\'s Company Name':i.registration_data.father_companyname,
                # 'Father\'s Aadhaar Number':i.registration_data.father_aadhaar_number,
                # 'Father\'s Transferable Job':i.registration_data.father_transferable_job,
                # 'Father\'s Special Ground':i.registration_data.father_special_ground,
                # 'Father\'s Designation':i.registration_data.father_designation,
                # "Father\'s Profession":i.registration_data.father_profession,
                # "Father\'s Special Ground proof":check_url(i.registration_data.father_special_ground_proof),
                # "Father\'s aadhar card":check_url(i.registration_data.father_parent_aadhar_card),
                # "Father\'s Pan_card_proof":check_url(i.registration_data.father_pan_card_proof),
                # "Father\'s Income":i.registration_data.father_income,
                # "Father\'s Bio":i.registration_data.father_bio,
                # "Father\'s Education":i.registration_data.father_education,
                # "Father\'s Occupation":i.registration_data.father_occupation,
                # "Father\'s Office_address":i.registration_data.father_office_address,
                # "Father\'s Office_number":i.registration_data.father_office_number,
                # "Father\'s Alumni_school_name":i.registration_data.father_alumni_school_name,
                # "Father\'s Alumni_year_of_passing":i.registration_data.father_alumni_year_of_passing,
                # "Father\'s Passing_class":i.registration_data.father_passing_class,
                # "Father\'s Alumni_proof":check_url(i.registration_data.father_alumni_proof),

                # 'Mother\'s Name':i.registration_data.mother_name,
                # 'Mother\'s Age':i.registration_data.mother_age,
                # 'Mother\'s Phone No':i.registration_data.mother_phone,
                # 'Mother\'s Email':i.registration_data.mother_email,
                # 'Mother\'s Photo':check_url(i.registration_data.mother_photo),
                # 'Mother\'s Company Name':i.registration_data.mother_companyname,
                # 'Mother\'s Aadhaar Number':i.registration_data.mother_aadhaar_number,
                # 'Mother\'s Transferable Job':i.registration_data.mother_transferable_job,
                # 'Mother\'s Special Ground':i.registration_data.mother_special_ground,
                # 'Mother\'s Designation':i.registration_data.mother_designation,
                # "Mother\'s Profession":i.registration_data.mother_profession,
                # "Mother\'s Special Ground proof":check_url(i.registration_data.mother_special_ground_proof),
                # "Mother\'s aadhar card":check_url(i.registration_data.mother_parent_aadhar_card),
                # "Mother\'s Pan_card_proof":check_url(i.registration_data.mother_pan_card_proof),
                # "Mother\'s Income":i.registration_data.mother_income,
                # "Mother\'s Bio":i.registration_data.mother_bio,
                # "Mother\'s Education":i.registration_data.mother_education,
                # "Mother\'s Occupation":i.registration_data.mother_occupation,
                # "Mother\'s Office_address":i.registration_data.mother_office_address,
                # "Mother\'s Office_number":i.registration_data.mother_office_number,
                # "Mother\'s Alumni_school_name":i.registration_data.mother_alumni_school_name,
                # "Mother\'s Alumni_year_of_passing":i.registration_data.mother_alumni_year_of_passing,
                # "Mother\'s Passing_class":i.registration_data.mother_passing_class,
                # "Father\'s Alumni_proof":check_url(i.registration_data.mother_alumni_proof),




                'Guardian\'s Name':i.registration_data.guardian_name,
                'Guardian\'s Age':i.registration_data.guardian_age,
                'Guardian\'s Phone No':i.registration_data.guardian_phone,
                'Guardian\'s Email': i.registration_data.guardian_email,
                'Guardian\'s Photo': check_url(i.registration_data.guardian_photo),
                'Guardian\'s Company Name': i.registration_data.guardian_companyname,
                'Guardian\'s Aadhaar Number':  i.registration_data.guardian_aadhaar_number,
                'Guardian\'s Transferable Job':i.registration_data.guardian_transferable_job,
                'Guardian\'s Special Ground':i.registration_data.guardian_special_ground,
                'Guardian\'s Designation':i.registration_data.guardian_designation,
                "Guardian\'s Profession":i.registration_data.guardian_profession,
                "Guardian\'s Special Ground proof":check_url(i.registration_data.guardian_special_ground_proof),
                "Guardian\'s Parent aadhar card":check_url(i.registration_data.guardian_parent_aadhar_card),
                "Guardian\'s Pan_card_proof":check_url(i.registration_data.guardian_pan_card_proof),
                "Guardian\'s Income":i.registration_data.guardian_income,
                "Guardian\'s Bio":i.registration_data.guardian_bio,
                "Guardian\'s Education":i.registration_data.guardian_education,
                "Guardian\'s Institue":i.registration_data.guardian_college_name,
                "Guardian\'s Course":i.registration_data.guardian_course_name,
                "Guardian\'s Occupation":i.registration_data.guardian_education,
                "Guardian\'s Office_address":i.registration_data.guardian_office_address,
                "Guardian\'s Office_number":i.registration_data.guardian_office_number,
                "Guardian\'s Alumni_school_name":i.registration_data.guardian_alumni_school_name,
                "Guardian\'s Alumni_year_of_passing":i.registration_data.guardian_alumni_year_of_passing,
                "Guardian\'s Passing_class":i.registration_data.guardian_passing_class,
                "Guardian\'s Alumni_proof":check_url(i.registration_data.guardian_alumni_proof),
                "Guardian\'s Staff Ward": get_staff_ward_status(i.registration_data.staff_ward,i.registration_data.guardian_staff_ward_school_name, i.school),
                "Guardian\'s Staff Ward Department":get_staff_ward_department(i.registration_data.staff_ward,i.registration_data.guardian_staff_ward_school_name, i.school,i.registration_data.guardian_staff_ward_department),
                "Guardian\'s Type of Staff Ward ":get_staff_ward_type(i.registration_data.staff_ward,i.registration_data.guardian_staff_ward_school_name, i.school,i.registration_data.guardian_type_of_staff_ward),
                "Guardian\'s Staff Ward Tenure":get_staff_ward_tenure(i.registration_data.staff_ward,i.registration_data.guardian_staff_ward_school_name, i.school,i.registration_data.guardian_staff_ward_tenure)
                })

            else:
                for cls in i.school.class_relation.filter():
                    multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(
                        multi_class_relation__id=i.apply_for.id).first()
                    if multi_obj:
                        if cls.id == i.apply_for.id:
                            half_data["ClassApplied"] = i.apply_for.name
                        else:
                            half_data["ClassApplied"] = i.apply_for.name + "/" + cls.name
                    else:
                        half_data["ClassApplied"] = i.apply_for.name
                writer.writerow({
                'Form Id':i.uid,
                'Date Received':i.timestamp,
                'Session':i.registration_data.session,
                "Applying For": half_data["ClassApplied"],
                "Points": i.total_points,
                'Distance Points': i.distance_points,
                "Single Child Points": i.single_child_points,
                "First Born Child Points": i.first_born_child_points,
                'Siblings Points': i.siblings_studied_points,
                "Christian Child Points": i.christian_points,
                "Parent Alumni Points": i.parents_alumni_points,
                "Staff Ward Points": i.staff_ward_points,
                "Single Girl Child Points": i.single_girl_child_points,
                "First Girl Child Points": i.first_girl_child_points,
                "Girl Child Points": i.girl_child_point,
                "Single Parent Points": i.single_parent_point,
                "Minority Points": i.minority_points,
                "Children of Armed Forces Points": i.children_of_armed_force_points,
                "Children With Special Needs Points": i.student_with_special_needs_points,
                "Transport Facility Points": i.transport_facility_points,

                'Name':i.registration_data.child_name,
                # "Applying For":i.apply_for.name,
                "Date of Birth":i.registration_data.child_date_of_birth,
                "Child Age":i.registration_data.child_age_str,
                'Short Address':i.registration_data.short_address,
                'Address':i.registration_data.street_address,
                'City':i.registration_data.city,
                'State':i.registration_data.state,
                'Zipcode':i.registration_data.pincode,
                'Combined Address':combined_address(i),
                'Gender':i.registration_data.child_gender,
                'Category':get_category(i),
                'Email':i.registration_data.user.email,
                'Phone No':i.registration_data.father_phone,
                'Blood Group':get_bloodgrp(i),
                'Religion':i.registration_data.child_religion,
                'Nationality':i.registration_data.child_nationality,

                'Child\'s Photo':check_url(i.registration_data.child_photo),
                'Child\'s Aadhaar number':get_child_addhar_no(i),
                'Child\'s Aadhaar Proof':get_child_addhar_card_proof(i),
                'Child\'s blood Group':i.registration_data.child_blood_group,
                'Child\'s Birth certificate':i.registration_data.child_birth_certificate,
                'Childs\'s Address proof':i.registration_data.child_address_proof,
                'Childs\'s Address proof2':i.registration_data.child_address_proof2,
                'First child affidavit':get_child_first_child_affidavit(i),
                'Childs\'s Vaccination card':get_vaccination_card(i),

                'Minority proof':get_child_minoriy_proof(i),
                'Sibling1 Alumni Name':i.registration_data.sibling1_alumni_name,
                'Sibling1 Alumni School Name':check_obj(i.registration_data.sibling1_alumni_school_name),
                'Sibling2 Alumni Name':i.registration_data.sibling2_alumni_name,
                'Sibling2 Alumni School Name':check_obj(i.registration_data.sibling2_alumni_school_name),
                'Sibling1 Alumni Proof':check_url(i.registration_data.sibling1_alumni_proof),
                'Sibling2 Alumni Proof':check_url(i.registration_data.sibling2_alumni_proof),

                'family_photo':get_family_photo(i),
                'Distance_affidavit':get_distance_affidavit(i),
                'Baptism_certificate':get_baptism_certificate(i),
                'Parent_signature_upload':get_parent_sign(i),
                'Differently_abled_proof':get_differently_abled_proof(i),
                'Caste_category_certificate':get_cast_category_certificate(i),
                'Transport_facility_required':i.registration_data.transport_facility_required,
                "Last School Name":get_last_school_name(i),
                "Last School board":get_last_school_board(i),
                "last school_address":get_last_school_address(i),
                "last school_class":get_last_school_class(i),
                "transfer certificate":get_transfer_certificate(i),
                "reason of leaving":get_reason_of_leaving(i),
                "report card":get_report_card(i),
                "last school result percentage":get_last_school_percentage(i),
                "transfer number":get_transfer_no(i),
                "transfer date":get_transfer_date(i),

                'Father\'s Name':i.registration_data.father_name,
                'Father\'s Age':i.registration_data.father_age,
                'Father\'s Phone No':i.registration_data.father_phone,
                'Father\'s Email':i.registration_data.father_email,
                'Father\'s Photo':check_url(i.registration_data.father_photo),
                'Father\'s Company Name':i.registration_data.father_companyname,
                'Father\'s Aadhaar Number':i.registration_data.father_aadhaar_number,
                'Father\'s Transferable Job':i.registration_data.father_transferable_job,
                'Father\'s Special Ground':i.registration_data.father_special_ground,
                'Father\'s Designation':i.registration_data.father_designation,
                "Father\'s Profession":i.registration_data.father_profession,
                "Father\'s Special Ground proof":check_url(i.registration_data.father_special_ground_proof),
                "Father\'s aadhar card":check_url(i.registration_data.father_parent_aadhar_card),
                "Father\'s Pan_card_proof":check_url(i.registration_data.father_pan_card_proof),
                "Father\'s Income":i.registration_data.father_income,
                "Father\'s Bio":i.registration_data.father_bio,
                "Father\'s Education":i.registration_data.father_education,
                "Father\'s Institue":i.registration_data.father_college_name,
                "Father\'s Course":i.registration_data.father_course_name,
                "Father\'s Occupation":i.registration_data.father_occupation,
                "Father\'s Office_address":i.registration_data.father_office_address,
                "Father\'s Office_number":i.registration_data.father_office_number,
                "Father\'s Alumni_school_name":i.registration_data.father_alumni_school_name,
                "Father\'s Alumni_year_of_passing":i.registration_data.father_alumni_year_of_passing,
                "Father\'s Passing_class":i.registration_data.father_passing_class,
                "Father\'s Alumni_proof":check_url(i.registration_data.father_alumni_proof),
                "Father\'s Staff Ward": get_staff_ward_status(i.registration_data.staff_ward,i.registration_data.father_staff_ward_school_name, i.school),
                "Father\'s Staff Ward Department": get_staff_ward_department(i.registration_data.staff_ward,i.registration_data.father_staff_ward_school_name, i.school,i.registration_data.father_staff_ward_department),
                "Father\'s Type of Staff Ward ": get_staff_ward_type(i.registration_data.staff_ward,i.registration_data.father_staff_ward_school_name, i.school,i.registration_data.father_type_of_staff_ward),
                "Father\'s Staff Ward Tenure": get_staff_ward_tenure(i.registration_data.staff_ward,i.registration_data.father_staff_ward_school_name, i.school,i.registration_data.father_staff_ward_tenure),

                'Mother\'s Name':i.registration_data.mother_name,
                'Mother\'s Age':i.registration_data.mother_age,
                'Mother\'s Phone No':i.registration_data.mother_phone,
                'Mother\'s Email':i.registration_data.mother_email,
                'Mother\'s Photo':check_url(i.registration_data.mother_photo),
                'Mother\'s Company Name':i.registration_data.mother_companyname,
                'Mother\'s Aadhaar Number':i.registration_data.mother_aadhaar_number,
                'Mother\'s Transferable Job':i.registration_data.mother_transferable_job,
                'Mother\'s Special Ground':i.registration_data.mother_special_ground,
                'Mother\'s Designation':i.registration_data.mother_designation,
                "Mother\'s Profession":i.registration_data.mother_profession,
                "Mother\'s Special Ground proof":check_url(i.registration_data.mother_special_ground_proof),
                "Mother\'s Parent aadhar card":check_url(i.registration_data.mother_parent_aadhar_card),
                "Mother\'s Pan_card_proof":check_url(i.registration_data.mother_pan_card_proof),
                "Mother\'s Income":i.registration_data.mother_income,
                "Mother\'s Bio":i.registration_data.mother_bio,
                "Mother\'s Education":i.registration_data.mother_education,
                "Mother\'s Occupation":i.registration_data.mother_occupation,
                "Mother\'s Office_address":i.registration_data.mother_office_address,
                "Mother\'s Office_number":i.registration_data.mother_office_number,
                "Mother\'s Alumni_school_name":i.registration_data.mother_alumni_school_name,
                "Mother\'s Alumni_year_of_passing":i.registration_data.mother_alumni_year_of_passing,
                "Mother\'s Passing_class":i.registration_data.mother_passing_class,
                "Mother\'s Alumni_proof":check_url(i.registration_data.mother_alumni_proof),
                "Mother\'s Staff Ward": get_staff_ward_status(i.registration_data.staff_ward,i.registration_data.mother_staff_ward_school_name, i.school),
                "Mother\'s Staff Ward Department": get_staff_ward_department(i.registration_data.staff_ward,i.registration_data.mother_staff_ward_school_name, i.school,i.registration_data.mother_staff_ward_department),
                "Mother\'s Type of Staff Ward ": get_staff_ward_type(i.registration_data.staff_ward,i.registration_data.mother_staff_ward_school_name, i.school,i.registration_data.mother_type_of_staff_ward),
                "Mother\'s Staff Ward Tenure": get_staff_ward_tenure(i.registration_data.staff_ward,i.registration_data.mother_staff_ward_school_name, i.school,i.registration_data.mother_staff_ward_tenure),




                # 'Guardian\'s Name':i.registration_data.guardian_name,
                # 'Guardian\'s Age':i.registration_data.guardian_age,
                # 'Guardian\'s Phone No':i.registration_data.guardian_phone,
                # 'Guardian\'s Email': i.registration_data.guardian_email,
                # 'Guardian\'s Photo': check_url(i.registration_data.guardian_photo),
                # 'Guardian\'s Company Name': i.registration_data.guardian_companyname,
                # 'Guardian\'s Aadhaar Number':  i.registration_data.guardian_aadhaar_number,
                # 'Guardian\'s Transferable Job':i.registration_data.guardian_transferable_job,
                # 'Guardian\'s Special Ground':i.registration_data.guardian_special_ground,
                # 'Guardian\'s Designation':i.registration_data.guardian_designation,
                # "Guardian\'s Profession":i.registration_data.guardian_profession,
                # "Guardian\'s Special Ground proof":check_url(i.registration_data.guardian_special_ground_proof),
                # "Guardian\'s Parent aadhar card":check_url(i.registration_data.guardian_parent_aadhar_card),
                # "Guardian\'s Pan_card_proof":check_url(i.registration_data.guardian_pan_card_proof),
                # "Guardian\'s Income":i.registration_data.guardian_income,
                # "Guardian\'s Bio":i.registration_data.guardian_bio,
                # "Guardian\'s Education":i.registration_data.guardian_education,
                # "Guardian\'s Occupation":i.registration_data.guardian_education,
                # "Guardian\'s Office_address":i.registration_data.guardian_office_address,
                # "Guardian\'s Office_number":i.registration_data.guardian_office_number,
                # "Guardian\'s Alumni_school_name":i.registration_data.guardian_alumni_school_name,
                # "Guardian\'s Alumni_year_of_passing":i.registration_data.guardian_alumni_year_of_passing,
                # "Guardian\'s Passing_class":i.registration_data.guardian_passing_class,
                # "Guardian\'s Alumni_proof":check_url(i.registration_data.guardian_alumni_proof),
                })
        return response


class SchoolCodeFetch(APIView):
    permission_classes = [IsSchool]

    def post(self, request):
        school = SchoolProfile.objects.get(pk=request.user.current_school)
        serializer = serializers.SchoolCodeSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            code = data["code"]
            if SchoolVerificationCode.objects.filter(
                    code=code, active=False).exists():
                d = SchoolVerificationCode.objects.get(code=code, active=False)
                data = serializers.SchoolCodeSerializer(d).data
                return Response(data, status=status.HTTP_200_OK)
            else:
                error_logger(f"{self.__class__.__name__} Not Found for code {code} userid {request.user.id}")
                return Response({"detail": "Not found."},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            error_logger(f"{self.__class__.__name__} Serializer Invalid for userid {request.user.id}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class SchoolCodeVerify(APIView):
    permission_classes = [IsSchool]

    def post(self, request):
        school = SchoolProfile.objects.get(user=request.user)
        serializer = serializers.SchoolCodeSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            code = data["code"]
            d = SchoolVerificationCode.objects.get(code=code)
            school.is_verified = True
            school.save()
            d.active = True
            d.save()
            info_logger(f"{self.__class__.__name__} Account Activated for userid {request.user.id}")
            return Response(
                {"status": "Account activated successfully!"}, status=status.HTTP_200_OK)
        else:
            error_logger(f"{self.__class__.__name__} Serializer Invalid for userid {request.user.id}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class SchoolCodeRequest(APIView):
    permission_classes = [IsSchool]

    def post(self, request):
        school = SchoolProfile.objects.get(user=request.user)
        send_school_code_request_mail.delay(school.id)
        return Response({}, status=status.HTTP_200_OK)


class FeaturedSchoolListView(generics.ListAPIView):
    serializer_class = serializers.FeaturedSchoolSerializer

    def get_queryset(self):
        return SchoolProfile.objects.only(
            "name", "slug", "logo", "city").filter(
            is_featured=True).annotate(
            views_count=Count("views")).order_by("-views_count")


class SchoolProfileSitemapData(APIView):
    def get(self, request, format=False):
        data = list(SchoolProfile.objects.filter(is_verified=True,
                                                 is_active=True).values_list("slug", flat=True))
        return Response(data, status=status.HTTP_200_OK)


class ActivityTypeAutocompleteView(generics.ListAPIView):
    serializer_class = serializers.ActivityTypeAutocompleteSerializer
    queryset = ActivityTypeAutocomplete.objects.all()


class ActivityAutocompleteView(generics.ListAPIView):
    serializer_class = serializers.ActivityAutocompleteSerializer
    queryset = ActivityAutocomplete.objects.all()
    filterset_fields = ["activity_type", "name"]


class AgeCriteriaView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    # permission_classes = [IsSchoolOrReadOnly, ]
    filterset_class = AgeCiteriaFilter

    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = AgeCriteria.objects.filter(school=school).select_related(
            "class_relation").order_by("class_relation__rank")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.AgeCriteriaSerializer
        if self.request.method == "POST":
            return serializers.AgeCriteriaCreateUpdateSerializer


class AgeCriteriaDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasSchoolObjectPermission, ]

    def get_queryset(self):
        school = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        queryset = AgeCriteria.objects.filter(school=school).select_related(
            "class_relation").order_by("class_relation__rank")
        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.AgeCriteriaSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.AgeCriteriaCreateUpdateSerializer

class SGCLASS(BasePermission):
     def has_permission(self, request, view):
        # if (request.META['HTTP_X_REAL_IP'] == '15.207.216.11') or request.user.is_authenticated:
        #    return True
        f= open("myfile.txt", "w")
        f.write(str(request.headers))
        return True



class SchoolDocumentView(DocumentViewSet):
    permission_classes = [SGCLASS]
    document = SchoolProfileDocument
    serializer_class = SchoolDocumentSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
    #    FacetedSearchFilterBackend,
        DefaultOrderingFilterBackend,
        NestedFilteringFilterBackend,
        GeoSpatialFilteringFilterBackend,
        GeoSpatialOrderingFilterBackend,
        CompoundSearchFilterBackend,
        HighlightBackend,
        SuggesterFilterBackend,
        IdsFilterBackend
    ]
    lookup_field = 'id'
    search_fields = {
        "name": {"fuzziness": "4"},
        "school_city":{"fuzziness": "4"}
    }
    nested_filter_fields = {
       "fee_price": {
           "field": "school_fee_structure.fee_price",
           "path": "school_fee_structure",
           "lookups":[
               LOOKUP_QUERY_GTE,
               LOOKUP_QUERY_LTE
           ],
           "default_lookup": LOOKUP_QUERY_LTE
       },
      "open_class":{
          "field":"admmissionopenclasses_set.class_relation.id",
          "path":"admmissionopenclasses_set",
          "lookups":[MATCHING_OPTION_MUST,LOOKUP_QUERY_IN],
          "default_lookup":MATCHING_OPTION_MUST
          },
     "feature_exist":{
        "field":"feature_set.filter_string",
        "path":"feature_set",
        "lookups":[MATCHING_OPTION_MUST,LOOKUP_QUERY_IN],
        "default_lookup":MATCHING_OPTION_MUST
     },
    }

    highlight_fields = {
        'name': {
            'enabled': True,
            'options': {
                'pre_tags': ["<b>"],
                'post_tags': ["</b>"],
            }
        }
    }

    suggester_fields = {
        'name_suggest': {
            'field': 'name.suggest',
            'suggesters': [
                SUGGESTER_COMPLETION,
            ],
        },
        'school_city':{
            'field':'school_city.name.suggest',
            'suggesters': [
                SUGGESTER_COMPLETION,
            ],
        }
    }



    filter_fields = {
        "active":  {
            "field": "is_active",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookup": MATCHING_OPTION_MUST
        },
        "verified": {
            "field": "is_verified",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookup": MATCHING_OPTION_MUST
        },
        "type": {
            "field": "school_type.slug",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookup": MATCHING_OPTION_MUST
        },

        "school_category":{
            "field":"school_category",
            "lookups":[
                MATCHING_OPTION_MUST,
                ],
            "default_lookup":MATCHING_OPTION_MUST
            },

        "school_country": {
            "field": "school_country.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
            "default_lookup": MATCHING_OPTION_MUST
        },
        "school_state": {
            "field": "school_state.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
        },
        "max_fees":{
            "field":"max_fees",
            "lookups":[
                MATCHING_OPTION_MUST,
                LOOKUP_FILTER_RANGE,
                LOOKUP_QUERY_GTE,
                LOOKUP_QUERY_LTE
                ],
        },
        "min_fees":{
            "field":"min_fees",
            "lookups":[
                MATCHING_OPTION_MUST,
                LOOKUP_FILTER_RANGE,
                LOOKUP_QUERY_GTE,
                LOOKUP_QUERY_LTE
                ],
        },
        "school_city": {
            "field": "school_city.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
        },
        "region": {
            "field": "region.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
        },
        "district": {
            "field": "district.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
        },

        "district_region": {
            "field": "district_region.slug",
            "lookups": [
                LOOKUP_FILTER_PREFIX,
                LOOKUP_FILTER_WILDCARD,
                LOOKUP_QUERY_IN,
                LOOKUP_QUERY_EXCLUDE,
            ],
        },
        "board": {
            "field": "school_boardss.slug",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookup": MATCHING_OPTION_MUST
        },
        "format": {
            "field": "school_format.slug",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookups": MATCHING_OPTION_MUST
        },
        "category": {
            "field": "school_category",
            "lookups": [
                MATCHING_OPTION_MUST
            ],
            "default_lookups": MATCHING_OPTION_MUST
        },
    }

   # faceted_search_fields = {
  #  'feature_name': {
 #         'field': 'feature_set.features.name',
#
       #   #  'facet': TermsFacet,  # But we can define it explicitly
      #      'enabled': True,
     #   },
    #'feature_exist':{
      #   'field': 'feature_set.exist',
     #    'enabled':True
    #    }
   # }

    geo_spatial_filter_fields = {
        "location": {
            "field": "geocoords",
            "lookups": [
                LOOKUP_FILTER_GEO_DISTANCE,
            ],
        },
    }

    geo_spatial_ordering_fields = {
        'location': {
            'field': 'geocoords',
        }
    }

    ordering_fields = {
        "location": "geocoords",
        "global_rank":"global_rank",
        "region_rank":"region_rank",
        "district_rank":"district_rank",
        "district_region_rank":"district_region_rank",
        "collab":"collab",
        "admissionclasses_open_count":"admissionclasses_open_count",
        "total_views":"total_views",
    }


class SchoolViewExcelExport(APIView):
    permission_classes = [
        IsSchoolOrReadOnly,
    ]

    def get(self, request, slug, format=None):
        type= self.request.GET.get('type')
        if type == 'cart':
            queryset = ChildSchoolCart.objects.select_related(
                "user", "school").filter(
                school__pk=self.request.user.current_school).order_by("-timestamp")
            data = SchoolOngoingApplicationsResource().export(queryset=queryset).csv
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="SchoolCartItemList.csv"'
            return response
        elif type == 'views':
            queryset = SchoolView.objects.select_related(
                "user", "school").filter(
                school__pk=self.request.user.current_school)
            # list_of_ids=[]
            # for obj in queryset:
            #             if ChildSchoolCart.objects.filter(child__user=obj.user, school=self.request.user.current_school).exists():
            #                 list_of_ids.append(obj.id)
            # queryset = SchoolView.objects.filter(id__in = list_of_ids)
            data = SchoolViewResource().export(queryset=queryset).csv
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="SchoolViewsList.csv"'
            return response
        else:
            data = ["Please Provide data type"]
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="SchoolViewsList.csv"'
            return response



class SchoolEnquiryExcelExport(APIView):
    permission_classes = [
        IsSchoolOrReadOnly,
    ]

    def get(self, request, slug, format=None):
        enquiries = SchoolEnquiry.objects.select_related(
            "school", "user").filter(school__pk=self.request.user.current_school)
        data = SchoolEnquiryResource().export(queryset=enquiries).csv
        response = HttpResponse(data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="SchoolEnquiryList.csv"'
        return response


class SchoolAdmissionAlertSubscribeView(generics.CreateAPIView):
    serializer_class = serializers.SchoolAdmissionAlertSerializer
    queryset = SchoolAdmissionAlert.objects.all()
    permission_classes = [IsParent, ]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class SchoolAdmissionAlertDeleteView(generics.DestroyAPIView):
    serializer_class = serializers.SchoolAdmissionAlertSerializer
    queryset = SchoolAdmissionAlert.objects.all()
    permission_classes = [IsParent, ]


class SchoolSubscribeListView(generics.ListAPIView):
    serializer_class = serializers.SchoolAdmissionAlertSerializer
    permission_classes = [IsParent, ]

    def get_queryset(self):
        id = self.kwargs.get("pk")
        school = SchoolProfile.objects.filter(id = id).first()
        schoolAdmissionAlert = SchoolAdmissionAlert.objects.filter(user=self.request.user,school_relation=school)
        return schoolAdmissionAlert

class SchoolAdmissionFormFeeListView(generics.ListAPIView):
    serializer_class = serializers.SchoolAdmissionFormFeeSerializer
    permission_classes = [HasSchoolChildModelPermissionOrReadOnly, ]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = SchoolAdmissionFormFee.objects.filter(school_relation=school)
        return queryset

class SchoolAdmissionFormFeeCreateView(APIView):
    serializer_class = serializers.SchoolAdmissionFormFeeSerializer
    permission_classes = [HasSchoolChildModelPermissionOrReadOnly,]

    def post(self,request,slug,format=None):
        serializer = serializers.SchoolAdmissionFormFeeSerializer(data=request.data)
        if serializer.is_valid():
            data=serializer.validated_data
            slug = self.kwargs.get("slug", None)
            school = generics.get_object_or_404(SchoolProfile, slug=slug)
            form_fee_obj,boolean = SchoolAdmissionFormFee.objects.get_or_create(class_relation=data['class_relation'],school_relation=school)
            form_fee_obj.form_price=data['form_price']
            form_fee_obj.save()
            info_logger(f"{self.__class__.__name__} Form Fee Updating for user id {request.user.id}")
            return Response(
                {"status": "Form fee updated successfully!"}, status=status.HTTP_200_OK)
        error_logger(f"{self.__class__.__name__} Serializer Invalid for userid {request.user.id}")
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)



class CustomValidation(APIException):
    """
     To rise custom validation errors
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, detail, field, status_code):
        if status_code is not None:self.status_code = status_code
        if detail is not None:
            self.detail = {field: force_text(detail)}
        else: self.detail = {'detail': force_text(self.default_detail)}

class SchoolUploadCsvView(generics.ListCreateAPIView):
    serializer_class = serializers.SchoolUploadCsvSerializer

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = AppliedSchoolSelectedCsv.objects.filter(school_relation=school)
        return queryset

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        serializer = serializers.SchoolUploadCsvSerializer(data=self.request.data)
        if serializer.is_valid():
            doc=serializer.save()
            csv = pd.read_csv(doc.csv_file)
            if (('RECEIPT ID' in csv.columns) and ("APPLICANT'S NAME" in csv.columns)):
                add_selected_child_data_from_csv(school.id,doc.id)
                return Response({"status": "file uploaded successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "file doesnt have required fields"}, status=status.HTTP_400_BAD_REQUEST)





def add_selected_child_data_from_csv1(school_id,doc_id):
    school = generics.get_object_or_404(SchoolProfile, id=school_id)
    doc = generics.get_object_or_404(AppliedSchoolSelectedCsv,id=doc_id,school_relation=school)
    csv = pd.read_csv(doc.csv_file)
    for index, row in csv.iterrows():
        SelectedStudentFromCsv.objects.create(document=doc,school_relation=school,receipt_id=row['RECEIPT ID'],child_name=row["APPLICANT'S NAME"])
    processed_list = [preprocess_text(i) for i in csv['RECEIPT ID']]
    Applications=SchoolApplication.objects.filter(uid__in=processed_list)
    if Applications:
        for i in Applications:
            ApplicationStatusLog.objects.create(status_id=4,application=i)
    return True



class SchoolFeatureApiView(APIView):
    serializer_class = serializers.SchoolFeaturesSerializer

    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = Feature.objects.filter(school=school).order_by("features__parent__id")
        serializer = serializers.SchoolFeaturesSerializer(queryset ,many=True)
        return  Response(serializer.data,status=status.HTTP_200_OK)


    def put(self,request,slug,format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        data = json.loads(request.body)
        for i in data:
            feature=Feature.objects.get(id=i['id'])
            feature.exist=i['exist']
            feature.filter_string=str(feature.features.name)+"_"+str(feature.exist)
            feature.save()
        queryset = Feature.objects.filter(school=school).order_by("features__parent__id")
        serializer = serializers.SchoolFeaturesSerializer(queryset ,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)




class SchoolFeatureStrApiView(APIView):
    serializer_class = serializers.SchoolFeaturesSerializer

    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        count=Feature.objects.filter(school=school).count()
        if(count==0):
            return Response([],status=status.HTTP_200_OK)
        feature_list = FeatureName.objects.all()
        response_list=[]
        for j in feature_list:
            data={}
            data['feature'] = j.name
            nesteddata_query = Feature.objects.filter(school=school,features__parent=j)
            sub_feature=[]
            for i in nesteddata_query:
                nesteddata={}
                nesteddata['id']= i.features.id
                nesteddata['name']=i.features.name
                nesteddata['exist']= i.exist
                sub_feature.append(nesteddata)
            data['subfeature']=sub_feature
            response_list.append(data)
        return Response(response_list,status=status.HTTP_200_OK)


class SchoolOpenclassesStatus(APIView):
    serializer_class = serializers.SchoolClassesSerializer

    """
    old code without session
    """
    # def get(self, request, slug, format=None):
    #     slug = self.kwargs.get("slug", None)
    #     school = generics.get_object_or_404(SchoolProfile, slug=slug)
    #     queryset = AdmmissionOpenClasses.objects.filter(school=school)
    #     serializer = serializers.AdmmissionOpenClassesSerializer(queryset ,many=True)
    #     return Response(serializer.data,status=status.HTTP_200_OK)
    """
    new code for session based admission
    """
    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        # queryset = AdmmissionOpenClasses.objects.filter(school=school)
        # serializer = serializers.AdmmissionOpenClassesSerializer(queryset ,many=True)
        response = []
        for item in school.class_relation.all():
            item_response = {}
            item_class_realtion_response = {}
            item_class_realtion_response['id'] = item.id
            item_class_realtion_response['name'] = item.name
            item_class_realtion_response['slug'] = item.slug
            item_response['class_relation'] = item_class_realtion_response
            response.append(item_response)
        return Response(response,status=status.HTTP_200_OK)

    def post(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        try:
            for i in request.data:
                if(i["status"]==True):
                    obj=SchoolClasses.objects.get(id=i["id"])
                    school.class_relation.add(obj)

                if(i["status"]==False):
                    obj=SchoolClasses.objects.get(id=i["id"])
                    if school.class_relation.filter(id=obj.id).exists():
                        """
                        old code without session
                        """
                        # obj_del=AdmmissionOpenClasses.objects.get(school=school,class_relation=obj.id)
                        # obj_del.delete()
                        # school.class_relation.remove(obj)
                        """
                        new code for session based admission
                        """
                        if AdmmissionOpenClasses.objects.filter(school=school,class_relation=obj.id).exists():
                            obj_del = AdmmissionOpenClasses.objects.filter(school=school,class_relation=obj.id)
                            for open_class in obj_del:
                                open_class.delete()
                        school.class_relation.remove(obj)
                school.save()
        except SchoolClasses.DoesNotExist:
             return Response({"status": "Please fill correct id"}, status=status.HTTP_400_BAD_REQUEST)
        queryset = AdmmissionOpenClasses.objects.filter(school=school)
        serializer = serializers.AdmmissionOpenClassesSerializer(queryset ,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

import json
class SchoolAvailableClasses(APIView):
    serializer_class = serializers.SchoolAvailableClassesSerializer

    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        # school = generics.get_object_or_404(SchoolProfile, slug=slug)
        # queryset = SchoolProfile.objects.filter(slug=slug)
        queryset1 = generics.get_object_or_404(SchoolProfile, slug=slug)
        serializer = serializers.SchoolAvailableClassesSerializer(queryset1)
        output_dict = json.loads(json.dumps(serializer.data['class_relation']))
        def sortingByRank(e):
            return e['rank']
        output_dict.sort(key=sortingByRank)
        response = {}
        response['class_relation'] = output_dict
        return Response(response,status=status.HTTP_200_OK)

class SchoolSession(APIView):

    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
        classesInCurrentSession = AdmmissionOpenClasses.objects.filter(school__id=school.id, session=currentSession)
        classesInNextSession = AdmmissionOpenClasses.objects.filter(school__id=school.id, session=nextSession)
        if classesInCurrentSession:
            for item in classesInCurrentSession:
                if item.admission_open == "OPEN":
                    isCurrentSessionAdmissionOpen = True
                    break
                else:
                    isCurrentSessionAdmissionOpen = False
        else:
            isCurrentSessionAdmissionOpen = False

        if classesInNextSession:
            for item in classesInNextSession:
                if item.admission_open == "OPEN":
                    isNextSessionAdmissionOpen = True
                    break
                else:
                    isNextSessionAdmissionOpen = False
        else:
            isNextSessionAdmissionOpen = False
        if isCurrentSessionAdmissionOpen == True and isNextSessionAdmissionOpen == True:
            admissionOpenSession = "both"
            selected = nextSession.name
        elif isCurrentSessionAdmissionOpen == False and isNextSessionAdmissionOpen == False:
            admissionOpenSession = "none"
            selected = currentSession.name
        elif isCurrentSessionAdmissionOpen == True:
            admissionOpenSession = "current"
            selected = currentSession.name
        elif isNextSessionAdmissionOpen == True:
            admissionOpenSession = "next"
            selected = nextSession.name
        response = {}
        response['isCurrentSessionAdmissionOpen'] = isCurrentSessionAdmissionOpen
        response['isNextSessionAdmissionOpen'] = isNextSessionAdmissionOpen
        response['admissionOpenSession'] = admissionOpenSession
        response['selected'] = selected
        return Response(response,status=status.HTTP_200_OK)

# For session based admission
# class AdmissionSessionsView(generics.ListAPIView):
class AdmissionSessionsView(APIView):

    # serializer_class = AdmissionSessionsSerializer
    # queryset = AdmissionSession.objects.all().order_by('-id')[:2]
    def get(self, request, format=None):
        # currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
        response = {}
        # nestedCurrentSession = {}
        # nestedNextSession = {}
        # nestedCurrentSession['id'] = currentSession.id
        # nestedCurrentSession['name'] = currentSession.name
        # nestedCurrentSession['slug'] = currentSession.slug
        # nestedCurrentSession['active'] = currentSession.active
        # nestedNextSession['id'] = nextSession.id
        # nestedNextSession['name'] = nextSession.name
        # nestedNextSession['slug'] = nextSession.slug
        # nestedNextSession['active'] = nextSession.active
        nestedResponse = []
        # nestedResponse.append(nestedCurrentSession)
        # nestedResponse.append(nestedNextSession)
        response['count'] = 2
        response['next'] = None
        response['previous'] = None
        bothSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
        if bothSession:
            for session in bothSession:
                nestedSession = {}
                nestedSession['id'] = session.id
                nestedSession['name'] = session.name
                nestedSession['slug'] = session.slug
                nestedSession['active'] = session.active
                nestedResponse.append(nestedSession)
        else:
            nestedSession = {}
        response['results'] = nestedResponse
        return Response(response,status=status.HTTP_200_OK)

class AllAdmissionSessionsView(generics.ListAPIView):
    serializer_class = AdmissionSessionsSerializer
    queryset = AdmissionSession.objects.all()

class AdmissionPageContentView(generics.ListAPIView):
    serializer_class = serializers.AdmissionPageContentSerializer
    queryset = AdmissionPageContent.objects.all()
    filterset_class = AdmissionPageContentFilter

# Notify Me-

class SchoolClassNotificationView(generics.ListCreateAPIView):
    serializer_class = serializers.SchoolClassNotificationSerializer
    def post(self,request,slug):
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        notify_class=self.request.data.get('notify_class')
        notify_class_obj=SchoolClasses.objects.get(id=notify_class)
        session = self.request.data.get('session')
        parent_name=""
        phone_no =""
        email=""
        if self.request.user and self.request.user.is_authenticated:
            parent_name = self.request.user.name
            email = self.request.user.email
            parents = ParentProfile.objects.filter(email=email)
            for parent in parents:
                if (not parent.parent_type):
                    phone_no = parent.phone
                    break
            if SchoolClassNotification.objects.filter(user=self.request.user,school=school,notify_class=notify_class_obj,parent_name=parent_name,session=session,phone_no=phone_no,email=email).exists():
                response = "Already exist"
                return Response(response, status=status.HTTP_200_OK)
            else:
                SchoolClassNotification.objects.create(user=self.request.user,school=school,notify_class=notify_class_obj,parent_name=parent_name,session=session,phone_no=phone_no,email=email,notification_sent=False)
                response = "Submitted"
                return Response(response,status=status.HTTP_200_OK)
        else:
            if not SchoolClassNotification.objects.filter(school=school,notify_class=notify_class_obj,parent_name=parent_name,session=session,phone_no=phone_no,email=email).exists():
                SchoolClassNotification.objects.create(school=school,notify_class=notify_class_obj,parent_name=parent_name,session=session,phone_no=phone_no,email=email,notification_sent=False)
                response = "Submitted"
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = "Already exist"
                return Response(response, status=status.HTTP_200_OK)

    # def get_queryset(self):
    #     slug = self.kwargs.get("slug", None)
    #     queryset=""
    #     school = generics.get_object_or_404(SchoolProfile, slug=slug)
    #     if self.request.user and self.request.user.is_authenticated and self.request.user.is_school:
    #         school_id = self.request.user.current_school
    #         queryset = SchoolClassNotification.objects.filter(
    #             school__id=school_id, school__slug=slug).order_by("-timestamp")
    #     elif self.request.user.is_authenticated:
    #         queryset = SchoolClassNotification.objects.all()
    #     return queryset
    def get(self,request,slug):
        response = "UNAUTHORIZED"
        return Response(response, status=status.HTTP_200_OK)

class VideoTourLinksView(APIView):
    def get(self,request,slug):
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        if VideoTourLinks.objects.filter(school=school).exists():
            school_link=VideoTourLinks.objects.get(school=school)
            links=school_link.link.split(",")
            return Response(links, status=status.HTTP_200_OK)
        else:
            response = []
            return Response(response, status=status.HTTP_200_OK)

class NotificationStatusView(APIView):
   def get(self,request,slug):
       school = generics.get_object_or_404(SchoolProfile, slug=slug)
       notify_class = self.request.GET.get('notify_class')
       notify_class_obj = SchoolClasses.objects.get(id=notify_class)
       session = self.request.GET.get('session')
       result={}
       result["found_status"]=False
       if(SchoolClassNotification.objects.filter(user=self.request.user,school=school,notify_class=notify_class_obj,session=session)):
           result["found_status"] = True
       return Response(result,status=status.HTTP_200_OK)

class TrendingSchoolsHomePage(APIView):
   def get(self,request):
       city = self.request.GET.get('city')
    #    sessionV = requests.get("https://api.main.ezyschooling.com/api/v1/schools/admission-session")
       cuS, neS = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
       currentSession = cuS.name
       nextSession = neS.name
       if SchoolProfile.objects.filter(school_city__slug=city).filter(is_featured=True).filter(collab=True).exists():
           allSchools = SchoolProfile.objects.filter(school_city__slug=city).filter(is_featured=True).filter(collab=True).order_by('-region_rank')
           response = {}
           nestedResponse = []
           for item in allSchools:
               if AdmmissionOpenClasses.objects.filter(school=item,admission_open="OPEN", session=currentSession).exists() or AdmmissionOpenClasses.objects.filter(school=item,admission_open="OPEN", session=nextSession).exists():
                   nestedSchool = {}
                   nestedSchool['id'] = item.id
                   nestedSchool['name'] = item.name
                   nestedSchool['slug'] = item.slug
                   nestedSchool['district_region'] = item.district_region.name
                   nestedSchool['district'] = item.district.name
                   nestedSchool['image'] = item.cover.url
                   nestedSchool['description'] = item.description
                   board_str = ''
                   for board in item.school_boardss.all():
                       if board_str == '':
                           board_str = board.name
                       else:
                           board_str = board_str + ', ' + board.name
                   nestedSchool['boards'] = board_str
                   nestedResponse.append(nestedSchool)
           response['results'] = nestedResponse
           return Response(response,status=status.HTTP_200_OK)

       else:
           response = "No School Found"
           return Response(response,status=status.HTTP_404_NOT_FOUND)

class SimilarSchoolsView(APIView):
  def get(self,request,id):
      child=Child.objects.select_related('class_applying_for').get(id=id)
      class_relation_obj=child.class_applying_for
      cart_items=ChildSchoolCart.objects.filter(child=child).select_related('school','form')
      result = {}
      data = []
      uniques_schools=[]
      if(len(cart_items)):
          for cart in cart_items:
              uniques_schools.append(cart.school)

          for cart in cart_items:
              session=cart.session
              school_obj=cart.school
              district_obj=school_obj.district
              city_obj=school_obj.school_city
              schools = SchoolProfile.objects.filter(school_city=city_obj, district=district_obj)
              multi_obj = [cls_obj for multi_cls in SchoolMultiClassRelation.objects.filter(multi_class_relation=class_relation_obj) for cls_obj in multi_cls.multi_class_relation.filter()]
              if(len(schools)>1):
                  for school in schools:
                      if(school.collab and (school not in uniques_schools)):
                          sch_cls_obj = None
                          if class_relation_obj in multi_obj:
                              for sch_cls in school.class_relation.filter():
                                  if sch_cls in multi_obj:
                                      sch_cls_obj = sch_cls
                          if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj,session=session).exists() or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj,session=session).exists():
                              admission_open_class=AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj,session=session).first() or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj,session=session).first()
                              if(admission_open_class and admission_open_class.admission_open=="OPEN"):
                                  uniques_schools.append(school)
                                  dict = {}
                                  dict["name"]=school.name
                                  dict["class"]=class_relation_obj.name+"/"+sch_cls_obj.name if sch_cls_obj and class_relation_obj != sch_cls_obj else class_relation_obj.name
                                  dict["district"]=school.district.name
                                  dict["district_region"] = school.district_region.name
                                  dict["slug"]=school.slug
                                  dict["logo_url"]=str(school.logo.url)
                                  dict["id"] = school.id
                                  dict['session'] = session
                                  data.append(dict)
              else:
                  schools = SchoolProfile.objects.filter(school_city__slug='delhi')
                  for school in schools:
                      if (school.collab and (school not in uniques_schools)):
                          sch_cls_obj = None
                          if class_relation_obj in multi_obj:
                              for sch_cls in school.class_relation.filter():
                                  if sch_cls in multi_obj:
                                      sch_cls_obj = sch_cls
                          if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj,session=session).exists() or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj,session=session).exists():
                              admission_open_class = AdmmissionOpenClasses.objects.filter(school=school,
                                                                                          class_relation=class_relation_obj,session=session) or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj,session=session)
                              for adm_opn in admission_open_class:
                                  if (adm_opn and adm_opn.admission_open == "OPEN" and school not in uniques_schools):
                                      uniques_schools.append(school)
                                      dict = {}
                                      dict["name"] = school.name
                                      dict["class"]=class_relation_obj.name+"/"+sch_cls_obj.name if sch_cls_obj and class_relation_obj != sch_cls_obj else class_relation_obj.name
                                      dict["district"] = school.district.name
                                      dict["district_region"] = school.district_region.name
                                      dict["slug"] = school.slug
                                      dict["logo_url"] = str(school.logo.url)
                                      dict["id"]=school.id
                                      dict['session']=session
                                      data.append(dict)

      else:
          schools = SchoolProfile.objects.filter(school_city__slug='delhi')
          multi_obj = [cls_obj for multi_cls in
                       SchoolMultiClassRelation.objects.filter(multi_class_relation=class_relation_obj) for cls_obj in
                       multi_cls.multi_class_relation.filter()]

          for school in schools:
              if (school.collab and (school not in uniques_schools)):
                  sch_cls_obj = None
                  if class_relation_obj in multi_obj:
                      for sch_cls in school.class_relation.filter():
                          if sch_cls in multi_obj:
                              sch_cls_obj = sch_cls
                  if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj).exists() or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj).exists():
                      admission_open_class = AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj) or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj)
                      for adm_opn in admission_open_class:
                          if (adm_opn and adm_opn.admission_open == "OPEN" and school not in uniques_schools):
                              uniques_schools.append(school)
                              dict = {}
                              dict["name"] = school.name
                              dict["class"]=class_relation_obj.name+"/"+sch_cls_obj.name if sch_cls_obj and class_relation_obj != sch_cls_obj else class_relation_obj.name
                              dict["district"] = school.district.name
                              dict["district_region"] = school.district_region.name
                              dict["slug"] = school.slug
                              dict["logo_url"] = str(school.logo.url)
                              dict["id"] = school.id
                              data.append(dict)

      if len(data) == 0:
          schools = SchoolProfile.objects.filter(school_city__slug='delhi')
          for school in schools:
              if len(data) <=5:
                  if (school.collab and (school not in uniques_schools)):
                      sch_cls_obj = None
                      if class_relation_obj in multi_obj:
                          for sch_cls in school.class_relation.filter():
                              if sch_cls in multi_obj:
                                  sch_cls_obj = sch_cls
                      if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj).exists() or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj).exists():
                          admission_open_class = AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_relation_obj) or AdmmissionOpenClasses.objects.filter(school=school,class_relation=sch_cls_obj)
                          for adm_opn in admission_open_class:
                              if (adm_opn and adm_opn.admission_open == "OPEN" and school not in uniques_schools):
                                  uniques_schools.append(school)
                                  dict = {}
                                  dict["name"] = school.name
                                  dict["class"]=class_relation_obj.name+"/"+sch_cls_obj.name if sch_cls_obj and class_relation_obj != sch_cls_obj else class_relation_obj.name
                                  dict["district"] = school.district.name
                                  dict["district_region"] = school.district_region.name
                                  dict["slug"] = school.slug
                                  dict["logo_url"] = str(school.logo.url)
                                  dict["id"] = school.id
                                  data.append(dict)
      result["results"]=data
      return Response(result,status=status.HTTP_200_OK)


class FetchMultiSchoolView(APIView):
    def get(self, request, id):
        result = {}
        multi_obj=SchoolMultiClassRelation.objects.filter(multi_class_relation__id=id).first()
        if multi_obj:
            result["class_ids"] = [sch_cls.id for sch_cls in multi_obj.multi_class_relation.filter()]
            result["status"] = True
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["class_ids"] = []
            result["status"] = False
            return Response(result, status=status.HTTP_200_OK)


class SchoolAverageFees(APIView):
    def get(self,request):
        slug = self.request.GET.get('slug')
        if SchoolProfile.objects.filter(slug=slug).exists():
            school_profile = SchoolProfile.objects.get(slug=slug)
            if not school_profile.boarding_school:
                if school_profile.avg_fee:
                    result = {}
                    result['results']={}
                    result['results']['fee'] = str(school_profile.avg_fee)
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
                elif not school_profile.last_avg_fee_calculated:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                    if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists() and FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                        final_fee_current = 10000000000
                        final_fee_next = 10000000000
                        fee_tenure_next = "Monthly"
                        fee_tenure_current = "Monthly"
                        for currentFee in currentSessionFees:
                            for fee in currentFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                            fee_tenure_current = fee.tenure
                                            final_fee_current = fee.price

                        for nextFee in nextSessionFees:
                            for fee in nextFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                            fee_tenure_next = fee.tenure
                                            final_fee_next = fee.price
                        avg_fee = 0
                        if final_fee_current and final_fee_next:
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        elif final_fee_current == 10000000000 and final_fee_next:
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        elif final_fee_next == 10000000000 and final_fee_current:
                            if fee_tenure_current == "Monthly":
                                avg_fee = int(final_fee_current/1)
                            elif fee_tenure_current == "Quarterly":
                                avg_fee = int(final_fee_current/3)
                            elif fee_tenure_current == "Annually":
                                avg_fee = int(final_fee_current/12)
                            else:
                                avg_fee = int(final_fee_current)

                    elif FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        fee_tenure_current = "Monthly"
                        final_fee_current = 10000000000
                        for currentFee in currentSessionFees:
                            for fee in currentFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                            fee_tenure_current = fee.tenure
                                            final_fee_current = fee.price

                        if fee_tenure_current == "Monthly":
                            avg_fee = int(final_fee_current/1)
                        elif fee_tenure_current == "Quarterly":
                            avg_fee = int(final_fee_current/3)
                        elif fee_tenure_current == "Annually":
                            avg_fee = int(final_fee_current/12)
                        else:
                            avg_fee = int(final_fee_current)
                    elif FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                        nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                        fee_tenure_next = "Monthly"
                        final_fee_next = 10000000000
                        for nextFee in nextSessionFees:
                            for fee in nextFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                            fee_tenure_next = fee.tenure
                                            final_fee_next = fee.price
                        if fee_tenure_next == "Monthly":
                            avg_fee = int(final_fee_next/1)
                        elif fee_tenure_next == "Quarterly":
                            avg_fee = int(final_fee_next/3)
                        elif fee_tenure_next == "Annually":
                            avg_fee = int(final_fee_next/12)
                        else:
                            avg_fee = int(final_fee_next)
                    else:
                        avg_fee = "NA"
                    if avg_fee == 10000000000 or avg_fee == '10000000000':
                        avg_fee = "NA"
                    todays_date = date.today()
                    school_profile.calculated_avg_fee = str(avg_fee)
                    school_profile.last_avg_fee_calculated = todays_date
                    school_profile.save()
                    result = {}
                    result['results']={}
                    result['results']['fee'] = school_profile.calculated_avg_fee
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)

                else:
                    todays_date = date.today()
                    last_update_date = school_profile.last_avg_fee_calculated
                    days_diff = todays_date - last_update_date
                    if days_diff.days >=4:
                        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                        if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists() and FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                            currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                            nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                            final_fee_current = 10000000000
                            final_fee_next = 10000000000
                            fee_tenure_next = "Monthly"
                            fee_tenure_current = "Monthly"
                            for currentFee in currentSessionFees:
                                for fee in currentFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                                fee_tenure_current = fee.tenure
                                                final_fee_current = fee.price

                            for nextFee in nextSessionFees:
                                for fee in nextFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                                fee_tenure_next = fee.tenure
                                                final_fee_next = fee.price
                            avg_fee = 0
                            if final_fee_current and final_fee_next:
                                if fee_tenure_next == "Monthly":
                                    avg_fee = int(final_fee_next/1)
                                elif fee_tenure_next == "Quarterly":
                                    avg_fee = int(final_fee_next/3)
                                elif fee_tenure_next == "Annually":
                                    avg_fee = int(final_fee_next/12)
                                else:
                                    avg_fee = int(final_fee_next)
                            elif final_fee_current == 10000000000 and final_fee_next:
                                if fee_tenure_next == "Monthly":
                                    avg_fee = int(final_fee_next/1)
                                elif fee_tenure_next == "Quarterly":
                                    avg_fee = int(final_fee_next/3)
                                elif fee_tenure_next == "Annually":
                                    avg_fee = int(final_fee_next/12)
                                else:
                                    avg_fee = int(final_fee_next)
                            elif final_fee_next == 10000000000 and final_fee_current:
                                if fee_tenure_current == "Monthly":
                                    avg_fee = int(final_fee_current/1)
                                elif fee_tenure_current == "Quarterly":
                                    avg_fee = int(final_fee_current/3)
                                elif fee_tenure_current == "Annually":
                                    avg_fee = int(final_fee_current/12)
                                else:
                                    avg_fee = int(final_fee_current)

                        elif FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                            currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                            fee_tenure_current = "Monthly"
                            final_fee_current = 10000000000
                            for currentFee in currentSessionFees:
                                for fee in currentFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                                fee_tenure_current = fee.tenure
                                                final_fee_current = fee.price

                            if fee_tenure_current == "Monthly":
                                avg_fee = int(final_fee_current/1)
                            elif fee_tenure_current == "Quarterly":
                                avg_fee = int(final_fee_current/3)
                            elif fee_tenure_current == "Annually":
                                avg_fee = int(final_fee_current/12)
                            else:
                                avg_fee = int(final_fee_current)
                        elif FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                            nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                            fee_tenure_next = "Monthly"
                            final_fee_next = 10000000000
                            for nextFee in nextSessionFees:
                                for fee in nextFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                                fee_tenure_next = fee.tenure
                                                final_fee_next = fee.price
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        else:
                            avg_fee = "NA"
                        if avg_fee == 10000000000 or avg_fee == '10000000000':
                            avg_fee = "NA"
                        school_profile.calculated_avg_fee = str(avg_fee)
                        school_profile.last_avg_fee_calculated = todays_date
                        school_profile.save()
                    result = {}
                    result['results']={}
                    result['results']['fee'] = school_profile.calculated_avg_fee
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
            else:
                if school_profile.avg_fee:
                    result = {}
                    result['results']={}
                    result['results']['fee'] = str(school_profile.avg_fee)
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
                elif not school_profile.last_avg_fee_calculated:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                    if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        final_fee_current = 10000000000
                        for currentFee in currentSessionFees:
                            class_total_monthly_fee = 0
                            for fee in currentFee.fees_parameters.all().values_list('tenure','price'):
                                if fee[0] == "Monthly":
                                    class_total_monthly_fee += int(fee[1]/1)
                                elif fee[0] == "Quarterly":
                                    class_total_monthly_fee += int(fee[1]/3)
                                # elif fee[0] == "Annually":
                                #     class_total_monthly_fee += int(fee[1]/12)
                                else:
                                    class_total_monthly_fee += int(fee[1]/12)

                            if final_fee_current > class_total_monthly_fee:
                                final_fee_current = class_total_monthly_fee
                    avg_fee = final_fee_current*3
                    if avg_fee == 30000000000 or avg_fee == '100000000001000000000010000000000':
                        avg_fee = "NA"
                    school_profile.calculated_avg_fee = str(avg_fee)
                    school_profile.last_avg_fee_calculated = todays_date
                    school_profile.save()
                    result = {}
                    result['results']={}
                    result['results']['fee'] = school_profile.calculated_avg_fee
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)

                else:
                    todays_date = date.today()
                    last_update_date = school_profile.last_avg_fee_calculated
                    days_diff = todays_date - last_update_date
                    if days_diff.days >=4:
                        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                        if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                            currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                            final_fee_current = 10000000000
                            for currentFee in currentSessionFees:
                                class_total_monthly_fee = 0
                                for fee in currentFee.fees_parameters.all().values_list('tenure','price'):
                                    if fee[0] == "Monthly":
                                        class_total_monthly_fee += int(fee[1]/1)
                                    elif fee[0] == "Quarterly":
                                        class_total_monthly_fee += int(fee[1]/3)
                                    # elif fee[0] == "Annually":
                                    #     class_total_monthly_fee += int(fee[1]/12)
                                    else:
                                        class_total_monthly_fee += int(fee[1]/12)

                                if final_fee_current > class_total_monthly_fee:
                                    final_fee_current = class_total_monthly_fee
                        avg_fee = final_fee_current*3
                        if avg_fee == 30000000000 or avg_fee == '100000000001000000000010000000000':
                            avg_fee = "NA"
                        school_profile.calculated_avg_fee = str(avg_fee)
                        school_profile.last_avg_fee_calculated = todays_date
                        school_profile.save()
                    result = {}
                    result['results']={}
                    result['results']['fee'] = school_profile.calculated_avg_fee
                    result['results']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)

        else:
            result = {}
            result["results"] = "No School Found"
            return Response(result,status=status.HTTP_404_NOT_FOUND)



today = date.today()
class GroupedSchoolsView(APIView):
    def get(self,request,id):

        if self.request.GET.get('date'):
            date = self.request.GET.get('date')
        else:
            date = ''
        if date:
            date = date.split("-")
            date = datetime(int(date[0]), int(date[1]), int(date[2]), tzinfo=pytz.timezone("Asia/Calcutta"))
        groups=GroupedSchools.objects.prefetch_related('schools')
        grouped_schools=groups.get(api_key=id)
        if(grouped_schools.is_active):
            data = {}
            data["date_format"] = f"To filter by date provide date in query in YYYY-MM-DD format query example - ?date={today}"
            data["example_api_without_date"] = f"https://api.main.ezyschooling.com/api/v1/schools/{id}/group-data/"
            data["example_api_with_date"] = f"https://api.main.ezyschooling.com/api/v1/schools/{id}/group-data/?date={today}"
            data["group_name"] = grouped_schools.group_name
            data["results"] = []
            for school in grouped_schools.schools.all().select_related('school_city','district_region','school_state'):
                school_result={}
                school_result["id"] = school.id
                school_result["common_id"]=''
                school_result["name"]=''
                school_result["city"]=''
                school_result["area"]=''
                school_result["state"]=''
                if(school.name):
                    school_result["name"] = school.name
                if(school.school_city):
                    school_result["city"]=school.school_city.name
                if(school.district_region):
                    school_result["area"]=school.district_region.name
                if(school.school_state):
                    school_result["state"] = school.school_state.name
                if(school.common_id):
                    school_result["common_id"] = school.common_id
                if(school.enquiry_permission):
                    if not date:
                        school_enquiries=SchoolEnquiry.objects.filter(school=school)
                    else:
                        school_enquiries=SchoolEnquiry.objects.filter(school=school,timestamp__year=date.year,timestamp__month=date.month,timestamp__day=date.day)
                    school_result["enquiries"] = []
                    for enquiry in school_enquiries:
                        enquiries = {}
                        enquiries["id"] = enquiry.id
                        enquiries["date"] = enquiry.timestamp.strftime('%d/%m/%Y')
                        enquiries["parent_name"] = enquiry.parent_name
                        enquiries["phone_no"] = enquiry.phone_no
                        enquiries["email"] = enquiry.email
                        enquiries["query"] = enquiry.query
                        school_result["enquiries"].append(enquiries)
                else:
                    school_result["enquiries"]={
                        'status':'Permission Denied',
                        'id': '',
                        'date': '',
                        'parent_name': '',
                        'phone_no': '',
                        'email': '',
                        'query': '',
                    }
                if not date:
                    form_receipt=FormReceipt.objects.filter(school_applied__school=school).select_related('school_applied__apply_for','school_applied__child')
                else:
                    form_receipt=FormReceipt.objects.filter(school_applied__school=school,timestamp__year=date.year,timestamp__month=date.month,timestamp__day=date.day).select_related('school_applied__apply_for','school_applied__child')
                school_result["form_receipt"] = []
                for form in form_receipt:
                    receipt={}
                    receipt["form_data"]={}
                    receipt["form_data"]["applied_date"]=form.timestamp.strftime('%d/%m/%Y')
                    receipt["form_data"]["form_fee"]=form.form_fee
                    receipt["form_data"]["receipt_id"]=form.receipt_id
                    receipt["form_data"]["session"]=form.school_applied.registration_data.session
                    receipt["form_data"]["class_applied_for"] = form.school_applied.registration_data.child_class_applying_for.name
                    receipt["child_data"]={}
                    receipt["child_data"]["name"] = form.school_applied.registration_data.child_name
                    receipt["child_data"]["date_of_birth"] = form.school_applied.registration_data.child_date_of_birth.strftime('%d/%m/%Y')
                    if form.school_applied.registration_data.child_orphan:
                        receipt["child_data"]["is_orphan"]= "Yes"
                    else:
                        receipt["child_data"]["is_orphan"]= "No"
                    if not form.school_applied.registration_data.child_orphan:
                        receipt["father_data"]={}
                        receipt["father_data"]["name"]=form.school_applied.registration_data.father_name
                        receipt["father_data"]["email"]=form.school_applied.registration_data.father_email
                        receipt["father_data"]["mobile"]=form.school_applied.registration_data.father_phone
                        receipt["mother_data"]={}
                        receipt["mother_data"]["name"]=form.school_applied.registration_data.father_name
                        receipt["mother_data"]["email"]=form.school_applied.registration_data.mother_email
                        receipt["mother_data"]["mobile"]=form.school_applied.registration_data.mother_phone
                    elif form.school_applied.registration_data.child_orphan:
                        receipt["guardian_data"]={}
                        receipt["guardian_data"]["name"]=form.school_applied.registration_data.guardian_name
                        receipt["guardian_data"]["email"]=form.school_applied.registration_data.guardian_email
                        receipt["guardian_data"]["mobile"]=form.school_applied.registration_data.guardian_phone
                    school_result["form_receipt"].append(receipt)
                if school.counselling_data_permission:
                    if not date:
                        AdmissionData=list(AdmissionDoneData.objects.filter(admission_done_for=school))
                        VisitSchedule=list(VisitScheduleData.objects.filter(walk_in_for=school))
                        LeadGeneratedData=LeadGenerated.objects.filter(lead_for=school)
                    else:
                        AdmissionData=AdmissionDoneData.objects.filter(admission_done_for=school,admissiomn_done_created_at__year=date.year,admissiomn_done_created_at__month=date.month,admissiomn_done_created_at__day=date.day)
                        VisitSchedule=VisitScheduleData.objects.filter(walk_in_for=school,walk_in_created_at__year=date.year,walk_in_created_at__month=date.month,walk_in_created_at__day=date.day)
                        LeadGeneratedData=LeadGenerated.objects.filter(lead_for=school,lead_created_at__year=date.year,lead_created_at__month=date.month,lead_created_at__day=date.day)
                    school_result["lead_generated"] = []
                    for lead in LeadGeneratedData:
                        LeadGenerated_Data ={}
                        LeadGenerated_Data['name'] =lead.user_name
                        if lead.enquiry:
                            LeadGenerated_Data['phone_number'] =lead.user_phone_number[1:-1]
                        else:
                            LeadGenerated_Data['phone_number'] =lead.user_phone_number
                        LeadGenerated_Data['email'] =lead.user_email
                        LeadGenerated_Data['class'] =lead.classes
                        LeadGenerated_Data['budget'] =lead.budget
                        LeadGenerated_Data['location'] =lead.location
                        LeadGenerated_Data['lead_date'] =lead.lead_created_at.strftime('%d/%m/%Y')
                        school_result["lead_generated"].append(LeadGenerated_Data)

                    school_result["visit_schedule"] = []
                    for visit in VisitSchedule:
                        VisitSchedule_Data ={}
                        VisitSchedule_Data['name'] =visit.user_name
                        if visit.enquiry:
                            VisitSchedule_Data['phone_number'] =visit.user_phone_number[1:-1]
                        else:
                            VisitSchedule_Data['phone_number'] =visit.user_phone_number
                        VisitSchedule_Data['email'] =visit.user_email
                        VisitSchedule_Data['walk_in_date'] =visit.walk_in_created_at.strftime('%d/%m/%Y')
                        school_result["visit_schedule"].append(VisitSchedule_Data)

                    school_result["admissions_done"] = []
                    for admission in AdmissionData:
                        AdmissionsData = {}
                        AdmissionsData['name'] =admission.user_name
                        if admission.enquiry:
                            AdmissionsData['phone_number'] =admission.user_phone_number[1:-1]
                        else:
                            AdmissionsData['phone_number'] =admission.user_phone_number
                        AdmissionsData['email'] =admission.user_email
                        AdmissionsData['admission_date'] =admission.admissiomn_done_created_at.strftime('%d/%m/%Y')
                        school_result["admissions_done"].append(AdmissionsData)
                else:
                    school_result["lead_generated"] = {
                        'status':'Permission Denied',
                        'name': '',
                        'phone_number': '',
                        'email': '',
                        'class': '',
                        'budget':'',
                        'location':'',
                        'lead_date':'',
                    }
                    school_result["visit_schedule"] = {
                        'status':'Permission Denied',
                        'name': '',
                        'phone_number': '',
                        'email': '',
                        'walk_in_date': '',
                    }
                    school_result["admissions_done"] = {
                        'status':'Permission Denied',
                        'name': '',
                        'phone_number': '',
                        'email': '',
                        'admission_date': '',
                    }
                data["results"].append(school_result)
            return Response(data,status=status.HTTP_200_OK)
        else:
            data = {}
            data['results'] = "School API Not Active"
            return Response(data,status=status.HTTP_200_OK)

# School Applied and Interested Parents data
class SchoolVisitorsDataView(APIView):
    def get(self,request,slug):
        if SchoolProfile.objects.filter(slug=slug).exists():
            school = SchoolProfile.objects.get(slug=slug)
            time=datetime.now()-timedelta(hours = 720)
            cart_items_last30 =ChildSchoolCart.objects.filter(school=school,timestamp__gte=time).count()
            apply_items_last30 =SchoolApplication.objects.filter(school=school,timestamp__gte=time).count()
            cart_items= ChildSchoolCart.objects.filter(school=school).count()
            school_apply_items=SchoolApplication.objects.filter(school=school).count()
            notify_items=SchoolClassNotification.objects.filter(school=school).count()
            enquiry_items=SchoolEnquiry.objects.filter(school=school).count()
            views=school.views
            interested= int(cart_items+school_apply_items+notify_items+enquiry_items+(views*0.3))
            result={}
            result["results"]={}
            result["results"]["last_30_days"]=cart_items_last30 +apply_items_last30
            result["results"]["interested_items"] = interested
            return Response(result,status=status.HTTP_200_OK)
        else:
            result={}
            result["results"]="No School Found"
            return Response(result,status=status.HTTP_404_NOT_FOUND)

# School Wise Expert articles and news
class SchoolNewsArticlesView(APIView):
    def get(self,request,slug):
        if SchoolProfile.objects.filter(slug=slug).exists():
            if ExpertArticle.objects.filter(status="P").filter(for_schools__slug=slug).exists() and News.objects.filter(status="P").filter(for_schools__slug=slug).exists():
                all_articles = ExpertArticle.objects.filter(status="P").filter(for_schools__slug=slug)
                all_news = News.objects.filter(status="P").filter(for_schools__slug=slug)
                results = []
                for articles in all_articles:
                    results.append({
                    "title": articles.title,
                    "mini_title": articles.mini_title,
                    "created_by":articles.created_by.name,
                    "thumbnail": articles.thumbnail.url,
                    "views": articles.views,
                    "slug": articles.slug,
                    "type": "article",
                    })
                for news in all_news:
                    results.append({
                    "title": news.title,
                    "mini_title": news.mini_title,
                    "author": news.author.name,
                    "image": news.image.url,
                    "views": news.views,
                    "slug": news.slug,
                    "type": "news",
                    })
                return Response(results, status=status.HTTP_200_OK)
            elif ExpertArticle.objects.filter(status="P").filter(for_schools__slug=slug).exists():
                all_articles = ExpertArticle.objects.filter(status="P").filter(for_schools__slug=slug)
                results = []
                for articles in all_articles:
                    results.append({
                    "title": articles.title,
                    "mini_title": articles.mini_title,
                    "created_by":articles.created_by.name,
                    "thumbnail": articles.thumbnail.url,
                    "views": articles.views,
                    "slug": articles.slug,
                    "type": "article",
                    })
                return Response(results, status=status.HTTP_200_OK)
            elif News.objects.filter(status="P").filter(for_schools__slug=slug).exists():
                all_news = News.objects.filter(status="P").filter(for_schools__slug=slug)
                results = []
                for news in all_news:
                    results.append({
                    "title": news.title,
                    "mini_title": news.mini_title,
                    "author": news.author.name,
                    "image": news.image.url,
                    "views": news.views,
                    "slug": news.slug,
                    "type": "news",
                    })
                return Response(results, status=status.HTTP_200_OK)
            else:
                results =[]
                return Response(results,status=status.HTTP_200_OK)
        else:
            results =[]
            return Response(results, status=status.HTTP_200_OK)


# For checking fee in session
class SchoolFeeSession(APIView):
    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]

        if FeeStructure.objects.filter(school__id=school.id, session=currentSession).exists() and FeeStructure.objects.filter(school__id=school.id, session=nextSession).exists():
            feeInSession = "both"
            selected = nextSession.name
        elif FeeStructure.objects.filter(school__id=school.id,session=currentSession).exists():
            feeInSession = "current"
            selected = currentSession.name
        elif FeeStructure.objects.filter(school__id=school.id, session=nextSession).exists():
            feeInSession = "next"
            selected = nextSession.name
        else:
            feeInSession = "none"
            selected = currentSession.name
        isCurrentSessionFeeAvailable = False
        isNextSessionFeeAvailable = False
        if FeeStructure.objects.filter(school__id=school.id, session=currentSession).exists():
            isCurrentSessionFeeAvailable = True
        if FeeStructure.objects.filter(school__id=school.id, session=nextSession).exists():
            isNextSessionFeeAvailable = True
        response = {}
        response['isCurrentSessionFeeAvailable'] = isCurrentSessionFeeAvailable
        response['isNextSessionFeeAvailable'] = isNextSessionFeeAvailable
        response['feeInSession'] = feeInSession
        response['selected'] = selected
        return Response(response,status=status.HTTP_200_OK)

class SchoolAdmissionResultImageView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    serializer_class = serializers.SchoolAdmissionResultImageSerializer
    def get_queryset(self):
        slug = self.kwargs.get("slug")
        queryset = SchoolAdmissionResultImage.objects.filter(school__slug=slug).order_by("timestamp")
        return queryset

class SchoolAdmissionResultImageDetailView(SchoolPerformCreateUpdateMixin,
        generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.SchoolAdmissionResultImageSerializer
    lookup_field = "pk"
    def get_queryset(self):
        slug = self.kwargs.get("slug")
        queryset = SchoolAdmissionResultImage.objects.filter(school__slug=slug)
        return queryset


class ExploreSchoolPageSEO(APIView):
    def get(self,request):
        yearValue = get_year_value_for_seo()
        city = self.request.GET.get('city')
        district = self.request.GET.get('district')
        area = self.request.GET.get('area')
        grade = self.request.GET.get('grade')
        board = self.request.GET.get('board')
        if city:
            if City.objects.filter(slug=city).exists():
                pass
            else:
                city = 'delhi'
        if district:
            if District.objects.filter(slug=district).exists():
                pass
            else:
                district = ''
        if area:
            if DistrictRegion.objects.filter(slug=area).exists():
                pass
            else:
                area = ''
        if grade:
            grade = grade.split(",")
            if SchoolClasses.objects.filter(slug__in=grade).exists():
                if 'pre-nursery' in grade:
                    grade = 'pre-nursery'
                elif 'lkg' in grade:
                    grade = 'lkg'
                elif 'ukg' in grade:
                    grade = 'ukg'
                else:
                    grade = grade[0]
            else:
                grade = ''
        if board:
            if SchoolBoard.objects.filter(slug=board).exists():
                pass
            else:
                board = ''

        result={}
        if area and board and grade:
            result["results"]={}
            obj = DistrictRegion.objects.get(slug=area)
            obj1 = SchoolBoard.objects.get(slug=board)
            obj2 = SchoolClasses.objects.get(slug=grade)
            if obj.city.slug == "online-schools":
                result["results"]["h1"] = f'{obj1.name} Online | Virtual Schools In India For {obj2.name}'
                result["results"][
                    "title"] = f"Best {obj1.name} Online | Virtual Schools In India For {obj2.name} Admission {yearValue} | Ezyschooling"
                result["results"][
                    "description"] = f"List of all Best {obj1.name} Online | Virtual Schools for {obj2.name} in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'{obj1.name} Boarding Schools In {obj.name} For {obj2.name}'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools In {obj.name} For {obj2.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools In {obj.name} For {obj2.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj2.name} {obj1.name} Schools In {obj.name}, {obj.city.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools For {obj2.name} in {obj.name}, {obj.city.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools For {obj2.name} in {obj.name}, {obj.city.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif district and board and grade:
            result["results"]={}
            obj = District.objects.get(slug=district)
            obj1 = SchoolBoard.objects.get(slug=board)
            obj2 = SchoolClasses.objects.get(slug=grade)
            if obj.city.slug == 'boarding-schools':
                result["results"]["h1"] = f'{obj1.name} Boarding Schools In {obj.name} For {obj2.name}'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools In {obj.name} For {obj2.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools In {obj.name} For {obj2.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj2.name} {obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools For {obj2.name} in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools For {obj2.name} in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif city and board and grade:
            result["results"]={}
            obj = City.objects.get(slug=city)
            obj1 = SchoolBoard.objects.get(slug=board)
            obj2 = SchoolClasses.objects.get(slug=grade)
            if obj.slug == "online-schools":
                result["results"]["h1"] = f'{obj1.name} Online | Virtual Schools In India For {obj2.name}'
                result["results"]["title"] = f"Best {obj1.name} Online | Virtual Schools In India For {obj2.name} Admission {yearValue} | Ezyschooling"
                result["results"]["description"] = f"List of all Best {obj1.name} Online | Virtual Schools for {obj2.name} in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.slug == "boarding-schools":
                result["results"]["h1"] = f'{obj1.name} Boarding Schools In India For {obj2.name}'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools In India For {obj2.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools In India For {obj2.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj2.name} {obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools For {obj2.name} in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools For {obj2.name} in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif area and board:
            result["results"]={}
            obj = DistrictRegion.objects.get(slug=area)
            obj1 = SchoolBoard.objects.get(slug=board)
            if obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'{obj1.name} Boarding Schools in {obj.name}'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools in {obj.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools in {obj.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            elif obj.city.slug == "online-schools":
                result["results"]["h1"] = f'{obj1.name} Online | Virtual Schools In India'
                result["results"][
                    "title"] = f"Best {obj1.name} Online | Virtual Schools In India For Admission {yearValue} | Ezyschooling"
                result["results"][
                    "description"] = f"List of all Best {obj1.name} Online | Virtual Schools in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            else:
                result["results"]["h1"] = f'{obj1.name} Schools in {obj.name}, {obj.city.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name}, {obj.city.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}, {obj.city.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif district and board:
            result["results"]={}
            obj = District.objects.get(slug=district)
            obj1 = SchoolBoard.objects.get(slug=board)
            if obj.city.slug == 'boarding-schools':
                result["results"]["h1"] = f'{obj1.name} Boarding Schools in {obj.name}'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools in {obj.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools in {obj.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif city and board:
            result["results"]={}
            obj = City.objects.get(slug=city)
            obj1 = SchoolBoard.objects.get(slug=board)
            if obj.slug == "online-schools":
                result["results"]["h1"] = f'{obj1.name} Online | Virtual Schools In India'
                result["results"]["title"] = f"Best {obj1.name} Online | Virtual Schools In India For Admission {yearValue} | Ezyschooling"
                result["results"]["description"] = f"List of all Best {obj1.name} Online | Virtual Schools in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.slug == "boarding-schools":
                result["results"]["h1"] = f'{obj1.name} Boarding Schools in India'
                result["results"]["title"] = f"Top {obj1.name} Boarding Schools in India {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Boarding Schools in India. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif area and grade:
            result["results"]={}
            obj = DistrictRegion.objects.get(slug=area)
            obj1 = SchoolClasses.objects.get(slug=grade)
            if obj.city.slug == "online-schools":
                result["results"]["h1"] = f'Online | Virtual Schools in India For {obj1.name}'
                result["results"]["title"] = f"Best Online | Virtual Schools In India For {obj1.name} Admission {yearValue} | Ezyschooling"
                result["results"]["description"] = f"List of all Best Online | Virtual Schools for {obj1.name} in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in {obj.name} For {obj1.name}'
                result["results"]["title"] = f"Top Boarding Schools in {obj.name} For {obj1.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in {obj.name} For {obj1.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj1.name} Schools In {obj.name}, {obj.city.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name}, {obj.city.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}, {obj.city.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif district and grade:
            result["results"]={}
            obj = District.objects.get(slug=district)
            obj1 = SchoolClasses.objects.get(slug=grade)
            if obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in {obj.name} For {obj1.name}'
                result["results"]["title"] = f"Top Boarding Schools in {obj.name} For {obj1.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in {obj.name} For {obj1.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif city and grade:
            result["results"]={}
            obj = City.objects.get(slug=city)
            obj1 = SchoolClasses.objects.get(slug=grade)
            if obj.slug == "online-schools":
                result["results"]["h1"] = f'Online | Virtual Schools in India For {obj1.name}'
                result["results"]["title"] = f"Best Online | Virtual Schools In India For {obj1.name} Admission {yearValue} | Ezyschooling"
                result["results"]["description"] = f"List of all Best Online | Virtual Schools for {obj1.name} in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in India For {obj1.name}'
                result["results"]["title"] = f"Top Boarding Schools in India For {obj1.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in India For {obj1.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'{obj1.name} Schools in {obj.name}'
                result["results"]["title"] = f"Best {obj1.name} Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best {obj1.name} Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif area:
            result["results"]={}
            obj = DistrictRegion.objects.get(slug=area)
            if obj.city.slug == "online-schools":
                result["results"]["h1"] = f'Online | Virtual Schools In India'
                result["results"][
                    "title"] = f"Best Online | Virtual Schools In India For Admission {yearValue} | Ezyschooling"
                result["results"][
                    "description"] = f"List of all Best Online | Virtual Schools in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in {obj.name}'
                result["results"]["title"] = f"Top Boarding Schools in {obj.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in {obj.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'Schools in {obj.name}, {obj.city.name}'
                result["results"]["title"] = f"Best Schools in {obj.name}, {obj.city.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best Schools in {obj.name}, {obj.city.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif district:
            result["results"]={}
            obj = District.objects.get(slug=district)
            if obj.city.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in {obj.name}'
                result["results"]["title"] = f"Top Boarding Schools in {obj.name} {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in {obj.name}. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'Schools in {obj.name}'
                result["results"]["title"] = f"Best Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        elif city:
            result["results"]={}
            obj = City.objects.get(slug=city)
            if obj.slug == "online-schools":
                result["results"]["h1"] = f'Online | Virtual Schools In India'
                result["results"][
                    "title"] = f"Best Online | Virtual Schools In India For Admission {yearValue} | Ezyschooling"
                result["results"][
                    "description"] = f"List of all Best Online | Virtual Schools in India for Admission {yearValue}. Check Fee Structure, Eligibility, Accreditation & Admission Dates | Forms etc"
            elif obj.slug == "boarding-schools":
                result["results"]["h1"] = f'Boarding Schools in India'
                result["results"]["title"] = f"Top Boarding Schools in India {yearValue} - Admission, Fees, Eligibility"
                result["results"]["description"] = f"List of all Top/Best Boarding Schools in India. Check the latest info about Admission Dates, Forms, Fees Structure & Eligibility Criteria etc."
            else:
                result["results"]["h1"] = f'Schools in {obj.name}'
                result["results"]["title"] = f"Best Schools in {obj.name} {yearValue} - Admission, Fees & Eligibility"
                result["results"]["description"] = f"List of all Top/Best Schools in {obj.name}. Check the latest info about Admission Dates, Form, Fees Structure & Eligibility Criteria etc."

        return Response(result,status=status.HTTP_200_OK)

class GroupedSchoolsFormView(APIView):
    def get(self,request,id,uid):
        def get_parent_address(address,city,state,country,pincode):
            final_address = ''
            if address:
                final_address = final_address + ', ' + address.capitalize()

            if city:
                final_address = final_address + ', ' + city.upper()

            if state:
                final_address = final_address + ', ' + state.upper()

            if country:
                final_address = final_address + ', ' + country.upper()

            if pincode:
                if final_address:
                    final_address = final_address + ', ' + str(pincode)
                else:
                    final_address = 'Pincode - ' + str(pincode)

            return final_address

        if GroupedSchools.objects.filter(api_key=id).exists():
            group=GroupedSchools.objects.filter(api_key=id)
            if group.first().is_active:
                if SchoolApplication.objects.filter(uid=uid).exists():
                    if group.filter(schools=SchoolApplication.objects.filter(uid=uid).first().school).exists():
                        app = SchoolApplication.objects.filter(uid=uid).first()
                        school = app.school
                        required_other_fields = school.required_admission_form_fields
                        required_child_fields = school.required_child_fields
                        required_father_fields = school.required_father_fields
                        required_mother_fields = school.required_mother_fields
                        required_guardian_fields = school.required_guardian_fields
                        notChangeableData = app.registration_data
                        serializedApplication = serializers.SchoolApplicationSerializer(app)
                        # serializer_da1 = CopyObjectSerializer(app.registration_data)
                        # data = {}
                        # data['results'] = serializer_da.data
                        # data['results1'] = serializer_da1.data
                        data = {}
                        data["results"]={}
                        data["results"]['child_details']={}
                        data["results"]['father_details']={}
                        data["results"]['mother_details']={}
                        data["results"]['guardian_details']={}
                        data["results"]['other_details']={}

                        # Serving points if school city is Delhi
                        if school.school_city.name == "Delhi":
                            data["results"]['point_details']={}
                            for item in serializedApplication.data:
                                if 'point' in str(item):
                                    field_name = str(item)
                                    field_value = getattr(app, field_name)
                                    if not field_value:
                                        field_value = 0
                                    data["results"]['point_details'][field_name]=field_value
                        # Serving all the default child required data
                        data["results"]['child_details']['child_name']=notChangeableData.child_name
                        data["results"]['child_details']['child_date_of_birth']=notChangeableData.child_date_of_birth
                        data["results"]['child_details']['child_nationality']=notChangeableData.child_nationality
                        data["results"]['child_details']['child_class_applying_for']=notChangeableData.child_class_applying_for.name
                        data["results"]['child_details']['child_religion']=notChangeableData.child_religion
                        data["results"]['child_details']['child_gender']=notChangeableData.child_gender
                        if notChangeableData.child_orphan:
                            data["results"]['child_details']['child_orphan']= 'yes'
                        else:
                            data["results"]['child_details']['child_orphan']= 'no'
                        if notChangeableData.child_intre_state_transfer:
                            data["results"]['child_details']['child_intre_state_transfer']= 'yes'
                        else:
                            data["results"]['child_details']['child_intre_state_transfer']= 'no'
                        data["results"]['child_details']["photo_path"]=notChangeableData.child_photo.url

                        # Serving all the default child required data
                        data["results"]['other_details']["short_address"]=notChangeableData.short_address
                        data["results"]['other_details']["street_address"]=notChangeableData.street_address
                        data["results"]['other_details']["city"]=notChangeableData.city
                        data["results"]['other_details']["state"]=notChangeableData.state
                        data["results"]['other_details']["pincode"]=notChangeableData.pincode
                        data["results"]['other_details']["country"]=notChangeableData.country
                        # Serving all the default Father required data
                        if not notChangeableData.child_orphan:
                            data["results"]['father_details']["name"]=notChangeableData.father_name
                            data["results"]['father_details']["phone"]=notChangeableData.father_phone
                            data["results"]['father_details']["email"]=notChangeableData.father_email
                            data["results"]['father_details']["date_of_birth"]=notChangeableData.father_date_of_birth
                            if notChangeableData.father_frontline_helper:
                                data["results"]['father_details']["covid_frontline_helper"]='yes'
                            else:
                                data["results"]['father_details']["covid_frontline_helper"]='no'
                            data["results"]['father_details']["photo_path"]=notChangeableData.father_photo.url

                        else:
                            data["results"]['father_details']["name"]=''
                            data["results"]['father_details']["phone"]=''
                            data["results"]['father_details']["email"]=''
                            data["results"]['father_details']["date_of_birth"]=''
                            data["results"]['father_details']["covid_frontline_helper"]=''
                            data["results"]['father_details']["photo_path"]=''
                        # Serving all the default Mother required data
                        if not notChangeableData.child_orphan:
                            data["results"]['mother_details']["name"]=notChangeableData.mother_name
                            data["results"]['mother_details']["phone"]=notChangeableData.mother_phone
                            data["results"]['mother_details']["email"]=notChangeableData.mother_email
                            data["results"]['mother_details']["date_of_birth"]=notChangeableData.mother_date_of_birth
                            if notChangeableData.mother_frontline_helper:
                                data["results"]['mother_details']["covid_frontline_helper"]='yes'
                            else:
                                data["results"]['mother_details']["covid_frontline_helper"]='no'
                            data["results"]['mother_details']["photo_path"]=notChangeableData.mother_photo.url

                        else:
                            data["results"]['mother_details']["name"]=''
                            data["results"]['mother_details']["phone"]=''
                            data["results"]['mother_details']["email"]=''
                            data["results"]['mother_details']["date_of_birth"]=''
                            data["results"]['mother_details']["covid_frontline_helper"]=''
                            data["results"]['mother_details']["photo_path"]=''
                        # Serving all the default Gaurdian required data
                        if notChangeableData.child_orphan:
                            data["results"]['guardian_details']["name"]=notChangeableData.guardian_name
                            data["results"]['guardian_details']["phone"]=notChangeableData.guardian_phone
                            data["results"]['guardian_details']["email"]=notChangeableData.guardian_email
                            data["results"]['guardian_details']["date_of_birth"]=notChangeableData.guardian_date_of_birth
                            if notChangeableData.guardian_frontline_helper:
                                data["results"]['guardian_details']["covid_frontline_helper"]='yes'
                            else:
                                data["results"]['guardian_details']["covid_frontline_helper"]='no'
                            data["results"]['guardian_details']["photo_path"]=notChangeableData.guardian_photo.url

                        else:
                            data["results"]['guardian_details']["name"]=''
                            data["results"]['guardian_details']["phone"]=''
                            data["results"]['guardian_details']["email"]=''
                            data["results"]['guardian_details']["date_of_birth"]=''
                            data["results"]['guardian_details']["covid_frontline_helper"]=''
                            data["results"]['guardian_details']["photo_path"]=''

                        # Serving all the required child required data
                        if "is_christian" in required_child_fields.keys():
                            if notChangeableData.child_is_christian:
                                data["results"]['child_details']["christian_sikh_muslim"]='yes'
                                if notChangeableData.child_minority_proof:
                                    data["results"]['child_details']["christian_sikh_muslim_proof_path"]=notChangeableData.child_minority_proof.url
                                else:
                                    data["results"]['child_details']["christian_sikh_muslim_proof_path"]=''
                            else:
                                data["results"]['child_details']["christian_sikh_muslim"]='no'
                                data["results"]['child_details']["christian_sikh_muslim_proof_path"]=''
                        else:
                            data["results"]['child_details']["christian_sikh_muslim"]=''
                            data["results"]['child_details']["christian_sikh_muslim_proof_path"]=''
                        if "birth_certificate" in required_child_fields.keys():
                            if notChangeableData.child_birth_certificate:
                                data["results"]['child_details']["birth_certificate_path_path"]=notChangeableData.child_birth_certificate.url
                            else:
                                data["results"]['child_details']["birth_certificate_path_path"]=''
                        else:
                            data["results"]['child_details']["birth_certificate"]=''
                        if "medical_certificate" in required_child_fields.keys():
                            if notChangeableData.child_medical_certificate:
                                data["results"]['child_details']["medical_certificate_path"]=notChangeableData.child_medical_certificate.url
                            else:
                                data["results"]['child_details']["medical_certificate_path"]=''
                        else:
                            data["results"]['child_details']["medical_certificate_path"]=''
                        if "address_proof" in required_child_fields.keys():
                            if notChangeableData.child_address_proof:
                                data["results"]['child_details']["address_proof_path"]=notChangeableData.child_address_proof.url
                            else:
                                data["results"]['child_details']["address_proof_path"]=''
                        else:
                            data["results"]['child_details']["address_proof_path"]=''
                        if "address_proof2" in required_child_fields.keys():
                            if notChangeableData.child_address_proof2:
                                data["results"]['child_details']["address_proof_2_path"]=notChangeableData.child_address_proof2.url
                            else:
                                data["results"]['child_details']["address_proof_2_path"]=''
                        else:
                            data["results"]['child_details']["address_proof_2_path"]=''

                        if "vaccination_card" in required_child_fields.keys():
                            if notChangeableData.child_vaccination_card:
                                data["results"]['child_details']["vaccination_card_path"]=notChangeableData.child_vaccination_card.url
                            else:
                                data["results"]['child_details']["vaccination_card_path"]=''
                        else:
                            data["results"]['child_details']["vaccination_card_path"]=''

                        if "blood_group" in required_child_fields.keys():
                            if notChangeableData.child_blood_group:
                                data["results"]['child_details']["blood_group"]=notChangeableData.child_blood_group
                            else:
                                data["results"]['child_details']["blood_group"]=''
                        else:
                            data["results"]['child_details']["blood_group"]=''

                        if "armed_force_points" in required_child_fields.keys():
                            if notChangeableData.child_armed_force_points:
                                data["results"]['child_details']["ward_of_deffence_or_armed_personal"]=notChangeableData.child_armed_force_points
                            else:
                                data["results"]['child_details']["ward_of_deffence_or_armed_personal"]=''
                        else:
                            data["results"]['child_details']["ward_of_deffence_or_armed_personal"]=''

                        if "armed_force_proof" in required_child_fields.keys():
                            if notChangeableData.child_armed_force_proof:
                                data["results"]['child_details']["ward_of_deffence_or_armed_personal_proof_path"]=notChangeableData.child_armed_force_proof.url
                            else:
                                data["results"]['child_details']["ward_of_deffence_or_armed_personal_proof_path"]=''
                        else:
                            data["results"]['child_details']["ward_of_deffence_or_armed_personal_proof_path"]=''

                        if "student_with_special_needs_points" in required_child_fields.keys():
                            if notChangeableData.child_student_with_special_needs_points:
                                data["results"]['child_details']["require_special_needs"]=notChangeableData.child_student_with_special_needs_points
                            else:
                                data["results"]['child_details']["require_special_needs"]=''
                        else:
                            data["results"]['child_details']["require_with_special"]=''

                        if "aadhaar_card_number" in required_child_fields.keys():
                            if notChangeableData.child_aadhaar_number:
                                data["results"]['child_details']["aadhaar_card_number"]=notChangeableData.child_aadhaar_number
                            else:
                                data["results"]['child_details']["aadhaar_card_number"]=''
                        else:
                            data["results"]['child_details']["aadhaar_card_number"]=''

                        if "aadhaar_card_proof" in required_child_fields.keys():
                            if notChangeableData.child_aadhaar_card_proof:
                                data["results"]['child_details']["aadhaar_card_image_path"]=notChangeableData.child_aadhaar_card_proof.url
                            else:
                                data["results"]['child_details']["aadhaar_card_image_path"]=''
                        else:
                            data["results"]['child_details']["aadhaar_card_image_path"]=''

                        if "aadhaar_card_proof" in required_child_fields.keys():
                            if notChangeableData.child_aadhaar_card_proof:
                                data["results"]['child_details']["aadhaar_card_image_path"]=notChangeableData.child_aadhaar_card_proof.url
                            else:
                                data["results"]['child_details']["aadhaar_card_image_path"]=''
                        else:
                            data["results"]['child_details']["aadhaar_card_image_path"]=''

                        if "illness" in required_child_fields.keys():
                            if notChangeableData.child_illness:
                                data["results"]['child_details']["illness_diseases_allergy"]=notChangeableData.child_illness
                            else:
                                data["results"]['child_details']["illness_diseases_allergy"]=''
                        else:
                            data["results"]['child_details']["illness_diseases_allergy"]=''

                        if "differently_abled_proof" in required_other_fields.keys():
                            if notChangeableData.differently_abled_proof:
                                data["results"]['child_details']["differently_abled"]='yes'
                                data["results"]['child_details']["differently_abled_proof_path"]=notChangeableData.differently_abled_proof.url
                            else:
                                data["results"]['child_details']["differently_abled"]='no'
                                data["results"]['child_details']["differently_abled_proof_path"]=''
                        else:
                            data["results"]['child_details']["differently_abled"]='no'
                            data["results"]['child_details']["differently_abled_proof_path"]=''

                        if not notChangeableData.child_orphan:
                            # Serving all the required father required data
                            if "occupation" in required_father_fields.keys():
                                if notChangeableData.father_occupation:
                                    data["results"]['father_details']["occupation"]=notChangeableData.father_occupation
                                else:
                                    data["results"]['father_details']["occupation"]=''
                            else:
                                data["results"]['father_details']["occupation"]=''

                            if "designation" in required_father_fields.keys():
                                if notChangeableData.father_designation:
                                    data["results"]['father_details']["designation"]=notChangeableData.father_designation
                                else:
                                    data["results"]['father_details']["designation"]=''
                            else:
                                data["results"]['father_details']["designation"]=''

                            if "profession" in required_father_fields.keys():
                                if notChangeableData.father_profession:
                                    data["results"]['father_details']["profession"]=notChangeableData.father_profession
                                else:
                                    data["results"]['father_details']["profession"]=''
                            else:
                                data["results"]['father_details']["profession"]=''

                            if "office_address" in required_father_fields.keys():
                                if notChangeableData.father_office_address:
                                    data["results"]['father_details']["office_address"]=notChangeableData.father_office_address
                                else:
                                    data["results"]['father_details']["office_address"]=''
                            else:
                                data["results"]['father_details']["office_address"]=''

                            if "office_number" in required_father_fields.keys():
                                if notChangeableData.father_office_number:
                                    data["results"]['father_details']["office_contact_number"]=notChangeableData.father_office_number
                                else:
                                    data["results"]['father_details']["office_contact_number"]=''
                            else:
                                data["results"]['father_details']["office_contact_number"]=''

                            if "education" in required_father_fields.keys():
                                if notChangeableData.father_education:
                                    data["results"]['father_details']["qualification"]=notChangeableData.father_education
                                else:
                                    data["results"]['father_details']["qualification"]=''
                                if notChangeableData.father_college_name:
                                    data["results"]['father_details']["institute_name"]=notChangeableData.father_college_name
                                else:
                                    data["results"]['father_details']["institute_name"]=''
                                if notChangeableData.father_course_name:
                                    data["results"]['father_details']["course_name"]=notChangeableData.father_course_name
                                else:
                                    data["results"]['father_details']["course_name"]=''
                            else:
                                data["results"]['father_details']["qualification"]=''
                                data["results"]['father_details']["institute_name"]=''
                                data["results"]['father_details']["course_name"]=''

                            if "income" in required_father_fields.keys():
                                if notChangeableData.father_income:
                                    data["results"]['father_details']["income"]=notChangeableData.father_income
                                else:
                                    data["results"]['father_details']["income"]=''
                            else:
                                data["results"]['father_details']["income"]=''

                            if "aadhaar_card_number" in required_father_fields.keys():
                                if notChangeableData.father_aadhaar_number:
                                    data["results"]['father_details']["aadhaar_card_number"]=notChangeableData.father_aadhaar_number
                                else:
                                    data["results"]['father_details']["aadhaar_card_number"]=''
                            else:
                                data["results"]['father_details']["aadhaar_card_number"]=''

                            if "parent_aadhar_card" in required_father_fields.keys():
                                if notChangeableData.father_parent_aadhar_card:
                                    data["results"]['father_details']["aadhaar_card_image"]=notChangeableData.father_parent_aadhar_card.url
                                else:
                                    data["results"]['father_details']["aadhaar_card_image"]=''
                            else:
                                data["results"]['father_details']["aadhaar_card_image"]=''

                            if "alumni_proof" in required_father_fields.keys() and "alumni_school_name" in required_father_fields.keys() and "alumni_school_name" in required_father_fields.keys() and "alumni_year_of_passing" in required_father_fields.keys():
                                if notChangeableData.father_alumni_school_name and notChangeableData.father_alumni_school_name.name == school.name:
                                    data["results"]['father_details']["alumni_of_school"]= 'yes'

                                    if notChangeableData.father_alumni_year_of_passing:
                                        data["results"]['father_details']["year_of_passing"]= notChangeableData.father_alumni_year_of_passing
                                    else:
                                        data["results"]['father_details']["year_of_passing"]=''

                                    if notChangeableData.father_passing_class:
                                        data["results"]['father_details']["passing_class"]= notChangeableData.father_passing_class
                                    else:
                                        data["results"]['father_details']["passing_class"]=''

                                    if notChangeableData.father_alumni_proof:
                                        data["results"]['father_details']["alumni_proof_path"]= notChangeableData.father_alumni_proof.url
                                    else:
                                        data["results"]['father_details']["alumni_proof_path"]=''


                                else:
                                    data["results"]['father_details']["alumni_of_school"]= 'no'
                                    data["results"]['father_details']["year_of_passing"]=''
                                    data["results"]['father_details']["passing_class"]=''
                                    data["results"]['father_details']["alumni_proof_path"]=''

                            else:
                                data["results"]['father_details']["alumni_of_school"]= 'no'
                                data["results"]['father_details']["year_of_passing"]=''
                                data["results"]['father_details']["passing_class"]=''
                                data["results"]['father_details']["alumni_proof_path"]=''

                            if "city" in required_father_fields.keys() and "state" in required_father_fields.keys() and "country" in required_father_fields.keys() and "pincode" in required_father_fields.keys() and "short_address" in required_father_fields.keys() and "street_address" in required_father_fields.keys():
                                address = get_parent_address(notChangeableData.father_street_address, notChangeableData.father_city, notChangeableData.father_state, notChangeableData.father_country, notChangeableData.father_pincode)

                                data["results"]['father_details']["residential_details"]= address

                            else:
                                data["results"]['father_details']["residential_details"]= ''

                            if "pan_card_proof" in required_father_fields.keys():
                                if notChangeableData.father_pan_card_proof:
                                    data["results"]['father_details']["pan_card_image_path"]=notChangeableData.father_pan_card_proof.url
                                else:
                                    data["results"]['father_details']["pan_card_image_path"]=''
                            else:
                                data["results"]['father_details']["pan_card_image_path"]=''

                            if "special_ground" in required_father_fields.keys():
                                if notChangeableData.father_special_ground_proof:
                                    data["results"]['father_details']["in_sports_or_won_national_award_image_path"]=notChangeableData.father_special_ground_proof.url
                                else:
                                    data["results"]['father_details']["in_sports_or_won_national_award_image_path"]=''
                            else:
                                data["results"]['father_details']["in_sports_or_won_national_award_image_path"]=''

                            if "transferable_job" in required_father_fields.keys():
                                if notChangeableData.father_transferable_job:
                                    data["results"]['father_details']["transferable_job"]='yes'
                                else:
                                    data["results"]['father_details']["transferable_job"]='no'
                            else:
                                data["results"]['father_details']["transferable_job"]=''

                            if "covid_vaccination_certificate" in required_father_fields.keys():
                                if notChangeableData.father_covid_vaccination_certificate:
                                    data["results"]['father_details']["covid_vaccination_certificate_image_path"]=notChangeableData.father_covid_vaccination_certificate.url
                                else:
                                    data["results"]['father_details']["covid_vaccination_certificate_image_path"]=''
                            else:
                                data["results"]['father_details']["covid_vaccination_certificate_image_path"]=''

                            if "staff_ward" in required_other_fields.keys():
                                if notChangeableData.staff_ward:
                                    if father_staff_ward_school_name and father_staff_ward_school_name.name == school.name:
                                        data["results"]['father_details']["staff_ward"]='yes'
                                        if notChangeableData.father_staff_ward_department:
                                            data["results"]['father_details']["staff_ward_department"]=notChangeableData.father_staff_ward_department
                                        else:
                                            data["results"]['father_details']["staff_ward_department"]=''
                                        if notChangeableData.father_type_of_staff_ward:
                                            data["results"]['father_details']["type_of_staff_ward"]=notChangeableData.father_type_of_staff_ward
                                        else:
                                            data["results"]['father_details']["type_of_staff_ward"]=''
                                        if notChangeableData.father_staff_ward_tenure:
                                            data["results"]['father_details']["staff_ward_tenure"]=notChangeableData.father_staff_ward_tenure
                                        else:
                                            data["results"]['father_details']["staff_ward_tenure"]=''
                                    else:
                                        data["results"]['father_details']["staff_ward"]='no'
                                        data["results"]['father_details']["staff_ward_department"]=''
                                        data["results"]['father_details']["type_of_staff_ward"]=''
                                        data["results"]['father_details']["staff_ward_tenure"]=''
                                else:
                                    data["results"]['father_details']["staff_ward"]='no'
                                    data["results"]['father_details']["staff_ward_department"]=''
                                    data["results"]['father_details']["type_of_staff_ward"]=''
                                    data["results"]['father_details']["staff_ward_tenure"]=''
                            else:
                                data["results"]['father_details']["staff_ward"]=''
                                data["results"]['father_details']["staff_ward_department"]=''
                                data["results"]['father_details']["type_of_staff_ward"]=''
                                data["results"]['father_details']["staff_ward_tenure"]=''

                            # Serving all the required mother required data
                            if "occupation" in required_mother_fields.keys():
                                if notChangeableData.mother_occupation:
                                    data["results"]['mother_details']["occupation"]=notChangeableData.mother_occupation
                                else:
                                    data["results"]['mother_details']["occupation"]=''
                            else:
                                data["results"]['mother_details']["occupation"]=''

                            if "designation" in required_mother_fields.keys():
                                if notChangeableData.mother_designation:
                                    data["results"]['mother_details']["designation"]=notChangeableData.mother_designation
                                else:
                                    data["results"]['mother_details']["designation"]=''
                            else:
                                data["results"]['mother_details']["designation"]=''

                            if "profession" in required_mother_fields.keys():
                                if notChangeableData.mother_profession:
                                    data["results"]['mother_details']["profession"]=notChangeableData.mother_profession
                                else:
                                    data["results"]['mother_details']["profession"]=''
                            else:
                                data["results"]['mother_details']["profession"]=''

                            if "office_address" in required_mother_fields.keys():
                                if notChangeableData.mother_office_address:
                                    data["results"]['mother_details']["office_address"]=notChangeableData.mother_office_address
                                else:
                                    data["results"]['mother_details']["office_address"]=''
                            else:
                                data["results"]['mother_details']["office_address"]=''

                            if "office_number" in required_mother_fields.keys():
                                if notChangeableData.mother_office_number:
                                    data["results"]['mother_details']["office_contact_number"]=notChangeableData.mother_office_number
                                else:
                                    data["results"]['mother_details']["office_contact_number"]=''
                            else:
                                data["results"]['mother_details']["office_contact_number"]=''

                            if "education" in required_mother_fields.keys():
                                if notChangeableData.mother_education:
                                    data["results"]['mother_details']["qualification"]=notChangeableData.mother_education
                                else:
                                    data["results"]['mother_details']["qualification"]=''
                                if notChangeableData.mother_college_name:
                                    data["results"]['mother_details']["institute_name"]=notChangeableData.mother_college_name
                                else:
                                    data["results"]['mother_details']["institute_name"]=''
                                if notChangeableData.mother_course_name:
                                    data["results"]['mother_details']["course_name"]=notChangeableData.mother_course_name
                                else:
                                    data["results"]['mother_details']["course_name"]=''
                            else:
                                data["results"]['mother_details']["qualification"]=''
                                data["results"]['mother_details']["institute_name"]=''
                                data["results"]['mother_details']["course_name"]=''

                            if "income" in required_mother_fields.keys():
                                if notChangeableData.mother_income:
                                    data["results"]['mother_details']["income"]=notChangeableData.mother_income
                                else:
                                    data["results"]['mother_details']["income"]=''
                            else:
                                data["results"]['mother_details']["income"]=''

                            if "aadhaar_card_number" in required_mother_fields.keys():
                                if notChangeableData.mother_aadhaar_number:
                                    data["results"]['mother_details']["aadhaar_card_number"]=notChangeableData.mother_aadhaar_number
                                else:
                                    data["results"]['mother_details']["aadhaar_card_number"]=''
                            else:
                                data["results"]['mother_details']["aadhaar_card_number"]=''

                            if "parent_aadhar_card" in required_mother_fields.keys():
                                if notChangeableData.mother_parent_aadhar_card:
                                    data["results"]['mother_details']["aadhaar_card_image_path"]=notChangeableData.mother_parent_aadhar_card.url
                                else:
                                    data["results"]['mother_details']["aadhaar_card_image_path"]=''
                            else:
                                data["results"]['mother_details']["aadhaar_card_image_path"]=''

                            if "alumni_proof" in required_mother_fields.keys() and "alumni_school_name" in required_mother_fields.keys() and "alumni_school_name" in required_mother_fields.keys() and "alumni_year_of_passing" in required_mother_fields.keys():
                                if notChangeableData.mother_alumni_school_name and notChangeableData.mother_alumni_school_name.name == school.name:
                                    data["results"]['mother_details']["alumni_of_school"]= 'yes'

                                    if notChangeableData.mother_alumni_year_of_passing:
                                        data["results"]['mother_details']["year_of_passing"]= notChangeableData.mother_alumni_year_of_passing
                                    else:
                                        data["results"]['mother_details']["year_of_passing"]=''

                                    if notChangeableData.mother_passing_class:
                                        data["results"]['mother_details']["passing_class"]= notChangeableData.mother_passing_class
                                    else:
                                        data["results"]['mother_details']["passing_class"]=''

                                    if notChangeableData.mother_alumni_proof:
                                        data["results"]['mother_details']["alumni_proof_path"]= notChangeableData.mother_alumni_proof.url
                                    else:
                                        data["results"]['mother_details']["alumni_proof_path"]=''


                                else:
                                    data["results"]['mother_details']["alumni_of_school"]= 'no'
                                    data["results"]['mother_details']["year_of_passing"]=''
                                    data["results"]['mother_details']["passing_class"]=''
                                    data["results"]['mother_details']["alumni_proof_path"]=''

                            else:
                                data["results"]['mother_details']["alumni_of_school"]= 'no'
                                data["results"]['mother_details']["year_of_passing"]=''
                                data["results"]['mother_details']["passing_class"]=''
                                data["results"]['mother_details']["alumni_proof_path"]=''

                            if "city" in required_mother_fields.keys() and "state" in required_mother_fields.keys() and "country" in required_mother_fields.keys() and "pincode" in required_mother_fields.keys() and "short_address" in required_mother_fields.keys() and "street_address" in required_mother_fields.keys():
                                address = get_parent_address(notChangeableData.mother_street_address, notChangeableData.mother_city, notChangeableData.mother_state, notChangeableData.mother_country, notChangeableData.mother_pincode)

                                data["results"]['mother_details']["residential_details"]= address

                            else:
                                data["results"]['mother_details']["residential_details"]= ''

                            if "pan_card_proof" in required_mother_fields.keys():
                                if notChangeableData.mother_pan_card_proof:
                                    data["results"]['mother_details']["pan_card_image_path"]=notChangeableData.mother_pan_card_proof.url
                                else:
                                    data["results"]['mother_details']["pan_card_image_path"]=''
                            else:
                                data["results"]['mother_details']["pan_card_image_path"]=''

                            if "special_ground" in required_mother_fields.keys():
                                if notChangeableData.mother_special_ground_proof:
                                    data["results"]['mother_details']["in_sports_or_won_national_award_image_path"]=notChangeableData.mother_special_ground_proof.url
                                else:
                                    data["results"]['mother_details']["in_sports_or_won_national_award_image_path"]=''
                            else:
                                data["results"]['mother_details']["in_sports_or_won_national_award_image_path"]=''

                            if "transferable_job" in required_mother_fields.keys():
                                if notChangeableData.mother_transferable_job:
                                    data["results"]['mother_details']["transferable_job"]='yes'
                                else:
                                    data["results"]['mother_details']["transferable_job"]='no'
                            else:
                                data["results"]['mother_details']["transferable_job"]=''

                            if "covid_vaccination_certificate" in required_mother_fields.keys():
                                if notChangeableData.mother_covid_vaccination_certificate:
                                    data["results"]['mother_details']["covid_vaccination_certificate_image_path"]=notChangeableData.mother_covid_vaccination_certificate.url
                                else:
                                    data["results"]['mother_details']["covid_vaccination_certificate_image_path"]=''
                            else:
                                data["results"]['mother_details']["covid_vaccination_certificate_image_path"]=''

                            if "staff_ward" in required_other_fields.keys():
                                if notChangeableData.staff_ward:
                                    if mother_staff_ward_school_name and mother_staff_ward_school_name.name == school.name:
                                        data["results"]['mother_details']["staff_ward"]='yes'
                                        if notChangeableData.mother_staff_ward_department:
                                            data["results"]['mother_details']["staff_ward_department"]=notChangeableData.mother_staff_ward_department
                                        else:
                                            data["results"]['mother_details']["staff_ward_department"]=''
                                        if notChangeableData.mother_type_of_staff_ward:
                                            data["results"]['mother_details']["type_of_staff_ward"]=notChangeableData.mother_type_of_staff_ward
                                        else:
                                            data["results"]['mother_details']["type_of_staff_ward"]=''
                                        if notChangeableData.mother_staff_ward_tenure:
                                            data["results"]['mother_details']["staff_ward_tenure"]=notChangeableData.mother_staff_ward_tenure
                                        else:
                                            data["results"]['mother_details']["staff_ward_tenure"]=''
                                    else:
                                        data["results"]['mother_details']["staff_ward"]='no'
                                        data["results"]['mother_details']["staff_ward_department"]=''
                                        data["results"]['mother_details']["type_of_staff_ward"]=''
                                        data["results"]['mother_details']["staff_ward_tenure"]=''
                                else:
                                    data["results"]['mother_details']["staff_ward"]='no'
                                    data["results"]['mother_details']["staff_ward_department"]=''
                                    data["results"]['mother_details']["type_of_staff_ward"]=''
                                    data["results"]['mother_details']["staff_ward_tenure"]=''
                            else:
                                data["results"]['mother_details']["staff_ward"]=''
                                data["results"]['mother_details']["staff_ward_department"]=''
                                data["results"]['mother_details']["type_of_staff_ward"]=''
                                data["results"]['mother_details']["staff_ward_tenure"]=''

                            # making all the guardian data blank
                            data["results"]['guardian_details']["occupation"]=''
                            data["results"]['guardian_details']["designation"]=''
                            data["results"]['guardian_details']["profession"]=''
                            data["results"]['guardian_details']["office_address"]=''
                            data["results"]['guardian_details']["office_contact_number"]=''
                            data["results"]['guardian_details']["qualification"]=''
                            data["results"]['guardian_details']["institute_name"]=''
                            data["results"]['guardian_details']["course_name"]=''
                            data["results"]['guardian_details']["income"]=''
                            data["results"]['guardian_details']["aadhaar_card_number"]=''
                            data["results"]['guardian_details']["aadhaar_card_image_path"]=''
                            data["results"]['guardian_details']["alumni_of_school"]=''
                            data["results"]['guardian_details']["year_of_passing"]=''
                            data["results"]['guardian_details']["passing_class"]=''
                            data["results"]['guardian_details']["alumni_proof_path"]=''
                            data["results"]['guardian_details']["residential_details"]=''
                            data["results"]['guardian_details']["pan_card_image_path"]=''
                            data["results"]['guardian_details']["in_sports_or_won_national_award_image_path"]=''
                            data["results"]['guardian_details']["transferable_job"]=''
                            data["results"]['guardian_details']["covid_vaccination_certificate_image_path"]=''
                            data["results"]['guardian_details']["staff_ward"]=''
                            data["results"]['guardian_details']["staff_ward_department"]=''
                            data["results"]['guardian_details']["type_of_staff_ward"]=''
                            data["results"]['guardian_details']["staff_ward_tenure"]=''

                        else:
                            # making all father data null
                            data["results"]['father_details']["occupation"]=''
                            data["results"]['father_details']["designation"]=''
                            data["results"]['father_details']["profession"]=''
                            data["results"]['father_details']["office_address"]=''
                            data["results"]['father_details']["office_contact_number"]=''
                            data["results"]['father_details']["qualification"]=''
                            data["results"]['father_details']["institute_name"]=''
                            data["results"]['father_details']["course_name"]=''
                            data["results"]['father_details']["income"]=''
                            data["results"]['father_details']["aadhaar_card_number"]=''
                            data["results"]['father_details']["aadhaar_card_image_path"]=''
                            data["results"]['father_details']["alumni_of_school"]=''
                            data["results"]['father_details']["year_of_passing"]=''
                            data["results"]['father_details']["passing_class"]=''
                            data["results"]['father_details']["alumni_proof_path"]=''
                            data["results"]['father_details']["residential_details"]=''
                            data["results"]['father_details']["pan_card_image_path"]=''
                            data["results"]['father_details']["in_sports_or_won_national_award_image_path"]=''
                            data["results"]['father_details']["transferable_job"]=''
                            data["results"]['father_details']["covid_vaccination_certificate_image_path"]=''
                            data["results"]['father_details']["staff_ward"]=''
                            data["results"]['father_details']["staff_ward_department"]=''
                            data["results"]['father_details']["type_of_staff_ward"]=''
                            data["results"]['father_details']["staff_ward_tenure"]=''
                            # making all mother data null
                            data["results"]['mother_details']["occupation"]=''
                            data["results"]['mother_details']["designation"]=''
                            data["results"]['mother_details']["profession"]=''
                            data["results"]['mother_details']["office_address"]=''
                            data["results"]['mother_details']["office_contact_number"]=''
                            data["results"]['mother_details']["qualification"]=''
                            data["results"]['mother_details']["institute_name"]=''
                            data["results"]['mother_details']["course_name"]=''
                            data["results"]['mother_details']["income"]=''
                            data["results"]['mother_details']["aadhaar_card_number"]=''
                            data["results"]['mother_details']["aadhaar_card_image_path"]=''
                            data["results"]['mother_details']["alumni_of_school"]=''
                            data["results"]['mother_details']["year_of_passing"]=''
                            data["results"]['mother_details']["passing_class"]=''
                            data["results"]['mother_details']["alumni_proof_path"]=''
                            data["results"]['mother_details']["residential_details"]=''
                            data["results"]['mother_details']["pan_card_image_path"]=''
                            data["results"]['mother_details']["in_sports_or_won_national_award_image_path"]=''
                            data["results"]['mother_details']["transferable_job"]=''
                            data["results"]['mother_details']["covid_vaccination_certificate_image_path"]=''
                            data["results"]['mother_details']["staff_ward"]=''
                            data["results"]['mother_details']["staff_ward_department"]=''
                            data["results"]['mother_details']["type_of_staff_ward"]=''
                            data["results"]['mother_details']["staff_ward_tenure"]=''


                            # Serving all the required guardian required data
                            if "occupation" in required_guardian_fields.keys():
                                if notChangeableData.guardian_occupation:
                                    data["results"]['guardian_details']["occupation"]=notChangeableData.guardian_occupation
                                else:
                                    data["results"]['guardian_details']["occupation"]=''
                            else:
                                data["results"]['guardian_details']["occupation"]=''

                            if "designation" in required_guardian_fields.keys():
                                if notChangeableData.guardian_designation:
                                    data["results"]['guardian_details']["designation"]=notChangeableData.guardian_designation
                                else:
                                    data["results"]['guardian_details']["designation"]=''
                            else:
                                data["results"]['guardian_details']["designation"]=''

                            if "profession" in required_guardian_fields.keys():
                                if notChangeableData.guardian_profession:
                                    data["results"]['guardian_details']["profession"]=notChangeableData.guardian_profession
                                else:
                                    data["results"]['guardian_details']["profession"]=''
                            else:
                                data["results"]['guardian_details']["profession"]=''

                            if "office_address" in required_guardian_fields.keys():
                                if notChangeableData.guardian_office_address:
                                    data["results"]['guardian_details']["office_address"]=notChangeableData.guardian_office_address
                                else:
                                    data["results"]['guardian_details']["office_address"]=''
                            else:
                                data["results"]['guardian_details']["office_address"]=''

                            if "office_number" in required_guardian_fields.keys():
                                if notChangeableData.guardian_office_number:
                                    data["results"]['guardian_details']["office_contact_number"]=notChangeableData.guardian_office_number
                                else:
                                    data["results"]['guardian_details']["office_contact_number"]=''
                            else:
                                data["results"]['guardian_details']["office_contact_number"]=''

                            if "education" in required_guardian_fields.keys():
                                if notChangeableData.guardian_education:
                                    data["results"]['guardian_details']["qualification"]=notChangeableData.guardian_education
                                else:
                                    data["results"]['guardian_details']["qualification"]=''
                                if notChangeableData.guardian_college_name:
                                    data["results"]['guardian_details']["institute_name"]=notChangeableData.guardian_college_name
                                else:
                                    data["results"]['guardian_details']["institute_name"]=''
                                if notChangeableData.guardian_course_name:
                                    data["results"]['guardian_details']["course_name"]=notChangeableData.guardian_course_name
                                else:
                                    data["results"]['guardian_details']["course_name"]=''
                            else:
                                data["results"]['guardian_details']["qualification"]=''
                                data["results"]['guardian_details']["institute_name"]=''
                                data["results"]['guardian_details']["course_name"]=''

                            if "income" in required_guardian_fields.keys():
                                if notChangeableData.guardian_income:
                                    data["results"]['guardian_details']["income"]=notChangeableData.guardian_income
                                else:
                                    data["results"]['guardian_details']["income"]=''
                            else:
                                data["results"]['guardian_details']["income"]=''

                            if "aadhaar_card_number" in required_guardian_fields.keys():
                                if notChangeableData.guardian_aadhaar_number:
                                    data["results"]['guardian_details']["aadhaar_card_number"]=notChangeableData.guardian_aadhaar_number
                                else:
                                    data["results"]['guardian_details']["aadhaar_card_number"]=''
                            else:
                                data["results"]['guardian_details']["aadhaar_card_number"]=''

                            if "parent_aadhar_card" in required_guardian_fields.keys():
                                if notChangeableData.guardian_parent_aadhar_card:
                                    data["results"]['guardian_details']["aadhaar_card_image_path"]=notChangeableData.guardian_parent_aadhar_card.url
                                else:
                                    data["results"]['guardian_details']["aadhaar_card_image_path"]=''
                            else:
                                data["results"]['guardian_details']["aadhaar_card_image_path"]=''

                            if "alumni_proof" in required_guardian_fields.keys() and "alumni_school_name" in required_guardian_fields.keys() and "alumni_school_name" in required_guardian_fields.keys() and "alumni_year_of_passing" in required_guardian_fields.keys():
                                if notChangeableData.guardian_alumni_school_name and notChangeableData.guardian_alumni_school_name.name == school.name:
                                    data["results"]['guardian_details']["alumni_of_school"]= 'yes'

                                    if notChangeableData.guardian_alumni_year_of_passing:
                                        data["results"]['guardian_details']["year_of_passing"]= notChangeableData.guardian_alumni_year_of_passing
                                    else:
                                        data["results"]['guardian_details']["year_of_passing"]=''

                                    if notChangeableData.guardian_passing_class:
                                        data["results"]['guardian_details']["passing_class"]= notChangeableData.guardian_passing_class
                                    else:
                                        data["results"]['guardian_details']["passing_class"]=''

                                    if notChangeableData.guardian_alumni_proof:
                                        data["results"]['guardian_details']["alumni_proof_path"]= notChangeableData.guardian_alumni_proof.url
                                    else:
                                        data["results"]['guardian_details']["alumni_proof_path"]=''


                                else:
                                    data["results"]['guardian_details']["alumni_of_school"]= 'no'
                                    data["results"]['guardian_details']["year_of_passing"]=''
                                    data["results"]['guardian_details']["passing_class"]=''
                                    data["results"]['guardian_details']["alumni_proof_path"]=''

                            else:
                                data["results"]['guardian_details']["alumni_of_school"]= 'no'
                                data["results"]['guardian_details']["year_of_passing"]=''
                                data["results"]['guardian_details']["passing_class"]=''
                                data["results"]['guardian_details']["alumni_proof_path"]=''

                            if "city" in required_guardian_fields.keys() and "state" in required_guardian_fields.keys() and "country" in required_guardian_fields.keys() and "pincode" in required_guardian_fields.keys() and "short_address" in required_guardian_fields.keys() and "street_address" in required_guardian_fields.keys():
                                address = get_parent_address(notChangeableData.guardian_street_address, notChangeableData.guardian_city, notChangeableData.guardian_state, notChangeableData.guardian_country, notChangeableData.guardian_pincode)

                                data["results"]['guardian_details']["residential_details"]= address

                            else:
                                data["results"]['guardian_details']["residential_details"]= ''

                            if "pan_card_proof" in required_guardian_fields.keys():
                                if notChangeableData.guardian_pan_card_proof:
                                    data["results"]['guardian_details']["pan_card_image_path"]=notChangeableData.guardian_pan_card_proof.url
                                else:
                                    data["results"]['guardian_details']["pan_card_image_path"]=''
                            else:
                                data["results"]['guardian_details']["pan_card_image_path"]=''

                            if "special_ground" in required_guardian_fields.keys():
                                if notChangeableData.guardian_special_ground_proof:
                                    data["results"]['guardian_details']["in_sports_or_won_national_award_image"]=notChangeableData.guardian_special_ground_proof.url
                                else:
                                    data["results"]['guardian_details']["in_sports_or_won_national_award_image"]=''
                            else:
                                data["results"]['guardian_details']["in_sports_or_won_national_award_image"]=''

                            if "transferable_job" in required_guardian_fields.keys():
                                if notChangeableData.guardian_transferable_job:
                                    data["results"]['guardian_details']["transferable_job"]='yes'
                                else:
                                    data["results"]['guardian_details']["transferable_job"]='no'
                            else:
                                data["results"]['guardian_details']["transferable_job"]=''

                            if "covid_vaccination_certificate" in required_guardian_fields.keys():
                                if notChangeableData.guardian_covid_vaccination_certificate:
                                    data["results"]['guardian_details']["covid_vaccination_certificate_image_path"]=notChangeableData.guardian_covid_vaccination_certificate.url
                                else:
                                    data["results"]['guardian_details']["covid_vaccination_certificate_image_path"]=''
                            else:
                                data["results"]['guardian_details']["covid_vaccination_certificate_image_path"]=''

                            if "staff_ward" in required_other_fields.keys():
                                if notChangeableData.staff_ward:
                                    if guardian_staff_ward_school_name and guardian_staff_ward_school_name.name == school.name:
                                        data["results"]['guardian_details']["staff_ward"]='yes'
                                        if notChangeableData.guardian_staff_ward_department:
                                            data["results"]['guardian_details']["staff_ward_department"]=notChangeableData.guardian_staff_ward_department
                                        else:
                                            data["results"]['guardian_details']["staff_ward_department"]=''
                                        if notChangeableData.guardian_type_of_staff_ward:
                                            data["results"]['guardian_details']["type_of_staff_ward"]=notChangeableData.guardian_type_of_staff_ward
                                        else:
                                            data["results"]['guardian_details']["type_of_staff_ward"]=''
                                        if notChangeableData.guardian_staff_ward_tenure:
                                            data["results"]['guardian_details']["staff_ward_tenure"]=notChangeableData.guardian_staff_ward_tenure
                                        else:
                                            data["results"]['guardian_details']["staff_ward_tenure"]=''
                                    else:
                                        data["results"]['guardian_details']["staff_ward"]='no'
                                        data["results"]['guardian_details']["staff_ward_department"]=''
                                        data["results"]['guardian_details']["type_of_staff_ward"]=''
                                        data["results"]['guardian_details']["staff_ward_tenure"]=''
                                else:
                                    data["results"]['guardian_details']["staff_ward"]='no'
                                    data["results"]['guardian_details']["staff_ward_department"]=''
                                    data["results"]['guardian_details']["type_of_staff_ward"]=''
                                    data["results"]['guardian_details']["staff_ward_tenure"]=''
                            else:
                                data["results"]['guardian_details']["staff_ward"]=''
                                data["results"]['guardian_details']["staff_ward_department"]=''
                                data["results"]['guardian_details']["type_of_staff_ward"]=''
                                data["results"]['guardian_details']["staff_ward_tenure"]=''


                        # getting all other details
                        if "category" in required_other_fields.keys():
                            if notChangeableData.category:
                                data["results"]['other_details']["caste_or_category"]=notChangeableData.category
                            else:
                                data["results"]['other_details']["caste_or_category"]=''
                        else:
                            data["results"]['other_details']["caste_or_category"]=''

                        if "caste_category_certificate" in required_other_fields.keys():
                            if notChangeableData.caste_category_certificate:
                                data["results"]['other_details']["caste_or_category_certificate_path"]=notChangeableData.caste_category_certificate.url
                            else:
                                data["results"]['other_details']["caste_or_category_certificate_path"]=''
                        else:
                            data["results"]['other_details']["caste_or_category_certificate_path"]=''

                        if "single_child" in required_other_fields.keys():
                            if notChangeableData.single_child:
                                data["results"]['other_details']["single_child"]='yes'
                            else:
                                data["results"]['other_details']["single_child"]='no'
                        else:
                            data["results"]['other_details']["single_child"]=''

                        if "first_child" in required_other_fields.keys():
                            if notChangeableData.first_child:
                                data["results"]['other_details']["first_child"]='yes'
                            else:
                                data["results"]['other_details']["first_child"]='no'

                            if notChangeableData.child_first_child_affidavit and notChangeableData.child_orphan:
                                data["results"]['other_details']["first_child_affidavit_path"]=notChangeableData.child_first_child_affidavit.url
                            else:
                                data["results"]['other_details']["first_child_affidavit_path"]=''
                        else:
                            data["results"]['other_details']["first_child"]=''
                            data["results"]['other_details']["first_child_affidavit_path"]=''

                        if "single_parent" in required_other_fields.keys():
                            if notChangeableData.single_parent:
                                data["results"]['other_details']["single_parent"]='yes'
                            else:
                                data["results"]['other_details']["single_parent"]='no'

                            if notChangeableData.single_parent_proof:
                                data["results"]['other_details']["single_parent_proof_path"]=notChangeableData.single_parent_proof.url
                            else:
                                data["results"]['other_details']["single_parent_proof_path"]=''
                        else:
                            data["results"]['other_details']["single_parent"]=''
                            data["results"]['other_details']["single_parent_proof_path"]=''

                        if "first_girl_child" in required_other_fields.keys():
                            if notChangeableData.first_girl_child:
                                data["results"]['other_details']["only_girl_child"]='yes'
                            else:
                                data["results"]['other_details']["only_girl_child"]='no'
                        else:
                            data["results"]['other_details']["only_girl_child"]=''

                        if "sibling1_alumni_name" in required_other_fields.keys() and "sibling2_alumni_name" in required_other_fields.keys() and "sibling1_alumni_proof" in required_other_fields.keys() and "sibling2_alumni_proof" in required_other_fields.keys() and "sibling1_alumni_school_name" in required_other_fields.keys() and "sibling2_alumni_school_name" in required_other_fields.keys():
                            if notChangeableData.sibling1_alumni_school_name and notChangeableData.sibling1_alumni_school_name.name == school.name:
                                data["results"]['other_details']["sibling1_alumni_of_school"]='yes'
                                if notChangeableData.sibling1_alumni_name:
                                    data["results"]['other_details']["sibling1_alumni_name"]=notChangeableData.sibling1_alumni_name
                                else:
                                    data["results"]['other_details']["sibling1_alumni_name"]=''
                                if notChangeableData.sibling1_alumni_proof:
                                    data["results"]['other_details']["sibling1_alumni_id_card_path"]=notChangeableData.sibling1_alumni_proof.url
                                else:
                                    data["results"]['other_details']["sibling1_alumni_id_card_path"]=''
                            else:
                                data["results"]['other_details']["sibling1_alumni_of_school"]='no'
                                data["results"]['other_details']["sibling1_alumni_name"]=''
                                data["results"]['other_details']["sibling1_alumni_id_card_path"]=''

                            if notChangeableData.sibling2_alumni_school_name and notChangeableData.sibling2_alumni_school_name.name == school.name:
                                data["results"]['other_details']["sibling2_alumni_of_school"]='yes'
                                if notChangeableData.sibling2_alumni_name:
                                    data["results"]['other_details']["sibling2_alumni_name"]=notChangeableData.sibling2_alumni_name
                                else:
                                    data["results"]['other_details']["sibling2_alumni_name"]=''
                                if notChangeableData.sibling2_alumni_proof:
                                    data["results"]['other_details']["sibling2_alumni_id_card_path"]=notChangeableData.sibling2_alumni_proof.url
                                else:
                                    data["results"]['other_details']["sibling2_alumni_id_card"]=''
                            else:
                                data["results"]['other_details']["sibling2_alumni_of_school"]='no'
                                data["results"]['other_details']["sibling2_alumni_name"]=''
                                data["results"]['other_details']["sibling2_alumni_id_card_path"]=''
                        else:
                            data["results"]['other_details']["sibling1_alumni_of_school"]=''
                            data["results"]['other_details']["sibling1_alumni_name"]=''
                            data["results"]['other_details']["sibling1_alumni_id_card_path"]=''
                            data["results"]['other_details']["sibling2_alumni_of_school"]=''
                            data["results"]['other_details']["sibling2_alumni_name"]=''
                            data["results"]['other_details']["sibling2_alumni_id_card_path"]=''

                        if "report_card" in required_other_fields.keys() and "transfer_date" in required_other_fields.keys() and "transfer_number" in required_other_fields.keys() and "last_school_name" in required_other_fields.keys() and "last_school_board" in required_other_fields.keys() and "last_school_class" in required_other_fields.keys() and "reason_of_leaving" in required_other_fields.keys() and "last_school_address" in required_other_fields.keys() and "transfer_certificate" in required_other_fields.keys() and "last_school_result_percentage" in required_other_fields.keys():
                            if notChangeableData.last_school_name:
                                data["results"]['other_details']["previous_school_name"]=notChangeableData.last_school_name
                            else:
                                data["results"]['other_details']["previous_school_name"]=''
                            if notChangeableData.last_school_address:
                                data["results"]['other_details']["previous_school_address"]=notChangeableData.last_school_address
                            else:
                                data["results"]['other_details']["previous_school_address"]=''
                            if notChangeableData.last_school_class:
                                data["results"]['other_details']["previous_school_last_class_attendant"]=notChangeableData.last_school_class.name
                            else:
                                data["results"]['other_details']["previous_school_last_class_attendant"]=''
                            if notChangeableData.last_school_board:
                                data["results"]['other_details']["previous_school_board"]=notChangeableData.last_school_board.name
                            else:
                                data["results"]['other_details']["previous_school_board"]=''
                            if notChangeableData.last_school_result_percentage:
                                data["results"]['other_details']["previous_school_last_class_result_%"]=notChangeableData.last_school_result_percentage
                            else:
                                data["results"]['other_details']["previous_school_last_class_result_%"]=''
                            if notChangeableData.transfer_date:
                                data["results"]['other_details']["previous_school_transfer_date"]=notChangeableData.transfer_date
                            else:
                                data["results"]['other_details']["previous_school_transfer_date"]=''
                            if notChangeableData.transfer_number:
                                data["results"]['other_details']["previous_school_transfer_document_sr_no"]=notChangeableData.transfer_number
                            else:
                                data["results"]['other_details']["previous_school_transfer_document_sr_no"]=''
                            if notChangeableData.reason_of_leaving:
                                data["results"]['other_details']["previous_school_reason_of_leaving"]=notChangeableData.reason_of_leaving
                            else:
                                data["results"]['other_details']["previous_school_reason_of_leaving"]=''
                            if notChangeableData.transfer_certificate:
                                data["results"]['other_details']["previous_school_transfer_certificate_path"]=notChangeableData.transfer_certificate.url
                            else:
                                data["results"]['other_details']["previous_school_transfer_certificate_path"]=''
                            if notChangeableData.report_card:
                                data["results"]['other_details']["previous_school_report_card_path"]=notChangeableData.report_card.url
                            else:
                                data["results"]['other_details']["previous_school_report_card_path"]=''

                        else:
                            data["results"]['other_details']["previous_school_name"]=''
                            data["results"]['other_details']["previous_school_address"]=''
                            data["results"]['other_details']["previous_school_last_class_attendant"]=''
                            data["results"]['other_details']["previous_school_board"]=''
                            data["results"]['other_details']["previous_school_last_class_result_%"]=''
                            data["results"]['other_details']["previous_school_transfer_date"]=''
                            data["results"]['other_details']["previous_school_transfer_document_sr_no"]=''
                            data["results"]['other_details']["previous_school_reason_of_leaving"]=''
                            data["results"]['other_details']["previous_school_transfer_certificate_path"]=''
                            data["results"]['other_details']["previous_school_report_card_path"]=''

                        if "transport_facility" in required_other_fields.keys():
                            if notChangeableData.transport_facility_required:
                                data["results"]['other_details']["transport_facility_required"]='yes'
                            else:
                                data["results"]['other_details']["transport_facility_required"]='no'
                        else:
                            data["results"]['other_details']["transport_facility_required"]=''

                        if "baptism_certificate" in required_other_fields.keys():
                            if notChangeableData.baptism_certificate:
                                data["results"]['other_details']["baptism_certificate_path"]=notChangeableData.baptism_certificate.url
                            else:
                                data["results"]['other_details']["baptism_certificate_path"]=''
                        else:
                            data["results"]['other_details']["baptism_certificate_path"]=''

                        if "parent_signature_upload" in required_other_fields.keys():
                            if notChangeableData.parent_signature_upload:
                                data["results"]['other_details']["parent_signature_path"]=notChangeableData.parent_signature_upload.url
                            else:
                                data["results"]['other_details']["parent_signature_path"]=''
                        else:
                            data["results"]['other_details']["parent_signature_path"]=''

                        if "mother_tongue" in required_other_fields.keys():
                            if notChangeableData.mother_tongue:
                                data["results"]['other_details']["mother_tongue"]=notChangeableData.mother_tongue
                            else:
                                data["results"]['other_details']["mother_tongue"]=''
                        else:
                            data["results"]['other_details']["mother_tongue"]=''

                        if "distance_affidavit" in required_other_fields.keys():
                            if notChangeableData.distance_affidavit:
                                data["results"]['other_details']["distance_affidavit_path"]=notChangeableData.distance_affidavit
                            else:
                                data["results"]['other_details']["distance_affidavit_path"]=''
                        else:
                            data["results"]['other_details']["distance_affidavit_path"]=''

                        if "family_photo" in required_other_fields.keys():
                            if notChangeableData.family_photo:
                                data["results"]['other_details']["family_photo_path"]=notChangeableData.family_photo
                            else:
                                data["results"]['other_details']["family_photo_path"]=''
                        else:
                            data["results"]['other_details']["family_photo_path"]=''

                        if "is_twins" in required_other_fields.keys():
                            if notChangeableData.is_twins:
                                data["results"]['other_details']["is_twins"]='yes'
                            else:
                                data["results"]['other_details']["is_twins"]='no'
                        else:
                            data["results"]['other_details']["is_twins"]=''

                        if "second_born_child" in required_other_fields.keys():
                            if notChangeableData.second_born_child:
                                data["results"]['other_details']["second_born_child"]='yes'
                            else:
                                data["results"]['other_details']["second_born_child"]='no'
                        else:
                            data["results"]['other_details']["second_born_child"]=''

                        if "third_born_child" in required_other_fields.keys():
                            if notChangeableData.third_born_child:
                                data["results"]['other_details']["third_born_child"]='yes'
                            else:
                                data["results"]['other_details']["third_born_child"]='no'
                        else:
                            data["results"]['other_details']["third_born_child"]=''


                        # Return the whole data
                        return Response(data,status=status.HTTP_200_OK)
                    else:
                        data = {}
                        data['results'] = "This ID doesn't belog to your group"
                        return Response(data,status=status.HTTP_200_OK)
                else:
                    data = {}
                    data['results'] = "Provide a valid form ID"
                    return Response(data,status=status.HTTP_200_OK)
            else:
                data = {}
                data['results'] = "School API Not Active"
                return Response(data,status=status.HTTP_200_OK)
        else:
            data = {}
            data['results'] = "No Group Data Found"
            return Response(data,status=status.HTTP_200_OK)

class SchoolContactClickDataRecordView(APIView):
    def get(self,request,slug,type):
        if type == 'school' or type == 'ezyschooling':
            if SchoolProfile.objects.filter(slug=slug).exists():
                if self.request.user.is_authenticated:
                    if SchoolContactClickData.objects.filter(school=SchoolProfile.objects.get(slug=slug),user=self.request.user
                    ).exists():
                        contact_data = SchoolContactClickData.objects.get(school=SchoolProfile.objects.get(slug=slug),user=self.request.user
                        )
                    else:
                        contact_data = SchoolContactClickData.objects.create(school=SchoolProfile.objects.get(slug=slug),user=self.request.user
                        )
                    if type == 'school':
                        contact_data.count_school += 1
                    elif type == 'ezyschooling':
                        contact_data.count_ezyschooling += 1
                    else:
                        pass
                    if ParentProfile.objects.filter(id=self.request.user.current_parent).exists():
                        detailed_profile = ParentProfile.objects.get(id=self.request.user.current_parent)
                        contact_data.mobile_number = detailed_profile.phone
                    if ParentAddress.objects.filter(id=self.request.user.current_parent).exists():
                        detailed_address = ParentAddress.objects.get(id=self.request.user.current_parent)
                        contact_data.user_region = detailed_address.region.name
                    contact_data.save()

                return Response("Recorded",status=status.HTTP_200_OK)
            else:
                return Response("User is not authenticated",status=status.HTTP_200_OK)
        else:
            return Response("Provide a valid click record type",status=status.HTTP_200_OK)

# class SchoolContactClickDataView12(APIView):
#     def get(self,request,slug):
#         if SchoolProfile.objects.filter(slug=slug).exists():
#             school_pro = SchoolProfile.objects.get(slug=slug)
#             if school_pro.contact_data_permission:
#                 if self.request.user.is_authenticated:
#                     data = {}
#                     total_count = 0
#                     all_data = []
#                     if SchoolContactClickData.objects.filter(school=SchoolProfile.objects.get(slug=slug)).exists():
#                         all_call_data = SchoolContactClickData.objects.filter(school=SchoolProfile.objects.get(slug=slug))
#                         for call_data in all_call_data:
#                             total_count += call_data.count_school
#                             if ParentProfile.objects.filter(id=call_data.user.current_parent).exists() and call_data.count_school>0:
#                                 parent = ParentProfile.objects.get(id=call_data.user.current_parent)
#                                 all_data.append({
#                                     "name" : parent.name,
#                                     "mobile" : parent.phone,
#                                     "email" : self.request.user.email,
#                                     "contact_count" : call_data.count_school,
#                                 })
#
#                     data['results'] = {}
#                     data['results']['total_count'] = total_count
#                     data['results']['contact_list'] = all_data
#                     return Response(data,status=status.HTTP_200_OK)
#                 else:
#                     return Response("authentication failed",status=status.HTTP_200_OK)
#             else:
#                 return Response("permission denied",status=status.HTTP_200_OK)
#         else:
#             return Response("school doesn't exists",status=status.HTTP_200_OK)

class SchoolContactClickDataView(generics.ListAPIView):
    serializer_class = serializers.SchoolConatctSerializer
    permission_classes = [SchoolContactClickDataPermission]

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = SchoolContactClickData.objects.filter(school=school)
        return queryset

class ExploreSchoolURLValues(APIView):

    def get(self,request,url):
        # import ipdb;ipdb.set_trace()
        url = self.kwargs.get("url", None)
        startingPart = url.split("school-admission-in-")[0]
        endingPart = url.split("school-admission-in-")[1]
        if url.split("-")[-1] == "undefined":
            url = url.replace('-undefined','')
            endingPart = url.split("school-admission-in-")[1]
            if DistrictRegion.objects.filter(slug=endingPart).exists():
                region_value = DistrictRegion.objects.get(slug=endingPart)
                endingPart = f"{endingPart}-{region_value.district.slug}"
        elif url[len(url)-1] == '-':
            endingPart = url.split("school-admission-in-")[1][:-1]
            if DistrictRegion.objects.filter(slug=endingPart).exists():
                region_value = DistrictRegion.objects.get(slug=endingPart)
                endingPart = f"{endingPart}-{region_value.district.slug}"
        else:
            endingPart = url.split("school-admission-in-")[1]
        boardFoundedStatus = False
        classFoundedStatus = False
        selectedClass = ''
        if len(startingPart)==0:
            foundedBoard = ''
            foundedClass = ''
            selectedClass = ''
        else:
            startingPartBreaked = startingPart.split("-")[:-1]
            for item in startingPartBreaked:
                joinedItem = ("-").join(startingPartBreaked)
                foundedClass = ''
                selectedClass = ''
                if SchoolBoard.objects.filter(slug=joinedItem).exists():
                    boardObject= SchoolBoard.objects.get(slug=joinedItem)
                    foundedBoard = boardObject.slug
                    startingPart=startingPart.replace(foundedBoard,'')
                    boardFoundedStatus = True
                    if boardFoundedStatus and len(startingPart) > 1:
                        startingPart = startingPart[1:-1]
                        if SchoolClasses.objects.filter(slug=startingPart).exists():
                            data = []
                            res = SchoolClasses.objects.get(slug=startingPart)
                            multi_relation_id = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=res.id).first()
                            if multi_relation_id:
                                obj_filter = multi_relation_id.multi_class_relation.filter()
                                for multi_obj in obj_filter:
                                    if SchoolClasses.objects.get(slug=multi_obj.slug):
                                        data.append(multi_obj.slug)
                                obj = ''
                                for item in data:
                                    if obj:
                                        obj = obj + ',' + item
                                    else:
                                        obj = item
                                foundedClass = obj
                                selectedClass = res.slug
                            else:
                                foundedClass = res.slug
                                selectedClass = res.slug
                            classFoundedStatus = True
                    break
                else:
                    startingPartBreaked = startingPartBreaked[:-1]
            if not boardFoundedStatus and len(("-").join(startingPart.split("-")[:-1]))>0:
                classObject= SchoolClasses.objects.get(slug=("-").join(startingPart.split("-")[:-1]))
                data = []
                multi_relation_id = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=classObject.id).first()
                if multi_relation_id:
                    obj_filter = multi_relation_id.multi_class_relation.filter()
                    for multi_obj in obj_filter:
                        if SchoolClasses.objects.get(slug=multi_obj.slug):
                            data.append(multi_obj.slug)
                    obj = ''
                    for item in data:
                        if obj:
                            obj = obj + ',' + item
                        else:
                            obj = item
                    foundedClass = obj
                    selectedClass = classObject.slug
                else:
                    foundedClass = classObject.slug
                    selectedClass = classObject.slug
                foundedBoard = ''
        foundedCity = ''
        foundedDistrict = ''
        foundedDistrictRegion = ''

        if District.objects.filter(slug=endingPart).exists():
            endPartForDistrictRegion = endingPart
            districtObject = District.objects.get(slug=endingPart)
            citySlug = districtObject.city.slug
            if District.objects.filter(city__slug=citySlug).count() > 1:
                foundedCity = districtObject.city.slug
                foundedDistrict = districtObject.slug
            elif City.objects.filter(slug=endingPart).exists():
                cityObject = City.objects.get(slug=endingPart)
                foundedCity = cityObject.slug
        elif City.objects.filter(slug=endingPart).exists():
            endPartForDistrictRegion = endingPart
            cityObject = City.objects.get(slug=endingPart)
            foundedCity = cityObject.slug
        else:
            endPartForDistrictRegion = endingPart
            endingPart = endingPart.split("-")[1:]
            for item in endingPart:
                joinedItem = ("-").join(endingPart)
                if District.objects.filter(slug=joinedItem).exists():
                    districtObject = District.objects.get(slug=joinedItem)
                    citySlug = districtObject.city.slug
                    if District.objects.filter(city__slug=citySlug).count() > 1:
                        foundedCity = districtObject.city.slug
                        foundedDistrict = districtObject.slug
                        if endPartForDistrictRegion.count(foundedDistrict) == 1:
                            endPartForDistrictRegion = endPartForDistrictRegion.replace(foundedDistrict,"")[:-1]
                        else:
                            current_url = endPartForDistrictRegion
                            removal = foundedDistrict
                            reverse_removal = removal[::-1]
                            replacement = ""
                            reverse_replacement = replacement[::-1]
                            new_url = current_url[::-1].replace(reverse_removal, reverse_replacement, 1)[::-1]
                            endPartForDistrictRegion = new_url[:-1]
                        break
                    elif City.objects.filter(slug=joinedItem).exists():
                        cityObject = City.objects.get(slug=joinedItem)
                        foundedCity = cityObject.slug
                        if endPartForDistrictRegion.count(foundedCity) == 1:
                            endPartForDistrictRegion = endPartForDistrictRegion.replace(foundedCity,"")[:-1]
                        else:
                            current_url = endPartForDistrictRegion
                            removal = foundedCity
                            reverse_removal = removal[::-1]
                            replacement = ""
                            reverse_replacement = replacement[::-1]
                            new_url = current_url[::-1].replace(reverse_removal, reverse_replacement, 1)[::-1]
                            endPartForDistrictRegion = new_url[:-1]
                        break
                elif City.objects.filter(slug=joinedItem).exists():
                    cityObject = City.objects.get(slug=joinedItem)
                    foundedCity = cityObject.slug
                    if endPartForDistrictRegion.count(foundedCity) == 1:
                        endPartForDistrictRegion = endPartForDistrictRegion.replace(foundedCity,"")[:-1]
                    else:
                        current_url = endPartForDistrictRegion
                        removal = foundedCity
                        reverse_removal = removal[::-1]
                        replacement = ""
                        reverse_replacement = replacement[::-1]
                        new_url = current_url[::-1].replace(reverse_removal, reverse_replacement, 1)[::-1]
                        endPartForDistrictRegion = new_url[:-1]
                    break
                else:
                    endingPart = endingPart[1:]
        if DistrictRegion.objects.filter(slug=endPartForDistrictRegion, city__slug=foundedCity).exists():
            districtRegionObject = DistrictRegion.objects.get(slug=endPartForDistrictRegion)
            foundedDistrictRegion = districtRegionObject.slug
        data = {}
        data['board'] = foundedBoard
        data['class'] = foundedClass
        data['city'] = foundedCity
        data['district'] = foundedDistrict
        data['district_region'] = foundedDistrictRegion
        data['selected_class'] = selectedClass if selectedClass else ''
        return Response(data,status=status.HTTP_200_OK)

class ExploreSchoolURLValidation(APIView):

    def get(self,request,url):
        foundedCityName=''
        foundedCitySlug =''
        isCityValid = False
        url = self.kwargs.get("url", None)
        if url.split("-")[-1] == "undefined":
            url = url.replace('-undefined','')
            endingPart = url.split("school-admission-in-")[1]
            if DistrictRegion.objects.filter(slug=endingPart).exists():
                region_value = DistrictRegion.objects.get(slug=endingPart)
                endingPart = f"{endingPart}-{region_value.district.slug}"
        elif url[len(url)-1] == '-':
            endingPart = url.split("school-admission-in-")[1][:-1]
            if DistrictRegion.objects.filter(slug=endingPart).exists():
                region_value = DistrictRegion.objects.get(slug=endingPart)
                endingPart = f"{endingPart}-{region_value.district.slug}"
        else:
            endingPart = url.split("school-admission-in-")[1]
        if District.objects.filter(slug=endingPart).exists():
            endPartForDistrictRegion = endingPart
            districtObject = District.objects.get(slug=endingPart)
            citySlug = districtObject.city.slug
            if District.objects.filter(city__slug=citySlug).count() > 1:
                foundedCityName = districtObject.city.name
                foundedCitySlug = districtObject.city.slug
                isCityValid = True
            elif City.objects.filter(slug=endingPart).exists():
                cityObject = City.objects.get(slug=endingPart)
                foundedCityName = cityObject.name
                foundedCitySlug = cityObject.slug
                isCityValid = True
        elif City.objects.filter(slug=endingPart).exists():
            cityObject = City.objects.get(slug=endingPart)
            foundedCityName = cityObject.name
            foundedCitySlug = cityObject.slug
            isCityValid = True

        else:
            endPartForDistrictRegion = endingPart
            endingPart = endingPart.split("-")[1:]
            for item in endingPart:
                joinedItem = ("-").join(endingPart)
                if District.objects.filter(slug=joinedItem).exists():
                    districtObject = District.objects.get(slug=joinedItem)
                    citySlug = districtObject.city.slug
                    if District.objects.filter(city__slug=citySlug).count() > 1:
                        foundedCityName = districtObject.city.name
                        foundedCitySlug = districtObject.city.slug
                        isCityValid = True
                        break
                    elif City.objects.filter(slug=joinedItem).exists():
                        cityObject = City.objects.get(slug=joinedItem)
                        foundedCityName = cityObject.name
                        foundedCitySlug = cityObject.slug
                        isCityValid = True
                        break
                elif City.objects.filter(slug=joinedItem).exists():
                    cityObject = City.objects.get(slug=joinedItem)
                    foundedCityName = cityObject.name
                    foundedCitySlug = cityObject.slug
                    isCityValid = True
                    break
                else:
                    endingPart = endingPart[1:]
        data = {}
        data['city'] = foundedCityName
        data['city_slug'] = foundedCitySlug
        data['is_city_valid'] = isCityValid

        return Response(data,status=status.HTTP_200_OK)


class HomepageSchoolsView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = HomePageSchoolSerializer
    queryset = SchoolProfile.objects.filter(for_homepage=True).order_by("id")

class CityWiseSitemapData(APIView):
    def get(self,request,city):
        if City.objects.filter(slug=city).exists():
            result = [f'admissions/school-admission-in-{city}']
            all_district_slug = District.objects.filter(city__slug=city,params__Count__gt=0).values("slug") if District.objects.filter(city__slug=city,params__Count__gt=0).count() > 1 else District.objects.none()
            all_district_region_slug = DistrictRegion.objects.filter(city__slug=city,params__Count__gt=0).values_list("slug","district__slug")
            all_class_slug = SchoolClasses.objects.all().values("slug")
            board_slugs = ["cbse","icse","cisce","ib-board","cambridge","igcse"]
            all_board_slug = SchoolBoard.objects.filter(slug__in=board_slugs).values("slug")
            all_school_profile_slug = SchoolProfile.objects.filter(school_city__slug=city,is_active=True).values("slug")
            for value in all_district_slug:
                result.append(f"admissions/school-admission-in-{value['slug']}")
            for value in all_district_region_slug:
                result.append(f"admissions/school-admission-in-{value[0]}-{value[1]}")
            for value in all_class_slug:
                result.append(f"admissions/{value['slug']}-school-admission-in-{city}")
            for value in all_board_slug:
                result.append(f"admissions/{value['slug']}-school-admission-in-{city}")
            # for grade in all_class_slug:
            #     for region in all_district_region_slug:
            #         result.append(f"admissions/{grade['slug']}-school-admission-in-{region[0]}-{region[1]}")
            # for board in all_board_slug:
            #     for region in all_district_region_slug:
            #         result.append(f"admissions/{board['slug']}-school-admission-in-{region[0]}-{region[1]}")
            for value in all_school_profile_slug:
                result.append(f"/school/profile/{value['slug']}")
            return Response(result,status=status.HTTP_200_OK)
        return Response("data",status=status.HTTP_400_BAD_REQUEST)

class SchoolAlumniView(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]
    def get(self, request, slug):
        featured = self.request.GET.get('featured', None)
        data = {}
        values = []
        if featured == 'yes':
            all_alumni = SchoolAlumni.objects.filter(school__slug=slug, featured=True)
        else:
            all_alumni = SchoolAlumni.objects.filter(school__slug=slug)
        for alumni in all_alumni:
            values.append({
                'id':alumni.id,
                'name':alumni.name,
                'image':alumni.image.url,
                'designation':alumni.current_designation,
                'passing_year':alumni.passing_year,
                'featured':f"{'yes' if alumni.featured else 'no'}",
            })
        data['count'] = len(values)
        data['results'] = values
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, slug):
        if request.data:
            school=SchoolProfile.objects.get(slug=slug)
            name = request.data['name']
            image = request.data['image']
            designation = request.data['designation']
            passing_year = request.data['passing_year']
            featured = True
            if request.data['featured'] == 'no':
                featured = False
            SchoolAlumni.objects.create(name=name,image=image,current_designation=designation,passing_year=passing_year,featured=featured,school=school)
            return Response("Alumni Created", status=status.HTTP_200_OK)
        else:
            return Response({"results":'Provide Payload'},status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,slug):
        id = self.request.GET.get('id', None)
        if id:
            if request.data:
                if SchoolAlumni.objects.filter(school__slug=slug, id=id).exists():
                    alumni_obj = SchoolAlumni.objects.get(school__slug=slug, id=id)
                    name = request.data['name']
                    designation = request.data['designation']
                    passing_year = request.data['passing_year']
                    featured = True
                    if request.data['featured'] == 'no':
                        featured = False
                    try:
                        if request.data['image_change'] and request.data['image_change'].lower() == 'yes':
                            image = request.data['image']
                            alumni_obj.image=image
                    except Exception as e:
                        pass
                    alumni_obj.name=name
                    alumni_obj.current_designation=designation
                    alumni_obj.passing_year=passing_year
                    alumni_obj.featured=featured
                    alumni_obj.save()
                    return Response("Alumni Updated", status=status.HTTP_200_OK)
                else:
                    return Response("No Data Found", status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"results":'Provide Payload'},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"results":'Provide ID'},status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,slug):
        id = self.request.GET.get('id', None)
        if id:
            if SchoolAlumni.objects.filter(school__slug=slug, id=id).exists():
                alumni_obj = SchoolAlumni.objects.get(school__slug=slug, id=id)
                alumni_obj.delete()
                return Response("Alumni Deleted", status=status.HTTP_200_OK)
            else:
                return Response("No Data Found", status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"results":'Provide ID'},status=status.HTTP_400_BAD_REQUEST)

class BoardingSchoolExtendView(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]
    def get(self, request, slug):
        if BoardingSchoolExtend.objects.filter(extended_school__slug=slug).exists():
            currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
            profile = BoardingSchoolExtend.objects.get(extended_school__slug=slug)
            data = {}
            data['pre_post_adm_pro'] = profile.pre_post_admission_process
            data['withdrawl_policy'] = profile.withdrawl_policy
            data['food_details'] = profile.food_details
            data['guest_house'] = profile.faq_related_data['guest_house']
            data['laundry_service'] = profile.faq_related_data['laundry_service']
            data['day_scholars_allowed'] = profile.faq_related_data['day_scholar_allowed']
            data['faqs'] = get_boarding_school_faqs(profile)
            food_option = []
            for item in FoodCategories.objects.all():
                if item not in profile.food_option.all():
                    food_option.append({
                        'id':item.id,
                        "name":item.name,
                        'type':item.type,
                        'include':False
                    })
                else:
                    food_option.append({
                        'id':item.id,
                        "name":item.name,
                        'type':item.type,
                        'include':True
                    })
            data['food_option'] = food_option
            data['day_wise_schedule'] = {}
            current = DaywiseSchedule.objects.filter(school__slug=slug,session=str(currentSession))
            final_current_array = []
            for item in current:
                current_value = {}
                current_value['id'] = item.id
                if item.ending_class and item.starting_class:
                    current_value['name'] = str(item.starting_class.name)+ " to " + str(item.ending_class.name)+ " - (" + str(item.type) + ")"
                else:
                    current_value['name'] = "No Class - (" +str(item.type) +")"
                final_current_array.append(current_value)
            data['day_wise_schedule'][str(currentSession)] = final_current_array

            next = DaywiseSchedule.objects.filter(school__slug=slug,session=str(nextSession))
            final_next_array = []
            for item in next:
                next_value = {}
                next_value['id'] = item.id
                if item.ending_class and item.starting_class:
                    next_value['name'] = str(item.starting_class.name)+ " to " + str(item.ending_class.name)+ " - (" + str(item.type) + ")"
                else:
                    next_value['name'] = "No Class - (" +str(item.type) +")"
                final_next_array.append(next_value)
            data['day_wise_schedule'][str(nextSession)] = final_next_array
            infra_obj = BoardingSchoolInfrastructure.objects.filter(school__slug=slug)
            final_infra_array = []
            for item in infra_obj:
                final_infra_array.append({
                    'id':item.id,
                    'name':item.type.name,
                })
            data['infrastruture'] = final_infra_array

            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_200_OK)

    def post(self, request, slug):
        if request.data:
            if BoardingSchoolExtend.objects.filter(extended_school__slug=slug).exists():
                value1, value2, value3, value4, value5, value6, value7, value8, value9 = False, False, False, False, False, False, False, False, False
                school=BoardingSchoolExtend.objects.get(extended_school__slug=slug)
                try:
                    if request.data['pre_post_adm_pro']:
                        if request.data['pre_post_adm_pro'] == "":
                            school.pre_post_admission_process = ''
                        else:
                            school.pre_post_admission_process = request.data['pre_post_adm_pro']
                        school.save()
                        value1 = True
                except Exception as e:
                    pass
                try:
                    if request.data['withdrawl_policy']:
                        if request.data['withdrawl_policy'] == "":
                            school.withdrawl_policy = ''
                        else:
                            school.withdrawl_policy = request.data['withdrawl_policy']
                        school.save()
                        value2 = True
                except Exception as e:
                    pass
                try:
                    if request.data['food_details']:
                        if request.data['food_details'] == "":
                            school.food_details = ''
                        else:
                            school.food_details = request.data['food_details']
                        school.save()
                        value3 = True
                except Exception as e:
                    pass

                try:
                    if request.data['food_options']:
                        school.food_option.clear()
                        values = request.data['food_options']
                        id_list = request.data['food_options']
                        for id in id_list:
                            school.food_option.add(FoodCategories.objects.get(id=int(id)))
                        school.save()
                        value4 = True
                except Exception as e:
                    pass

                try:
                    if request.data['day_wise_schedule']:
                        all_data = request.data['day_wise_schedule']
                        type = all_data['type'].capitalize()
                        data = all_data['data']
                        class_category = data['class_category']
                        session = data['session']
                        parameters = data['values']
                        if class_category:
                            start_class = SchoolClasses.objects.get(id=int(data['start_class']))
                            end_class = SchoolClasses.objects.get(id=int(data['end_class']))
                            schedule_obj = DaywiseSchedule.objects.create(school=school.extended_school,type=type,starting_class=start_class,ending_class=end_class,session=session)
                        else:
                            schedule_obj = DaywiseSchedule.objects.create(school=school.extended_school,type=type,session=session)

                        i = 0
                        for item in parameters:
                            name = parameters[i]['name']
                            duration = parameters[i]['duration']
                            if duration:
                                duration_json = parameters[i]['duration_value']
                                hours = duration_json['hours']
                                minutes = duration_json['minutes']
                                duration_value = timedelta(hours=hours,minutes=minutes)
                                value_obj = ScheduleTimings.objects.create(name=name,duration=duration_value)
                                i+=1
                            else:
                                endTimeValue = parameters[i]['end_time']
                                startTimeValue = parameters[i]['start_time']
                                end_time = time(endTimeValue['hours'],endTimeValue['minutes'],0)
                                start_time = time(startTimeValue['hours'],startTimeValue['minutes'],0)
                                value_obj = ScheduleTimings.objects.create(name=name,end_time=end_time,start_time=start_time)
                                i+=1
                            schedule_obj.values.add(value_obj)
                            schedule_obj.save()
                        if type.capitalize() == "Weekdays":
                            school.weekday_schedule.add(schedule_obj)
                        elif type.capitalize() == "Weekends":
                            school.weekend_schedule.add(schedule_obj)
                        school.save()
                        value5 = True
                except Exception as e:
                    pass
                try:
                    if self.request.query_params.get('school_infrastructure'):
                        all_data = request.data
                        type = BoardingSchoolInfrastructureHead.objects.get(id=int(all_data['type']))
                        description = all_data['description']
                        infra_obj,_ = BoardingSchoolInfrastructure.objects.get_or_create(school=school.extended_school,type=type)
                        infra_obj.description = description
                        infra_obj.save()
                        # parameters = all_data['image_list']
                        count = int(all_data["count"])
                        i = 0
                        for j in list(range(count)):
                            item = 'image_list['+str(j)+']'
                            image = all_data[item]
                            image_obj = BoardingSchoolInfrastrutureImages.objects.create(image=image)
                            i+=1
                            infra_obj.related_images.add(image_obj)
                            infra_obj.save()
                        school.infrastruture.add(infra_obj)
                        school.save()
                        value6 = True
                except Exception as e:
                    pass
                try:
                    if request.data['day_scholars_allowed'] == True or request.data['day_scholars_allowed'] == False:
                        school.faq_related_data['day_scholar_allowed'] = request.data['day_scholars_allowed']
                        school.save()
                        value7 = True
                except Exception as e:
                    pass
                try:
                    if request.data['laundry_service'] == True or request.data['laundry_service'] == False:
                        school.faq_related_data['laundry_service'] = request.data['laundry_service']
                        school.save()
                        value8 = True
                except Exception as e:
                    pass
                try:
                    if request.data['guest_house'] == True or request.data['guest_house'] == False:
                        school.faq_related_data['guest_house'] = request.data['guest_house']
                        school.save()
                        value9 = True
                except Exception as e:
                    pass
                if value1 or value2 or value3 or value4 or value5 or value6:
                    return Response("School Profile Updated", status=status.HTTP_200_OK)
                else:
                    return Response("Something Went Wrong", status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response("Slug not valid", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"results":'Provide Payload'},status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, slug):
        if request.data:
            if BoardingSchoolExtend.objects.filter(extended_school__slug=slug).exists():
                value1, value2 = False, False
                school=BoardingSchoolExtend.objects.get(extended_school__slug=slug)
                id = self.request.GET.get('id', None)
                if id:
                    try:
                        if request.data['day_wise_schedule']:
                            old_obj = DaywiseSchedule.objects.get(id=int(id))
                            old_session = old_obj.session
                            all_data = request.data['day_wise_schedule']
                            type = all_data['type'].capitalize()
                            data = all_data['data']
                            class_category = data['class_category']
                            if class_category:
                                start_class = SchoolClasses.objects.get(id=int(data['start_class']))
                                end_class = SchoolClasses.objects.get(id=int(data['end_class']))
                                old_obj.starting_class =start_class
                                old_obj.ending_class =end_class
                            else:
                                pass
                            parameters = data['values']
                            old_obj.type = type
                            old_obj.session = old_session
                            old_obj.save()
                            old_obj.values.clear()
                            i = 0
                            for item in parameters:
                                name = parameters[i]['name']
                                duration = parameters[i]['duration']
                                if duration:
                                    duration_json = parameters[i]['duration_value']
                                    hours = int(duration_json['hours'])
                                    minutes = int(duration_json['minutes'])
                                    duration_value = timedelta(hours=hours,minutes=minutes)
                                    value_obj = ScheduleTimings.objects.create(name=name,duration=duration_value)
                                    i+=1
                                else:
                                    endTimeValue = parameters[i]['end_time']
                                    startTimeValue = parameters[i]['start_time']
                                    end_time = time(int(endTimeValue['hours']),int(endTimeValue['minutes']),0)
                                    start_time = time(int(startTimeValue['hours']),int(startTimeValue['minutes']),0)
                                    value_obj = ScheduleTimings.objects.create(name=name,end_time=end_time,start_time=start_time)
                                    i+=1
                                old_obj.values.add(value_obj)
                                old_obj.save()
                            old_obj.save()
                            school.save()
                            value1 = True
                    except Exception as e:
                        pass

                    try:
                        if self.request.query_params.get('school_infrastructure'):
                            all_data = request.data
                            type = BoardingSchoolInfrastructureHead.objects.get(id=int(all_data['type']))
                            description = all_data['description']
                            infra_obj = BoardingSchoolInfrastructure.objects.get(id=int(id))
                            infra_obj.type = type
                            infra_obj.description = description
                            infra_obj.save()
                            all_delete = all_data['image_delete']
                            if all_delete:
                                for id in all_delete.split(","):
                                    image_obj = BoardingSchoolInfrastrutureImages.objects.get(id=int(id))
                                    infra_obj.related_images.remove(image_obj)
                            # old_obj.related_images.clear()
                            count = int(all_data["count"])
                            if count > 0:
                                i = 0
                                for j in list(range(count)):
                                    item = 'image_list['+str(j)+']'
                                    image = all_data[item]
                                    image_obj = BoardingSchoolInfrastrutureImages.objects.create(image=image)
                                    i+=1
                                    infra_obj.related_images.add(image_obj)
                                    infra_obj.save()
                            school.save()
                            value2 = True
                    except Exception as e:
                        pass
                else:
                    return Response("Please Provide ID", status=status.HTTP_400_BAD_REQUEST)
                if value1 or value2:
                    return Response("School Profile Updated", status=status.HTTP_200_OK)
                else:
                    return Response("Something Went Wrong", status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response("Slug not valid", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"results":'Provide Payload'},status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        if BoardingSchoolExtend.objects.filter(extended_school__slug=slug).exists():
            value1, value2 = False, False
            school=BoardingSchoolExtend.objects.get(extended_school__slug=slug)
            id = self.request.GET.get('id', None)
            if id:
                try:
                    if self.request.query_params.get('day_wise_schedule') == 'yes':
                        old_obj = DaywiseSchedule.objects.get(id=int(id))
                        old_obj.delete()
                        school.save()
                        value1 = True
                except Exception as e:
                    pass
                try:
                    if self.request.query_params.get('school_infrastructure') == 'yes':
                        infra_obj = BoardingSchoolInfrastructure.objects.get(id=int(id))
                        infra_obj.delete()
                        school.save()
                        value2 = True
                except Exception as e:
                    pass
            else:
                return Response("Please Provide ID", status=status.HTTP_400_BAD_REQUEST)
            if value1 or value2:
                return Response("Item deleted successfully", status=status.HTTP_200_OK)
            else:
                return Response("Something Went Wrong", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("Slug not valid", status=status.HTTP_400_BAD_REQUEST)

class FoodOptionsList(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]
    def get(self,request):
        all_type = FoodCategories.objects.all()
        data =[]
        for item in all_type:
            data.append({
            'id':item.id,
            'name':item.name,
            'type':item.type,
            })
        return Response(data, status=status.HTTP_200_OK)

class SchoolInfraHead(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]
    def get(self,request):
        all_type = BoardingSchoolInfrastructureHead.objects.filter(active=True)
        data =[]
        for item in all_type:
            data.append({
            'id':item.id,
            'name':item.name,
            'slug':item.slug,
            })
        return Response(data, status=status.HTTP_200_OK)

class SchoolDayScheduleDetail(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]
    def get(self, request,id):
        item = DaywiseSchedule.objects.get(id=int(id))
        value = {}
        value['id'] = item.id
        value['type'] = item.type
        if item.ending_class and item.starting_class:
            start_value = {}
            start_value['id'] = item.starting_class.id
            start_value['name'] = item.starting_class.name
            value['starting_class'] = start_value
            end_value = {}
            end_value['id'] = item.ending_class.id
            end_value['name'] = item.ending_class.name
            value['ending_class'] = end_value
        else:
            value['starting_class'] = None
            value['ending_class'] = None
        values_array = []
        for val in item.values.all():
            nested_value = {}
            nested_value['id'] = val.id
            nested_value['name'] = val.name
            nested_value['start_time'] = val.start_time
            nested_value['end_time'] = val.end_time
            if val.duration:
                hours, minutes, seconds = convert_timedelta(val.duration)
                nested_value['duration'] = ('{} hours, {} minutes'.format(hours, minutes))
            else:
                nested_value['duration'] = None
            values_array.append(nested_value)
        value['timing'] = values_array
        return Response(value,status=status.HTTP_200_OK)

class SchoolInfraStructureDetail(APIView):
    permission_classes = [BoardingSchoolExtendProfilePermissions,]

    def get(self, request,id):
        item = BoardingSchoolInfrastructure.objects.get(id=id)
        value = {}
        value['id'] = item.id
        type_obj = {}
        type_obj['id'] = item.type.id
        type_obj['name'] = item.type.name
        type_obj['slug'] = item.type.slug
        value['type'] = type_obj
        value['description'] = item.description
        nested_value = []
        for val in item.related_images.all():
            nested_value.append({
                'id':val.id,
                'image':val.image.url,
                'visible':val.visible
            })
        value['image_list'] = nested_value
        return Response(value,status=status.HTTP_200_OK)

class ClaimYourSchool(APIView):

    def post(self,request, slug,*args, **kwargs):
        if SchoolProfile.objects.filter(slug=slug).exists():
            if SchoolProfile.objects.filter(slug=slug,collab=False).exists():
                if request.data:
                    name = request.data['name']
                    email = request.data['email']
                    phone_number = request.data['phone_number']
                    designation = request.data['designation']
                    school_obj = SchoolProfile.objects.get(slug=slug,collab=False)
                    SchoolClaimRequests.objects.create(school=school_obj, name=name,email=email,designation=designation,phone_number=phone_number)
                    return Response("Claim Request submitted.", status=status.HTTP_200_OK)
                else:
                    return Response("Please provide payload.", status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response("School is already collabrated with ezyschooling.", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("School Not Found/Invalid Slug.", status=status.HTTP_404_NOT_FOUND)

class ClickAdditionSourceTracking(APIView):
    def get(self,request):
        try:
            id = self.request.GET.get('id')
            if SchoolEqnuirySource.objects.filter(related_id=id).exists():
                ad_source=SchoolEqnuirySource.objects.get(related_id=id)
                ad_source.total_clicks = ad_source.total_clicks + 1
                ad_source.save()
            return Response("Success", status=status.HTTP_200_OK)
        except Exception as e:
            return Response("Success", status=status.HTTP_200_OK)
""" This is Coupon Verification api on the basis of school_slug ,coupon_id here we are checking that wheather the given coupon id is valid or not .
        If valid ,then where the coupon 'll applied like on the School_Form Or the ezyschool convenice fees """

# @api_view(['GET'])
# def Coupon_Verification_View(request):
#     if request.method == 'GET':
#         school_slug =request.query_params.get('school_slug')
#         coupon_code=request.query_params.get('coupon_code')
#         child_id=request.query_params.get('child_id')

#         if ChildSchoolCart.objects.filter(school__slug=school_slug,child__id =child_id).exists():
#             childcart= ChildSchoolCart.objects.get(school__slug=school_slug,child__id =child_id)
#             print(childcart.id,childcart.school.id,childcart.child_id)
#             if Coupons.objects.filter(school__id = childcart.school.id,school_code=coupon_code).exists():
#                 coupon_obj = Coupons.objects.get(school__id = childcart.school.id,school_code=coupon_code)
#                 form_fee = childcart.form_price
#                 convenience_fee = childcart.school.convenience_fee
#                 Aft_using_coupon_formfee = ""
#                 if coupon_obj.school_coupon_type == 'P':
#                     Aft_using_coupon_formfee= form_fee * coupon_obj.school_amount / 100
#                 elif coupon_obj.school_coupon_type == 'F':
#                     Aft_using_coupon_formfee= coupon_obj.school_amount
#                 total_amount = convenience_fee + form_fee - Aft_using_coupon_formfee
#                 data={
#                     "coupon_amount": f'{coupon_obj.school_amount} {"%" if coupon_obj.school_coupon_type =="P" else "Flat"}',
#                     "form_fee" : form_fee,
#                     "after_applied_coupon":Aft_using_coupon_formfee,
#                     "convenience_fee": convenience_fee,
#                     "total":total_amount,
#                     "msg":"School Coupons applied"
#                 }
#                 childcart.coupon_code = coupon_obj.school_code
#                 childcart.save()
#                 return Response(data, status=status.HTTP_200_OK)
#             elif Coupons.objects.filter(school__id = childcart.school.id,ezyschool_code=coupon_code).exists():
#                 coupon_obj = Coupons.objects.get(school__id = childcart.school.id,ezyschool_code=coupon_code)
#                 form_fee = childcart.form_price
#                 convenience_fee = childcart.school.convenience_fee
#                 if convenience_fee != 0:
#                     amount = ""
#                     if coupon_obj.ezyschool_coupon_type == 'P':
#                         amount= convenience_fee * coupon_obj.ezyschool_amount / 100
#                         print(amount,"-4-",coupon_obj.ezyschool_coupon_type)
#                     elif coupon_obj.ezyschool_coupon_type == 'F':
#                         amount= coupon_obj.ezyschool_amount
#                         print(amount,"--1")
#                     print(amount,"--2",coupon_obj.ezyschool_coupon_type)
#                     Aft_using_coupon =  amount
#                     total_amount = form_fee + convenience_fee - Aft_using_coupon
#                     print(form_fee,"----------",convenience_fee,"0000000000000000",Aft_using_coupon)
#                     data={
#                         "coupon_amount": f'{coupon_obj.ezyschool_amount} {"%" if coupon_obj.ezyschool_coupon_type =="P" else "Flat"}',
#                         "form_fee" : form_fee,
#                         "convenience_fee": convenience_fee,
#                         "after_applied_coupon":Aft_using_coupon,
#                         "total":total_amount,
#                         "msg":"EzySchool Coupons applied "
#                     }
#                     childcart.coupon_code = coupon_obj.ezyschool_code
#                     childcart.save()
#                     return Response(data,status=status.HTTP_200_OK)
#                 else:
#                     return Response(f"This coupons is not applicable!", status=status.HTTP_200_OK)
#             else:
#                 return Response(f"This coupons is not vaild!", status=status.HTTP_200_OK)


class CouponView(APIView):
    def get(self, request):
        school_slug =request.query_params.get('school_slug')
        coupon_code=request.query_params.get('coupon_code')
        child_id=request.query_params.get('child_id')

        if ChildSchoolCart.objects.filter(school__slug=school_slug,child__id =child_id).exists():
            childcart= ChildSchoolCart.objects.get(school__slug=school_slug,child__id =child_id)
            if Coupons.objects.filter(school__id = childcart.school.id,school_code=coupon_code).exists():
                coupon_obj = Coupons.objects.get(school__id = childcart.school.id,school_code=coupon_code)
                form_fee = childcart.form_price
                convenience_fee = childcart.school.convenience_fee
                Aft_using_coupon_formfee = ""
                if coupon_obj.school_coupon_type == 'P':
                    Aft_using_coupon_formfee= form_fee * coupon_obj.school_amount / 100
                elif coupon_obj.school_coupon_type == 'F':
                    Aft_using_coupon_formfee= coupon_obj.school_amount
                total_amount = convenience_fee + form_fee - Aft_using_coupon_formfee
                if (form_fee - Aft_using_coupon_formfee) > 0:
                    data={
                        "coupon_amount": f'{coupon_obj.school_amount} {"%" if coupon_obj.school_coupon_type =="P" else "Flat"}',
                        "form_fee" : form_fee,
                        "after_applied_coupon":Aft_using_coupon_formfee,
                        "convenience_fee": convenience_fee,
                        "total":total_amount,
                        "msg":"School Coupons applied"
                    }
                    childcart.coupon_code = coupon_obj.school_code
                    childcart.discount = Aft_using_coupon_formfee
                    childcart.save()
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    return Response("This School Coupon is not applicable !", status=status.HTTP_200_OK)
            elif Coupons.objects.filter(school__id = childcart.school.id,ezyschool_code=coupon_code).exists():
                coupon_obj = Coupons.objects.get(school__id = childcart.school.id,ezyschool_code=coupon_code)
                form_fee = childcart.form_price
                convenience_fee = childcart.school.convenience_fee
                if convenience_fee != 0:
                    amount = ""
                    if coupon_obj.ezyschool_coupon_type == 'P':
                        amount= convenience_fee * coupon_obj.ezyschool_amount / 100
                    elif coupon_obj.ezyschool_coupon_type == 'F':
                        amount= coupon_obj.ezyschool_amount
                    Aft_using_coupon =  amount
                    total_amount = form_fee + convenience_fee - Aft_using_coupon
                    if (convenience_fee - Aft_using_coupon) > 0:
                        data={
                            "coupon_amount": f'{coupon_obj.ezyschool_amount} {"%" if coupon_obj.ezyschool_coupon_type =="P" else "Flat"}',
                            "form_fee" : form_fee,
                            "convenience_fee": convenience_fee,
                            "after_applied_coupon":Aft_using_coupon,
                            "total":total_amount,
                            "msg":"EzySchool Coupons applied "
                        }
                        childcart.coupon_code = coupon_obj.ezyschool_code
                        childcart.discount = Aft_using_coupon
                        childcart.save()
                        return Response(data,status=status.HTTP_200_OK)
                    else:
                        return Response("This Ezyschooling Coupon is not applicable !", status=status.HTTP_200_OK)
                else:
                    childcart.coupon_code = None
                    childcart.discount = convenience_fee
                    childcart.save()
                    return Response(f"This coupons is not applicable!", status=status.HTTP_200_OK)
            else:
                return Response(f"This coupons is not valid!", status=status.HTTP_200_OK)
        return Response(f"something went wrong!", status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        school_slug =request.data.get('school_slug')
        coupon_code=request.data.get('coupon_code')
        child_id=request.data.get('child_id')

        if ChildSchoolCart.objects.filter(school__slug=school_slug,child__id =child_id).exists():
            childcart= ChildSchoolCart.objects.get(school__slug=school_slug,child__id =child_id)
            if Coupons.objects.filter(school__id = childcart.school.id,school_code=coupon_code).exists() and childcart.coupon_code != None:
                coupon_obj = Coupons.objects.get(school__id = childcart.school.id,school_code=coupon_code)
                if coupon_obj.school_code == childcart.coupon_code and childcart.coupon_code != None:
                    childcart.coupon_code = None
                    childcart.discount = 0
                    childcart.save()
                    return Response(f"coupons removed successfully !",status=status.HTTP_200_OK)
                else:
                    childcart.coupon_code = None
                    childcart.discount = 0
                    childcart.save()
                    return Response(f"This coupons is not applicable!", status=status.HTTP_200_OK)
            elif Coupons.objects.filter(school__id = childcart.school.id,ezyschool_code=coupon_code).exists() and childcart.coupon_code != None:
                coupon_obj = Coupons.objects.get(school__id = childcart.school.id,ezyschool_code=coupon_code)
                if coupon_obj.ezyschool_code == childcart.coupon_code and childcart.coupon_code != None:
                    childcart.coupon_code = None
                    childcart.discount = 0
                    childcart.save()
                    return Response(f"coupons removed successfully !",status=status.HTTP_200_OK)
                else:
                    childcart.coupon_code = None
                    childcart.discount = 0
                    childcart.save()
                    return Response(f"This coupons is not applicable!", status=status.HTTP_200_OK)
            else:
                return Response(f"This coupons is not applicable!", status=status.HTTP_200_OK)
        else:
            return Response(f"This coupons is not valid or Already removed !", status=status.HTTP_200_OK)

class SchoolCardAllDetailsView(APIView):
    def get(self,request,slug):
        if SchoolProfile.objects.filter(slug=slug).exists():
            school = SchoolProfile.objects.get(slug=slug)
            time=datetime.now()-timedelta(hours = 720)
            cart_items_last30 =ChildSchoolCart.objects.filter(school=school,timestamp__gte=time).count()
            apply_items_last30 =SchoolApplication.objects.filter(school=school,timestamp__gte=time).count()
            cart_items= ChildSchoolCart.objects.filter(school=school).count()
            school_apply_items=SchoolApplication.objects.filter(school=school).count()
            notify_items=SchoolClassNotification.objects.filter(school=school).count()
            enquiry_items=SchoolEnquiry.objects.filter(school=school).count()
            views=school.views
            interested= int(cart_items+school_apply_items+notify_items+enquiry_items+(views*0.3))
            result={}
            result["visitor"]={}
            result["visitor"]["last_30_days"]=cart_items_last30 +apply_items_last30
            result["visitor"]["interested_items"] = interested
            currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
            classesInCurrentSession = AdmmissionOpenClasses.objects.filter(school__id=school.id, session=currentSession)
            classesInNextSession = AdmmissionOpenClasses.objects.filter(school__id=school.id, session=nextSession)
            if classesInCurrentSession:
                for item in classesInCurrentSession:
                    if item.admission_open == "OPEN":
                        isCurrentSessionAdmissionOpen = True
                        break
                    else:
                        isCurrentSessionAdmissionOpen = False
            else:
                isCurrentSessionAdmissionOpen = False

            if classesInNextSession:
                for item in classesInNextSession:
                    if item.admission_open == "OPEN":
                        isNextSessionAdmissionOpen = True
                        break
                    else:
                        isNextSessionAdmissionOpen = False
            else:
                isNextSessionAdmissionOpen = False
            if isCurrentSessionAdmissionOpen == True and isNextSessionAdmissionOpen == True:
                admissionOpenSession = "both"
                selected = nextSession.name
            elif isCurrentSessionAdmissionOpen == False and isNextSessionAdmissionOpen == False:
                admissionOpenSession = "none"
                selected = currentSession.name
            elif isCurrentSessionAdmissionOpen == True:
                admissionOpenSession = "current"
                selected = currentSession.name
            elif isNextSessionAdmissionOpen == True:
                admissionOpenSession = "next"
                selected = nextSession.name
            result['session'] = {}
            result['session']['isCurrentSessionAdmissionOpen'] = isCurrentSessionAdmissionOpen
            result['session']['isNextSessionAdmissionOpen'] = isNextSessionAdmissionOpen
            result['session']['admissionOpenSession'] = admissionOpenSession
            result['session']['selected'] = selected
            serializer = serializers.SchoolAdmissionResultImageSerializer(SchoolAdmissionResultImage.objects.filter(school__slug=slug).order_by("timestamp"), many=True)
            result['school_results'] = serializer.data


            # asdfasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasd
            school_profile = SchoolProfile.objects.get(slug=slug)
            if not school_profile.boarding_school:
                if school_profile.avg_fee:
                    result['fee']={}
                    result['fee']['fee'] = str(school_profile.avg_fee)
                    result['fee']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
                elif not school_profile.last_avg_fee_calculated:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                    if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists() and FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                        final_fee_current = 10000000000
                        final_fee_next = 10000000000
                        fee_tenure_next = "Monthly"
                        fee_tenure_current = "Monthly"
                        for currentFee in currentSessionFees:
                            for fee in currentFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                            fee_tenure_current = fee.tenure
                                            final_fee_current = fee.price

                        for nextFee in nextSessionFees:
                            for fee in nextFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                            fee_tenure_next = fee.tenure
                                            final_fee_next = fee.price
                        avg_fee = 0
                        if final_fee_current and final_fee_next:
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        elif final_fee_current == 10000000000 and final_fee_next:
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        elif final_fee_next == 10000000000 and final_fee_current:
                            if fee_tenure_current == "Monthly":
                                avg_fee = int(final_fee_current/1)
                            elif fee_tenure_current == "Quarterly":
                                avg_fee = int(final_fee_current/3)
                            elif fee_tenure_current == "Annually":
                                avg_fee = int(final_fee_current/12)
                            else:
                                avg_fee = int(final_fee_current)

                    elif FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        fee_tenure_current = "Monthly"
                        final_fee_current = 10000000000
                        for currentFee in currentSessionFees:
                            for fee in currentFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                            fee_tenure_current = fee.tenure
                                            final_fee_current = fee.price

                        if fee_tenure_current == "Monthly":
                            avg_fee = int(final_fee_current/1)
                        elif fee_tenure_current == "Quarterly":
                            avg_fee = int(final_fee_current/3)
                        elif fee_tenure_current == "Annually":
                            avg_fee = int(final_fee_current/12)
                        else:
                            avg_fee = int(final_fee_current)
                    elif FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                        nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                        fee_tenure_next = "Monthly"
                        final_fee_next = 10000000000
                        for nextFee in nextSessionFees:
                            for fee in nextFee.fees_parameters.all():
                                if fee.head:
                                    if fee.head.head:
                                        if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                            fee_tenure_next = fee.tenure
                                            final_fee_next = fee.price
                        if fee_tenure_next == "Monthly":
                            avg_fee = int(final_fee_next/1)
                        elif fee_tenure_next == "Quarterly":
                            avg_fee = int(final_fee_next/3)
                        elif fee_tenure_next == "Annually":
                            avg_fee = int(final_fee_next/12)
                        else:
                            avg_fee = int(final_fee_next)
                    else:
                        avg_fee = "NA"
                    if avg_fee == 10000000000 or avg_fee == '10000000000':
                        avg_fee = "NA"
                    todays_date = date.today()
                    school_profile.calculated_avg_fee = str(avg_fee)
                    school_profile.last_avg_fee_calculated = todays_date
                    school_profile.save()
                    result['fee']={}
                    result['fee']['fee'] = school_profile.calculated_avg_fee
                    result['fee']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)

                else:
                    todays_date = date.today()
                    last_update_date = school_profile.last_avg_fee_calculated
                    days_diff = todays_date - last_update_date
                    if days_diff.days >=4:
                        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                        if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists() and FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                            currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                            nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                            final_fee_current = 10000000000
                            final_fee_next = 10000000000
                            fee_tenure_next = "Monthly"
                            fee_tenure_current = "Monthly"
                            for currentFee in currentSessionFees:
                                for fee in currentFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                                fee_tenure_current = fee.tenure
                                                final_fee_current = fee.price

                            for nextFee in nextSessionFees:
                                for fee in nextFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                                fee_tenure_next = fee.tenure
                                                final_fee_next = fee.price
                            avg_fee = 0
                            if final_fee_current and final_fee_next:
                                if fee_tenure_next == "Monthly":
                                    avg_fee = int(final_fee_next/1)
                                elif fee_tenure_next == "Quarterly":
                                    avg_fee = int(final_fee_next/3)
                                elif fee_tenure_next == "Annually":
                                    avg_fee = int(final_fee_next/12)
                                else:
                                    avg_fee = int(final_fee_next)
                            elif final_fee_current == 10000000000 and final_fee_next:
                                if fee_tenure_next == "Monthly":
                                    avg_fee = int(final_fee_next/1)
                                elif fee_tenure_next == "Quarterly":
                                    avg_fee = int(final_fee_next/3)
                                elif fee_tenure_next == "Annually":
                                    avg_fee = int(final_fee_next/12)
                                else:
                                    avg_fee = int(final_fee_next)
                            elif final_fee_next == 10000000000 and final_fee_current:
                                if fee_tenure_current == "Monthly":
                                    avg_fee = int(final_fee_current/1)
                                elif fee_tenure_current == "Quarterly":
                                    avg_fee = int(final_fee_current/3)
                                elif fee_tenure_current == "Annually":
                                    avg_fee = int(final_fee_current/12)
                                else:
                                    avg_fee = int(final_fee_current)

                        elif FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                            currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                            fee_tenure_current = "Monthly"
                            final_fee_current = 10000000000
                            for currentFee in currentSessionFees:
                                for fee in currentFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_current > fee.price:
                                                fee_tenure_current = fee.tenure
                                                final_fee_current = fee.price

                            if fee_tenure_current == "Monthly":
                                avg_fee = int(final_fee_current/1)
                            elif fee_tenure_current == "Quarterly":
                                avg_fee = int(final_fee_current/3)
                            elif fee_tenure_current == "Annually":
                                avg_fee = int(final_fee_current/12)
                            else:
                                avg_fee = int(final_fee_current)
                        elif FeeStructure.objects.filter(school=school_profile,session=nextSession).exists():
                            nextSessionFees = FeeStructure.objects.filter(school=school_profile,session=nextSession)
                            fee_tenure_next = "Monthly"
                            final_fee_next = 10000000000
                            for nextFee in nextSessionFees:
                                for fee in nextFee.fees_parameters.all():
                                    if fee.head:
                                        if fee.head.head:
                                            if fee.head.head == 'Tuition Fees' and final_fee_next > fee.price:
                                                fee_tenure_next = fee.tenure
                                                final_fee_next = fee.price
                            if fee_tenure_next == "Monthly":
                                avg_fee = int(final_fee_next/1)
                            elif fee_tenure_next == "Quarterly":
                                avg_fee = int(final_fee_next/3)
                            elif fee_tenure_next == "Annually":
                                avg_fee = int(final_fee_next/12)
                            else:
                                avg_fee = int(final_fee_next)
                        else:
                            avg_fee = "NA"
                        if avg_fee == 10000000000 or avg_fee == '10000000000':
                            avg_fee = "NA"
                        school_profile.calculated_avg_fee = str(avg_fee)
                        school_profile.last_avg_fee_calculated = todays_date
                        school_profile.save()
                    result['fee']={}
                    result['fee']['fee'] = school_profile.calculated_avg_fee
                    result['fee']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
            else:
                if school_profile.avg_fee:
                    result['fee']={}
                    result['fee']['fee'] = str(school_profile.avg_fee)
                    result['fee']["online_school"]=school_profile.online_school
                    return Response(result,status=status.HTTP_200_OK)
                elif not school_profile.last_avg_fee_calculated:
                    currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
                    if FeeStructure.objects.filter(school=school_profile,session=currentSession).exists():
                        currentSessionFees = FeeStructure.objects.filter(school=school_profile,session=currentSession)
                        final_fee_current = 10000000000
                        for currentFee in currentSessionFees:
                            class_total_monthly_fee = 0
                            for fee in currentFee.fees_parameters.all().values_list('tenure','price'):
                                if fee[0] == "Monthly":
                                    class_total_monthly_fee += int(fee[1]/1)
                                elif fee[0] == "Quarterly":
                                    class_total_monthly_fee += int(fee[1]/3)
                                # elif fee[0] == "Annually":
                                #     class_total_monthly_fee += int(fee[1]/12)
                                else:
                                    class_total_monthly_fee += int(fee[1]/12)

                            if final_fee_current > class_total_monthly_fee:
                                final_fee_current = class_total_monthly_fee
                    avg_fee = final_fee_current*3
                    if avg_fee == 30000000000 or avg_fee == '100000000001000000000010000000000':
                        avg_fee = "NA"
                    school_profile.calculated_avg_fee = str(avg_fee)
                    school_profile.last_avg_fee_calculated = todays_date
                    school_profile.save()
                    result['fee']={}
                    result['fee']['fee'] = school_profile.calculated_avg_fee
                    result['fee']["online_school"]=school_profile.online_school
            return Response(result,status=status.HTTP_200_OK)
        else:
            result={}
            result["results"]="No School Found"
            return Response(result,status=status.HTTP_404_NOT_FOUND)
