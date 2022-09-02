import csv
from ctypes import resize
import io
import json
import os
import random
from itertools import chain
from dateutil.relativedelta import relativedelta
from django.db.transaction import atomic
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from . import serializers
from django.http import HttpResponse
from rest_auth.app_settings import JWTSerializer, TokenSerializer
from django.core.exceptions import ObjectDoesNotExist
from backend.logger import info_logger, error_logger
from allauth.account import app_settings as allauth_settings
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, date
from django.utils.timezone import make_aware
from celery.utils.log import get_task_logger
from rest_auth.registration.views import RegisterView
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import User
from schools.models import SchoolEnquiry, City, District, DistrictRegion, SchoolView, SchoolProfile, FeeStructure, AdmissionSession, Feature, AdmmissionOpenClasses, SchoolAdmissionFormFee, Subfeature, Pincode, Country, States, Area, SchoolBoard, SchoolType, State, SchoolFormat, BoardingSchoolInfrastructure
from parents.models import ParentProfile,ParentAddress
from admission_forms.models import SchoolApplication, ChildSchoolCart
from admin_custom.permissions import IsExecutiveUser, IsAdminUser, SchoolCounsellingDataPermission, IsDatabaseAdminUser
from childs.models import Child
from phones.models import PhoneNumber
from admin_custom.models import CounselorCAdminUser, CAdminUser, CommentSection, CounselingAction, ActionSection, SubActionSection, LeadGenerated, VisitScheduleData, AdmissionDoneData, CounsellorDailyCallRecord, SchoolDashboardMasterActionCategory, SchoolDashboardActionSection, SchoolCommentSection, SchoolAction, SchoolPerformedCommentEnquiry, SchoolPerformedActionOnEnquiry, DatabaseCAdminUser, ViewedParentPhoneNumberBySchool, ParentCallScheduled, SharedCounsellor, TransferredCounsellor
from admin_custom.utils import get_user_phone_numbers, getAllList, create_fee_structure_object, weekendDays, unique_a_list_of_dict, get_user_phone_numbers_for_inside, upload_file_to_bucket
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext_lazy as _
import pytz
from itertools import chain
from django.db.models import Q
from notification.models import WhatsappSubscribers
from admin_custom.tasks import lead_generated_whatsapp_trigger, upload_school_profiles, upload_school_facilities, upload_district_region, upload_school_fee_structure, visit_scheduled_whatsapp_trigger, send_admission_done_mail_to_school_heads, send_admission_done_mail_to_school_heads_from_school_dashboard, get_404_500_api_responses
from schools.permissions import HasSchoolChildModelPermissionOrReadOnly
from schools.api.v1.serializers import SchoolFeaturesSerializer, FeeStructureCreateUpdateSeirializer,FeeStructureSerializer
from schools.filters import AdmissionOpenClassesFilter, FeeStructureFilter
from schools.mixins import SchoolPerformCreateUpdateMixin
from .serializers import SchoolProfileInsideSerializer, ParentCallScheduledSerializer

logger = get_task_logger(__name__)
hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD

def get_all_user_list(self, request, additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    citys = self.request.GET.get('citys', None)
    districts = self.request.GET.get('districts', None)
    districtregions = self.request.GET.get('districtregions', None)
    boarding_schools = self.request.GET.get('boarding', "no")
    online_schools = self.request.GET.get('online', "no")
    collab_status = self.request.GET.get('collab',"all")
    visit_interest = self.request.GET.get('visit_interest',"none")
    if collab_status == "all":
        collab_value=[True,False]
    elif collab_status == "true" or collab_status == True:
        collab_value=[True]
    elif collab_status == "false" or collab_status == False:
        collab_value=[False]

    if visit_interest == "none":
        visit_interest_value=[True,False]
    elif visit_interest == "true" or visit_interest == True:
        visit_interest_value=[True]
    elif visit_interest == "false" or visit_interest == False:
        visit_interest_value=[False]
    city_list=[]
    district_list=[]
    district_region_list=[]
    filter_applied = False
    if districtregions:
        filter_applied = True
        district_region_list=districtregions.split(',')
        city_list=[]
        district_list=[]

    elif districts:
        filter_applied = True
        city_list=[]
        district_list=districts.split(',')
        district_region_list=[]
        dist_item = district_list[0]
        if counselor_obj.district_region.filter(district__id=dist_item).exists():
            district_list.remove(dist_item)
            dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
            for item in dist_region_obj:
                district_region_list.append(item.id)
        else:
            dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
            for item in dist_region_obj:
                district_region_list.append(item.id)

    elif citys:
        filter_applied = True
        city_list=citys.split(',')
        district_list=[]
        district_region_list=[]
        city_item = city_list[0]

        if counselor_obj.district.filter(city__id=city_item).exists():
            city_list.remove(city_item)
            dist_obj = counselor_obj.district.filter(city__id=city_item)
            for item in dist_obj:
                district_list.append(item.id)
        else:
            dist_obj = District.objects.filter(city__id=city_item)
            for item in dist_obj:
                district_list.append(item.id)

        for dist_item in district_list:
            if counselor_obj.district_region.filter(district__id=dist_item).exists():
                district_list.remove(dist_item)
                dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
            else:
                dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
    elif boarding_schools == "yes" and counselor_obj.boarding_schools:
        filter_applied = True
        board_obj = City.objects.get(slug="boarding-schools")
        city_list.append(board_obj.id)
    elif online_schools == "yes" and counselor_obj.online_schools:
        filter_applied = True
        online_obj = City.objects.get(slug="online-schools")
        city_list.append(online_obj.id)
    else:
        if len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) ==0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in District.objects.filter(city__id__in=city_list):
                district_list.append(item.id)
            for item in DistrictRegion.objects.filter(district__id__in=district_list):
                district_region_list.append(item.id)

        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                for item in district_regions_via_dist:
                    district_region_list.append(item.id)
        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) >0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in counselor_obj.district_region.all():
                district_region_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                dist_ob = District.objects.get(id=item)
                if counselor_obj.district_region.filter(district__id=item).exists():
                    district_list.remove(item)
                else:
                    district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                    for item in district_regions_via_dist:
                        district_region_list.append(item.id)
    if start_date and end_date:
        if not citys:
            citys=''
        if not districts:
            districts=''
        if not districtregions:
            districtregions=''
        if offset ==25:
            new_offset = offset*2
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
        startDateTime =start_date +  ' 00:00:01'
        endDateTime =end_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        all_users = []
        latest_timestamp = []
        if counselor_obj.online_schools:
            # checking if filter applied
            if filter_applied:
                # if user have filtered for boarding schools
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        # if searched for online schools
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_city = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })

                                application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                # if user haven't serached for boarding schools
                else:
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_city = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
            else:
            #if filters are not applied
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                else:
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
        else:
        # if user dont'have permission of online schools
            if len(city_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                    newcity_list = []
                    for city in counselor_obj.city.all():
                        newcity_list.append(city.name)
                    counsellorCity = []
                    for c in City.objects.filter(id__in=city_list):
                        counsellorCity.append(c.name)
                    new_city_list = [item for item in newcity_list if item in counsellorCity]
                    all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                    for item in all_city_user:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
            if len(district_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
            if len(district_region_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
        new = set()
        new_all_users = []
        for user in all_users:
            t = tuple(user.items())
            if t not in new:
                new.add(t)
                new_all_users.append(user)
        unique_timestamp_list = list(
            {v['id']: v for v in sorted(latest_timestamp, key=lambda i: i['timestamp'])}.values())
        for i in new_all_users:
            for j in unique_timestamp_list:
                if i['id'] == j['id']:
                    i['timestamp'] = j['timestamp']
        users_with_timestamp_list = []
        for user in new_all_users:
            if CounselingAction.objects.filter(user__id=user['id']).exists() or CommentSection.objects.filter(user__id=user['id']).exists():
                couns = CounselingAction.objects.filter(user__id=user['id']).last()
                couns_cmnt = CommentSection.objects.filter(user__id=user['id']).last()
                latest_item = None
                temp_type = None
                if couns and couns_cmnt and couns.action_updated_at < couns_cmnt.timestamp:

                    latest_item = couns_cmnt
                    temp_type= "comment"
                else:
                    if couns:
                        latest_item = couns
                        temp_type="action"
                if temp_type =="comment" and user['timestamp'] > latest_item.timestamp:
                    users_with_timestamp_list.append(user)
                elif temp_type =="action" and user['timestamp'] > latest_item.action_updated_at:
                    users_with_timestamp_list.append(user)
                # if couns and couns.action_updated_at < user['timestamp']:
                #     users_with_timestamp_list.append(user)
                # if couns_cmnt and couns_cmnt.timestamp < user['timestamp']:
                #     users_with_timestamp_list.append(user)
            # elif not CounselingAction.objects.filter(user__id=user['id']).exists() and not CommentSection.objects.filter(user__id=user['id']).exists():
            #     users_with_timestamp_list.append(user)
            else:
                users_with_timestamp_list.append(user)

        result = {}
        result['count'] =len(users_with_timestamp_list)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =users_with_timestamp_list
    else:
        if not citys:
            citys=''
        if not districts:
            districts=''
        if not districtregions:
            districtregions=''
        if offset ==25:
            new_offset = offset*2
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest

            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_next_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-user-list/?offset=' +str(new_prev_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest
        all_users = []
        latest_timestamp = []
        if counselor_obj.online_schools:
            if filter_applied:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            for city in counselor_obj.city.all():
                                new_city_list.append(city.name)
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_city = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                else:
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_city = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_city:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if online_schools == 'yes':
                            if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                                cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in cart_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in application_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
                            elif visit_interest == "true" or visit_interest == True:
                                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                                for item in enquiry_items_district_region:
                                    latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                    all_users.append({
                                        'name': item.user.name.title(),
                                        'id': item.user.id
                                    })
            else:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                else:
                    if len(city_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            cart_items_city = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_city = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                            newcity_list = []
                            for city in counselor_obj.city.all():
                                newcity_list.append(city.name)
                            counsellorCity = []
                            for c in City.objects.filter(id__in=city_list):
                                counsellorCity.append(c.name)
                            new_city_list = [item for item in newcity_list if item in counsellorCity]
                            all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list).order_by('-timestamp')[start_offset:end_offset]
                            for item in all_city_user:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            cart_items_district = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                    if len(district_region_list)>0:
                        if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                            cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })

                            cart_items_district_region = ChildSchoolCart.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in cart_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            application_items_district_region = SchoolApplication.objects.filter(school__online_school=True,school__collab__in=collab_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in application_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                        elif visit_interest == "true" or visit_interest == True:
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.user.name.title(),
                                    'id': item.user.id
                                })
        else:
            if len(city_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_city = ChildSchoolCart.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_city = SchoolApplication.objects.filter(school__school_city__id__in=city_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=False,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_city:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                if collab_status == "all" and (visit_interest == "none" or visit_interest == "false" or visit_interest ==False):
                    newcity_list = []
                    for city in counselor_obj.city.all():
                        newcity_list.append(city.name)
                    counsellorCity = []
                    for c in City.objects.filter(id__in=city_list):
                        counsellorCity.append(c.name)
                    new_city_list = [item for item in newcity_list if item in counsellorCity]
                    all_city_user = ParentAddress.objects.filter(region__name__in=new_city_list).order_by('-timestamp')[start_offset:end_offset]
                    for item in all_city_user:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
            if len(district_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_district = ChildSchoolCart.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_district = SchoolApplication.objects.filter(school__district__id__in=district_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=False,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
            if len(district_region_list)>0:
                if visit_interest == "none" or visit_interest == "false" or visit_interest ==False:
                    cart_items_district_region = ChildSchoolCart.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in cart_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    application_items_district_region = SchoolApplication.objects.filter(school__district_region__id__in=district_region_list,school__collab__in=collab_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in application_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                    enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })
                elif visit_interest == "true" or visit_interest == True:
                    enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=False,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                    for item in enquiry_items_district_region:
                        latest_timestamp.append({'id': item.user.id, "timestamp": item.timestamp})
                        all_users.append({
                            'name': item.user.name.title(),
                            'id': item.user.id
                        })

        new = set()
        new_all_users = []
        for user in all_users:
            t = tuple(user.items())
            if t not in new:
                new.add(t)
                new_all_users.append(user)
        unique_timestamp_list = list({v['id']: v for v in sorted(latest_timestamp, key=lambda i: i['timestamp'])}.values())
        for i in new_all_users:
            for j in unique_timestamp_list:
                if i['id'] == j['id']:
                    i['timestamp'] = j['timestamp']
        users_with_timestamp_list = []
        for user in new_all_users:
            if CounselingAction.objects.filter(counseling_user=counselor_obj,user__id=user['id']).exists() or CommentSection.objects.filter(counseling=counselor_obj,user__id=user['id']).exists():
                couns = CounselingAction.objects.filter(counseling_user=counselor_obj, user__id=user['id']).last()
                couns_cmnt = CommentSection.objects.filter(counseling=counselor_obj, user__id=user['id']).last()
                latest_item = None
                temp_type = None
                if couns and couns_cmnt and couns.action_updated_at < couns_cmnt.timestamp:

                    latest_item = couns_cmnt
                    temp_type= "comment"
                else:
                    if couns:
                        latest_item = couns
                        temp_type="action"
                if temp_type =="comment" and user['timestamp'] > latest_item.timestamp:
                    users_with_timestamp_list.append(user)
                elif temp_type =="action" and user['timestamp'] > latest_item.action_updated_at:
                    users_with_timestamp_list.append(user)
                else:
                    users_with_timestamp_list.append(user)
        result = {}
        result['count'] =len(users_with_timestamp_list)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =users_with_timestamp_list


    return result

class AllUserListCounsellor(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request, *args, **kwargs):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_user_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_user_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

def get_all_call_scheduled_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    citys = self.request.GET.get('citys', None)
    city_list=[]

    filter_applied = False
    if citys:
        filter_applied = True
        city_list=citys.split(',')

    else:
        if len(counselor_obj.city.all()) > 0:
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            district_obj = [district.city.id for district in counselor_obj.district.filter() if
                            counselor_obj.district]
            district_region_obj = [district_region.city.id for
                                   district_region in counselor_obj.district_region.filter() if
                                   counselor_obj.district_region]
            city_list = city_list + district_obj + district_region_obj
        online_obj = [online.id for online in
                      City.objects.filter(slug="online-schools") if counselor_obj.online_schools]
        boarding_obj = [boarding.id for boarding in
                        City.objects.filter(slug="boarding-schools") if counselor_obj.boarding_schools]
        res = city_list + online_obj + boarding_obj
        city_list = list(set(res))

    if start_date and end_date:
        if not citys:
            citys=''
        if offset == 25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys
            prev_url = None
        else:
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset + 25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys
            prev_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys
        startDateTime = start_date + ' 00:00:01'
        endDateTime = end_date + ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        all_users = []
        if len(city_list)>0:
            parent_obj = ParentCallScheduled.objects.filter(city__id__in=city_list,timestamp__date__range=[startDateTime.date(), endDateTime.date()]).order_by('-timestamp')[start_offset:end_offset]
            for item in parent_obj:
                all_users.append({
                    'name': item.name,
                    'id': item.id
                })
            new_city_list = []
            for city in counselor_obj.city.all():
                new_city_list.append(city.name)
        new = set()
        new_all_users = []
        for parent in all_users:
            if not CounselingAction.objects.filter(call_scheduled_by_parent__id=parent['id']).exists() and not CommentSection.objects.filter(call_scheduled_by_parent__id=parent['id']).exists():
                t = tuple(parent.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(parent)
        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users
    else:
        if not citys:
            citys=''
        if offset ==25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_offset)+'&citys='+str(citys)
            prev_url = None
        else:
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&citys='+str(citys)
            prev_url = 'api/v2/admin_custom/all-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&citys='+str(citys)
        all_users = []
        if len(city_list)>0:
            parent_obj = ParentCallScheduled.objects.filter(city__id__in=city_list).order_by(
                '-timestamp')[start_offset:end_offset]
            for item in parent_obj:
                all_users.append({
                    'name': item.name,
                    'id': item.id
                })
            new_city_list = []
            for city in counselor_obj.city.all():
                new_city_list.append(city.name)
        # elif len(city_list)==0:
        #     parent_obj = ParentCallScheduled.objects.filter().order_by(
        #         '-timestamp')[start_offset:end_offset]
        #     for item in parent_obj:
        #         all_users.append({
        #             'name': item.name,
        #             'id': item.id
        #         })
        #     new_city_list = []
        #     for city in counselor_obj.city.all():
        #         new_city_list.append(city.name)
        new = set()
        new_all_users = []
        for user in all_users:
            if not CounselingAction.objects.filter(call_scheduled_by_parent__id=user['id']).exists() and not CommentSection.objects.filter(call_scheduled_by_parent__id=user['id']).exists():
                t = tuple(user.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(user)

        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users
    return result

class AllCallScheduldByParentListCounsellor(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self, request, *args, **kwargs):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_call_scheduled_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_call_scheduled_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

def get_all_unassigned_call_scheduled_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    citys = self.request.GET.get('citys', None)
    city_list=[]

    filter_applied = False
    if citys:
        filter_applied = True
        city_list=citys.split(',')

    else:
        if len(counselor_obj.city.all()) > 0:
            for item in counselor_obj.city.all():
                city_list.append(item.id)
        all_couns_city = [city_obj.id for couns_cities in CounselorCAdminUser.objects.filter() for city_obj in couns_cities.city.all()]
        online_obj = [online.id for online in
                      City.objects.filter(slug="online-schools") if counselor_obj.online_schools or CounselorCAdminUser.objects.filter(online_schools=True)]
        boarding_obj = [boarding.id for boarding in
                        City.objects.filter(slug="boarding-schools") if counselor_obj.boarding_schools or CounselorCAdminUser.objects.filter(boarding_schools=True)]
        res = city_list + online_obj + boarding_obj + all_couns_city
        city_list = list(set(res))

    if start_date and end_date:
        if not citys:
            citys=''
        if offset == 25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date
            prev_url = None
        else:
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset + 25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date
            prev_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date
        startDateTime = start_date + ' 00:00:01'
        endDateTime = end_date + ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        all_users = []
        if len(city_list)>0:
            parent_obj = ParentCallScheduled.objects.filter(timestamp__date__range=[startDateTime.date(), endDateTime.date()]).exclude(city__id__in=city_list).order_by('-timestamp')[start_offset:end_offset]
            for item in parent_obj:
                all_users.append({
                    'name': item.name,
                    'id': item.id
                })
            new_city_list = []
            for city in counselor_obj.city.all():
                new_city_list.append(city.name)
        new = set()
        new_all_users = []
        for parent in all_users:
            if not CounselingAction.objects.filter(call_scheduled_by_parent__id=parent['id']).exists() and not CommentSection.objects.filter(call_scheduled_by_parent__id=parent['id']).exists():
                t = tuple(parent.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(parent)
        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users
    else:
        if not citys:
            citys=''
        if offset ==25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_offset)
            prev_url = None
        else:
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_next_offset)
            prev_url = 'api/v2/admin_custom/all-unassigned-parent-call-scheduled-list/?offset=' +str(new_prev_offset)
        all_users = []
        if len(city_list)>0:
            parent_obj = ParentCallScheduled.objects.exclude(city__id__in=city_list).order_by(
                '-timestamp')[start_offset:end_offset]
            for item in parent_obj:
                all_users.append({
                    'name': item.name,
                    'id': item.id
                })
            new_city_list = []
            for city in counselor_obj.city.all():
                new_city_list.append(city.name)
        # elif len(city_list)==0:
        #     parent_obj = ParentCallScheduled.objects.filter().order_by(
        #         '-timestamp')[start_offset:end_offset]
        #     for item in parent_obj:
        #         all_users.append({
        #             'name': item.name,
        #             'id': item.id
        #         })
        #     new_city_list = []
        #     for city in counselor_obj.city.all():
        #         new_city_list.append(city.name)
        new = set()
        new_all_users = []
        for user in all_users:
            if not CounselingAction.objects.filter(call_scheduled_by_parent__id=user['id']).exists() and not CommentSection.objects.filter(call_scheduled_by_parent__id=user['id']).exists():
                t = tuple(user.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(user)

        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users
    return result


class AllUnassignedCallScheduledByParentListCounsellor(APIView):
    permission_classes = (IsExecutiveUser,)

    def get(self, request, *args, **kwargs):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_unassigned_call_scheduled_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_unassigned_call_scheduled_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

class CounsellorFilterData(APIView):
    permission_classes = (IsExecutiveUser,)

    def get(self,request):
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
        city_list=[]
        district_list=[]
        district_region_list=[]
        if len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) ==0 and len(counselor_obj.district_region.all()) ==0:
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in District.objects.filter(city__id__in=city_list):
                district_list.append(item.id)
            for item in DistrictRegion.objects.filter(district__id__in=district_list):
                district_region_list.append(item.id)

        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) ==0:
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    # city_list.remove(item)
                    pass
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                for item in district_regions_via_dist:
                    district_region_list.append(item.id)
        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) >0:
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in counselor_obj.district_region.all():
                district_region_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    # city_list.remove(item)
                    pass
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                dist_ob = District.objects.get(id=item)
                if counselor_obj.district_region.filter(district__id=item).exists():
                    # district_list.remove(item)
                    pass
                else:
                    district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                    for item in district_regions_via_dist:
                        district_region_list.append(item.id)
        city_list_new = city_list
        citys = self.request.GET.get('citys', None)
        districts = self.request.GET.get('districts', None)

        if districts:
            city_list=[]
            district_list=districts.split(',')
            district_region_list=[]
            dist_item = district_list[0]
            dist_obj = District.objects.get(id=dist_item)
            city_id_of_dist = dist_obj.city.id
            if counselor_obj.district_region.filter(district__id=dist_item).exists():
                dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
            else:
                dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
            district_list = []
            if counselor_obj.district.filter(city__id=city_id_of_dist).exists():
                dist_obj = counselor_obj.district.filter(city__id=city_id_of_dist)
                for item in dist_obj:
                    district_list.append(item.id)
            else:
                dist_obj = District.objects.filter(city__id=city_id_of_dist)
                for item in dist_obj:
                    district_list.append(item.id)
            city_list=city_list_new

        elif citys:
            city_list=citys.split(',')
            district_list=[]
            district_region_list=[]
            city_item = city_list[0]
            if counselor_obj.district.filter(city__id=city_item).exists():
                dist_obj = counselor_obj.district.filter(city__id=city_item)
                for item in dist_obj:
                    district_list.append(item.id)
            else:
                dist_obj = District.objects.filter(city__id=city_item)
                for item in dist_obj:
                    district_list.append(item.id)

            for dist_item in district_list:
                if counselor_obj.district_region.filter(district__id=dist_item).exists():
                    dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
                    for item in dist_region_obj:
                        district_region_list.append(item.id)
                else:
                    dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
                    for item in dist_region_obj:
                        district_region_list.append(item.id)
            city_list=[]
            for item in counselor_obj.city.all():
                city_list.append(item.id)

        city_data = []
        for item in city_list:
            city_obj = City.objects.get(id=item)
            city_data.append({
                'id':city_obj.id,
                'name':city_obj.name,
            })
        district_data = []
        for item in district_list:
            district_obj = District.objects.get(id=item)
            district_data.append({
                'id':district_obj.id,
                'name':district_obj.name,
                'city_id':district_obj.city.id,
            })
        district_region_data = []
        for item in district_region_list:
            district_region_obj = DistrictRegion.objects.get(id=item)
            district_region_data.append({
                'id':district_region_obj.id,
                'name':str(district_region_obj.name) +' (' + str(district_region_obj.district.name)+')',
                'city_id':district_region_obj.city.id,
                'district_id':district_region_obj.district.id,
            })
        result={}
        result['city_list'] =city_data
        result['district_list'] =district_data
        result['district_region_list'] =district_region_data
        return Response(result,status=status.HTTP_200_OK)

class ChildAndPhoneListFromUser(APIView):
    permission_classes = (IsExecutiveUser,)

    def get(self,request,id):
        type=self.request.GET.get("type", 'user')
        if type == 'user':
            all_child = Child.objects.filter(user__id=id)
            child = []
            for item in all_child:
                child.append({
                    'id': item.id,
                    'name': item.name,
                })
            user_phone_number = get_user_phone_numbers_for_inside(id)
            # user_phone_number = get_user_phone_numbers(id)
            result={}
            result['childs'] = child
            result['phone_numbers'] = user_phone_number
            return Response(result,status=status.HTTP_200_OK)
        elif type=='enquiry':
            enquiry = SchoolEnquiry.objects.get(id=id)
            user_phone_number = []
            if enquiry.second_number_verified:
                if enquiry.second_number == enquiry.phone_no:
                    user_phone_number.append({
                        "number": enquiry.phone_no,
                        "valid":True
                    })
                else:
                    user_phone_number.append({
                        "number": enquiry.second_number,
                        "valid":True
                    })
                    user_phone_number.append({
                        "number": enquiry.phone_no,
                        "valid":False
                    })

            else:
                user_phone_number.append({
                    "number": enquiry.phone_no,
                    "valid":False
                })
            result={}
            result['childs'] = []
            result['phone_numbers'] = unique_a_list_of_dict(user_phone_number)
            return Response(result,status=status.HTTP_200_OK)
        else:
            return Response("something went wrong",status=status.HTTP_400_BAD_REQUEST)

class ItemDetailView(APIView):
    # permission_classes = (IsExecutiveUser,)
    def get(self,request,id):
        type=self.request.GET.get("type", 'user')
        user_enquiry = []
        user_application = []
        user_cart_items = []
        user_school_visit = []
        user_comments = []
        user_cities = []
        user_lead = []
        user_admission_done = []
        user_visit_scheduled = []
        related_user_visit_scheduled = []
        all_schools = []
        parent_call_scheduled = []
        all_school_wise_action_performed = []
        scheduled_visits_by_user = []
        related_enquiry_data = []
        user_timeline = []

        if type == 'user':
            if CounselingAction.objects.filter(user=id).exists():
                obj = CounselingAction.objects.get(user=id)
                current_action = obj.action.name if obj.action else "NA"
                first_Action = obj.first_action['action_name']
                first_Action_by = obj.counseling_user.user.user_ptr.name if f'{obj.counseling_user.user.user_ptr.first_name} {obj.counseling_user.user.user_ptr.last_name}' == obj.first_action['counsellor_name'] else obj.first_action['counsellor_name']

                time = str(obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")

                time2 = str(obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
                time2 = d.strftime("%Y-%m-%d %I:%M %p")
                if current_action == first_Action:
                    user_timeline.append({"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name})
                else:
                    d1 = {"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name}
                    d2 = {"name":first_Action,"value":time2,"by":first_Action_by}
                    user_timeline.extend((d1,d2))
            child_id=self.request.GET.get("child_id", None)
            if AdmissionDoneData.objects.filter(user__id=id).exists():
                admission_done = AdmissionDoneData.objects.filter(user__id=id).last()
                for school in admission_done.admission_done_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_admission_done.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })

                time = str(admission_done.admissiomn_done_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if admission_done.counseling_user:
                    user_timeline.append({"name":"Admission Done","value":time,"by":admission_done.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Admission Done","value":time,"by":"School"})
            if VisitScheduleData.objects.filter(user__id=id).exists():
                visits = VisitScheduleData.objects.filter(user__id=id).last()
                for school in visits.walk_in_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_visit_scheduled.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })

                time = str(visits.walk_in_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if visits.counseling_user:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":visits.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":"School"})
            if LeadGenerated.objects.filter(user__id=id).exists():
                lead = LeadGenerated.objects.get(user__id=id)
                for school in lead.lead_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_lead.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })

                time = str(lead.lead_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                user_timeline.append({"name":"Lead Generated","value":time,"by":lead.counseling_user.user.user_ptr.name})
            if SchoolView.objects.filter(user__id=id).exists():
                user_school_views= SchoolView.objects.filter(user__id=id).order_by("-updated_at")
                for view in user_school_views:
                    if view.school:
                        all_schools.append(view.school.id)
                        school_name = view.school.name
                        district_name = ''
                        if view.school.district:
                            district_name = view.school.district.name
                            school_name = str(view.school.name)+', '+str(view.school.district.name)
                        user_school_visit.append({
                            'school_name': school_name,
                            'school_slug': view.school.slug,
                            'total_views': view.count,
                            'first_view_time':view.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                            'last_view_time':view.updated_at.strftime("%a, %d-%b-%Y, %I:%M %p"),
                        })
                        if view.school.school_city:
                            city_name = view.school.school_city.name
                        else:
                            city_name = ''
                        if view.school.district_region:
                            district_region_name = view.school.district_region.name
                        else:
                            district_region_name = ''
                        user_cities.append({
                            'city':city_name,
                            'district':district_name,
                            'district_region':district_region_name,
                        })

            if SchoolEnquiry.objects.filter(user__id=id).exists():
                user_enquiries = SchoolEnquiry.objects.filter(user__id=id).order_by("-timestamp")
                for enq in user_enquiries:
                    all_schools.append(enq.school.id)
                    enq_class = 'N/A'
                    if enq.class_relation:
                        enq_class = enq.class_relation.name

                    user_enquiry.append({
                        'school_name': enq.school.name,
                        'school_slug': enq.school.slug,
                        'user_email': enq.email,
                        'interested_for_visit_but_no_data_provided': "Yes" if enq.interested_for_visit_but_no_data_provided else "No",
                        'query': enq.query,
                        'class':enq_class,
                        'timestamp':enq.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    })
                    if enq.interested_for_visit:
                        scheduled_visits_by_user.append({
                            'school_name': f"{enq.school.name}, {enq.school.district_region.name}, {enq.school.district.name} (Collab= {'Yes' if enq.school.collab else 'No'})",
                            "child_name":enq.child_name,
                            "second_number":enq.second_number,
                            "tentative_date_of_visit":enq.tentative_date_of_visit,
                        })
                    if enq.school.school_city:
                        city_name = enq.school.school_city.name
                    else:
                        city_name = ''
                    if enq.school.district:
                        district_name = enq.school.district.name
                    else:
                        district_name = ''
                    if enq.school.district_region:
                        district_region_name = enq.school.district_region.name
                    else:
                        district_region_name = ''
                    user_cities.append({
                        'city':city_name,
                        'district':district_name,
                        'district_region':district_region_name,
                    })
            if CommentSection.objects.filter(user__id=id).exists():
                user_comment= CommentSection.objects.filter(user__id=id).order_by("-timestamp")
                for comment in user_comment:
                    user_comments.append({
                        'comment': comment.comment,
                        'counsellor_name': comment.counseling.user.user_ptr.name,
                        'timestamp':comment.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    })
            if child_id:
                if ChildSchoolCart.objects.filter(user__id=id,child__id=child_id).exists():
                    user_carts= ChildSchoolCart.objects.filter(user__id=id,child__id=child_id).order_by("-timestamp")
                    for item in user_carts:
                        if item.school:
                            all_schools.append(item.school.id)
                            school_name = item.school.name
                            if item.school.district_region:
                                school_name = (item.school.name)+', '+str(item.school.district_region.name) +', '+ str(item.school.school_city.name)
                            user_cart_items.append({
                                'school_name': school_name,
                                'school_slug': item.school.slug,
                                'child_name':item.child.name,
                                'applying_for_class':item.child.class_applying_for.name,
                                'timestamp':item.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                            })
                        if item.school.school_city:
                            city_name = item.school.school_city.name
                        else:
                            city_name = ''
                        if item.school.district:
                            district_name = item.school.district.name
                        else:
                            district_name = ''
                        if item.school.district_region:
                            district_region_name = item.school.district_region.name
                        else:
                            district_region_name = ''
                        user_cities.append({
                            'city':city_name,
                            'district':district_name,
                            'district_region':district_region_name,
                        })
                if SchoolApplication.objects.filter(user__id=id,child__id=child_id).exists():
                    user_apps= SchoolApplication.objects.filter(user__id=id,child__id=child_id).order_by("-timestamp")
                    for apps in user_apps:
                        all_schools.append(apps.school.id)
                        if apps.registration_data:
                            user_application.append({
                                'school_name': apps.school.name,
                                'school_slug': apps.school.slug,
                                'child_name':apps.registration_data.child_name,
                                'applied_class':apps.registration_data.child_class_applying_for.name,
                                'timestamp':apps.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                            })
                        if apps.school.school_city:
                            city_name = apps.school.school_city.name
                        else:
                            city_name = ''
                        if apps.school.district:
                            district_name = apps.school.district.name
                        else:
                            district_name = ''
                        if apps.school.district_region:
                            district_region_name = apps.school.district_region.name
                        else:
                            district_region_name = ''
                        user_cities.append({
                            'city':city_name,
                            'district':district_name,
                            'district_region':district_region_name,
                        })

            else:
                if ChildSchoolCart.objects.filter(user__id=id).exists():
                    user_carts= ChildSchoolCart.objects.filter(user__id=id).order_by("-timestamp")
                    for item in user_carts:
                        if item.school:
                            all_schools.append(item.school.id)
                            school_name = item.school.name
                            if item.school.district_region:
                                school_name = (item.school.name)+', '+str(item.school.district_region.name)+', '+ str(item.school.school_city.name)
                            user_cart_items.append({
                                'school_name': school_name,
                                'school_slug': item.school.slug,
                                'child_name':item.child.name,
                                'applying_for_class':item.child.class_applying_for.name,
                                'timestamp':item.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                            })
                        if item.school.school_city:
                            city_name = item.school.school_city.name
                        else:
                            city_name = ''
                        if item.school.district:
                            district_name = item.school.district.name
                        else:
                            district_name = ''
                        if item.school.district_region:
                            district_region_name = item.school.district_region.name
                        else:
                            district_region_user_timelineme = ''
                        user_cities.append({
                            'city':city_name,
                            'district':district_name,
                            'district_region':district_region_name,
                        })
                if SchoolApplication.objects.filter(user__id=id).exists():
                    user_apps= SchoolApplication.objects.filter(user__id=id).order_by("-timestamp")
                    for apps in user_apps:
                        all_schools.append(apps.school.id)
                        if apps.registration_data:
                            user_application.append({
                                'school_name': apps.school.name,
                                'school_slug': apps.school.slug,
                                'child_name':apps.registration_data.child_name,
                                'applied_class':apps.registration_data.child_class_applying_for.name,
                                'timestamp':apps.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                            })
                        if apps.school.school_city:
                            city_name = apps.school.school_city.name
                        else:
                            city_name = ''
                        if apps.school.district:
                            district_name = apps.school.district.name
                        else:
                            district_name = ''
                        if apps.school.district_region:
                            district_region_name = apps.school.district_region.name
                        else:
                            district_region_name = ''
                        user_cities.append({
                            'city':city_name,
                            'district':district_name,
                            'district_region':district_region_name,
                        })
            new = set()
            new_user_cities = []
            for city in user_cities:
                t = tuple(city.items())
                if t not in new:
                    new.add(t)
                    new_user_cities.append(city)
            school_ids = list(set(all_schools))

            collab_non_collab_status = 'NA'

            #for collab school
            collab_status = [sch for sch_id in school_ids for sch in SchoolProfile.objects.filter(id=sch_id, collab=True)]
            #for non collab school
            non_collab_status = [sch for sch_id in school_ids for sch in SchoolProfile.objects.filter(id=sch_id, collab=False)]

            if len(collab_status) > 0 and len(non_collab_status) > 0:
                collab_non_collab_status = "Both"
            elif len(collab_status) > 0 and len(non_collab_status) == 0:
                collab_non_collab_status = "Collab"
            elif len(collab_status) == 0 and len(non_collab_status) > 0:
                collab_non_collab_status = "Non-Collab"

            comments_result = []
            for sch_id in school_ids:
                school_obj = SchoolProfile.objects.get(id=sch_id)
                sch_action = SchoolAction.objects.filter(school=school_obj).filter(Q(lead__user__id=id) | Q(visit__user__id=id) | Q(admissions__user__id=id)).first()

                school_enq_comments = SchoolPerformedCommentEnquiry.objects.filter(enquiry__school=school_obj, user__id=id).order_by("-timestamp")
                comments = SchoolCommentSection.objects.filter(school=school_obj).filter(
                    Q(visit__user__id=id) | Q(lead__user__id=id) | Q(admissions__user__id=id)).order_by(
                    "-timestamp")
                for com in school_enq_comments:
                    comments_result.append({
                        'comment': com.comment,
                        'timestamp': com.timestamp,
                    })

                for com in comments:
                    comments_result.append({
                        'comment': com.comment,
                        'timestamp': com.timestamp,
                    })
                res = {"id": school_obj.id, "name": school_obj.name,
                       "action_performed_by_school": sch_action.action.name if sch_action else None,
                       "comments": comments_result}
                if res["action_performed_by_school"] or res["comments"]:
                    all_school_wise_action_performed.append(res)
                else:
                    pass
            result={}
            cannot_view_number_permission = [{"school_id": obj, "school_name": SchoolProfile.objects.filter(id=obj).values("name")[0]["name"], "phone_number_cannot_viewed": "Yes"} for obj in
                                     list(set(all_schools)) if SchoolProfile.objects.filter(id=obj,
                                    phone_number_cannot_viewed=True) and
                                    ViewedParentPhoneNumberBySchool.objects.filter(
                                    school__id=obj).filter(
                                    Q(ongoing_application__user__id=id) |
                                    Q(enquiry__user__id=id) |
                                    Q(lead__user__id=id) |
                                    Q(visit__user__id=id))]
            number_view_permission = [{"school_id": obj, "school_name": SchoolProfile.objects.filter(id=obj).values("name")[0]["name"], "phone_number_cannot_viewed": "No"} for obj in
                                      list(set(all_schools)) if SchoolProfile.objects.filter(id=obj,
                                     phone_number_cannot_viewed=True) and not ViewedParentPhoneNumberBySchool.objects.filter(
                                    school__id=obj).filter(
                                    Q(ongoing_application__user__id=id) |
                                    Q(enquiry__user__id=id) |
                                    Q(lead__user__id=id) |
                                    Q(visit__user__id=id))]

            user_timeline = list({v['name']:v  for v in user_timeline }.values())

            result['all_schools_number_view_permission'] = cannot_view_number_permission + number_view_permission
            result['user_cities']=new_user_cities
            result['user_enquiries'] = user_enquiry
            result['user_application'] = user_application
            result['user_timeline'] = user_timeline
            result['user_cart_items'] = user_cart_items
            result['user_school_history'] = user_school_visit
            result['user_comments']=user_comments
            result['lead_schools'] = user_lead
            result['admission_done_schools'] = user_admission_done
            result['visit_scheduled_schools'] = user_visit_scheduled
            result['scheduled_visits_by_user'] = scheduled_visits_by_user
            result['all_school_wise_action_performed'] = all_school_wise_action_performed
            result['collab_non_collab_status'] = collab_non_collab_status
            result['related_enquiry_data'] = related_enquiry_data
            result['related_user_visit_scheduled'] = related_user_visit_scheduled
            return Response(result,status=status.HTTP_200_OK)
        elif type == 'enquiry':
            user_timeline = []
            if CounselingAction.objects.filter(enquiry_data__id=id).exists():
                obj = CounselingAction.objects.get(enquiry_data__id=id)
                current_action = obj.enquiry_action.name if obj.enquiry_action else "NA"
                first_Action = obj.first_action['action_name']
                first_Action_by = obj.counseling_user.user.user_ptr.name if f'{obj.counseling_user.user.user_ptr.first_name} {obj.counseling_user.user.user_ptr.last_name}' == obj.first_action['counsellor_name'] else obj.first_action['counsellor_name']

                time = str(obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")

                time2 = str(obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
                time2 = d.strftime("%Y-%m-%d %I:%M %p")
                if current_action == first_Action:
                    user_timeline.append({"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name})
                else:
                    d1 = {"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name}
                    d2 = {"name":first_Action,"value":time2,"by":first_Action_by}
                    user_timeline.extend((d1,d2))
            if AdmissionDoneData.objects.filter(enquiry__id=id).exists():
                admission_done = AdmissionDoneData.objects.filter(enquiry__id=id).last()
                for school in admission_done.admission_done_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_admission_done.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(admission_done.admissiomn_done_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if admission_done.counseling_user:
                    user_timeline.append({"name":"Admission Done","value":time,"by":admission_done.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Admission Done","value":time,"by":"School"})

            if VisitScheduleData.objects.filter(enquiry__id=id).exists():
                visits = VisitScheduleData.objects.filter(enquiry__id=id).last()
                for school in visits.walk_in_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_visit_scheduled.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(visits.walk_in_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if visits.counseling_user:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":visits.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":"School"})
            if LeadGenerated.objects.filter(enquiry__id=id).exists():
                lead = LeadGenerated.objects.get(enquiry__id=id)
                for school in lead.lead_for.all():
                    all_schools.append(school.id)
                    if school.district and school.district_region:
                        school_name = f"{school.name} ({school.district_region.name}, {school.district.name})"
                    elif school.district:
                        school_name = f"{school.name} ({school.district.name})"
                    else:
                        school_name = school.name
                    user_lead.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(lead.lead_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                user_timeline.append({"name":"Lead Generated","value":time,"by":lead.counseling_user.user.user_ptr.name})
            if SchoolEnquiry.objects.filter(id=id).exists():
                user_enquiries = SchoolEnquiry.objects.filter(id=id).order_by("-timestamp")
                enquiry_phone_number = list(user_enquiries)[0].phone_no
                all_related_enquiries = SchoolEnquiry.objects.filter(user__isnull=True,phone_no=enquiry_phone_number).exclude(id=id).order_by("-timestamp")
                for e in all_related_enquiries:
                    enq_class = 'NA'
                    if e.class_relation:
                        enq_class = e.class_relation.name
                    time = str(e.timestamp.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                    time = d.strftime("%Y-%m-%d %I:%M %p")
                    school_name = f"{e.school.name}, {e.school.district_region.name}, {e.school.school_city.name} (Collab= {'Yes' if e.school.collab else 'No'}) "
                    related_enquiry_data.append({
                        'school_name': school_name,
                        'school_slug': e.school.slug,
                        'user_email': e.email,
                        'interested_for_visit_but_no_data_provided': "Yes" if e.interested_for_visit_but_no_data_provided else "No",
                        'query': e.query,
                        'class':enq_class,
                        'timestamp':time,
                    })
                    if e.interested_for_visit:
                        related_user_visit_scheduled.append({
                            "child_name":e.child_name,
                            "school_name":school_name,
                            "tentative_date_of_visit":e.tentative_date_of_visit,
                        })
                for enq in user_enquiries:
                    all_schools.append(enq.school.id)
                    enq_class = 'NA'
                    if enq.class_relation:
                        enq_class = enq.class_relation.name
                    time = str(enq.timestamp.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                    time = d.strftime("%Y-%m-%d %I:%M %p")
                    user_enquiry.append({
                        'school_name': enq.school.name,
                        'school_slug': enq.school.slug,
                        'user_email': enq.email,
                        'interested_for_visit_but_no_data_provided': "Yes" if enq.interested_for_visit_but_no_data_provided else "No",
                        'query': enq.query,
                        'class':enq_class,
                        'timestamp':time,
                    })
                    if enq.interested_for_visit:
                        scheduled_visits_by_user.append({
                            "child_name":enq.child_name,
                            "second_number":enq.second_number,
                            "tentative_date_of_visit":enq.tentative_date_of_visit,
                        })
                    if enq.school.school_city:
                        city_name = enq.school.school_city.name
                    else:
                        city_name = ''
                    if enq.school.district:
                        district_name = enq.school.district.name
                    else:
                        district_name = ''
                    if enq.school.district_region:
                        district_region_name = enq.school.district_region.name
                    else:
                        district_region_name = ''
                    user_cities.append({
                        'city':city_name,
                        'district':district_name,
                        'district_region':district_region_name,
                    })
            if CommentSection.objects.filter(enquiry_comment__id=id).exists():
                user_comment= CommentSection.objects.filter(enquiry_comment__id=id).order_by("-timestamp")
                for comment in user_comment:
                    user_comments.append({
                        'comment': comment.comment,
                        'counsellor_name': comment.counseling.user.user_ptr.name,
                        'timestamp':comment.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    })
            new = set()
            new_user_cities = []
            for city in user_cities:
                t = tuple(city.items())
                if t not in new:
                    new.add(t)
                    new_user_cities.append(city)
            school_ids = list(set(all_schools))

            collab_non_collab_status = 'NA'

            #for collab school
            collab_status = [sch for sch_id in school_ids for sch in SchoolProfile.objects.filter(id=sch_id, collab=True)]
            #for non collab school
            non_collab_status = [sch for sch_id in school_ids for sch in SchoolProfile.objects.filter(id=sch_id, collab=False)]

            if len(collab_status) > 0 and len(non_collab_status) > 0:
                collab_non_collab_status = "Both"
            elif len(collab_status) > 0 and len(non_collab_status) == 0:
                collab_non_collab_status = "Collab"
            elif len(collab_status) == 0 and len(non_collab_status) > 0:
                collab_non_collab_status = "Non-Collab"

            comments_result = []
            for sch_id in school_ids:
                school_obj = SchoolProfile.objects.get(id=sch_id)
                sch_action = SchoolAction.objects.filter(school=school_obj).filter(Q(lead__enquiry__id=id) | Q(visit__enquiry__id=id) | Q(admissions__enquiry__id=id)).first()
                school_enq_comments = SchoolPerformedCommentEnquiry.objects.filter(enquiry__school=school_obj, enquiry__id=id).order_by("-timestamp")
                comments = SchoolCommentSection.objects.filter(school=school_obj).filter(Q(visit__enquiry__id=id) | Q(lead__enquiry__id=id) | Q(admissions__enquiry__id=id)).order_by("-timestamp")
                for com in school_enq_comments:
                    comments_result.append({
                            'comment':com.comment,
                            'timestamp':com.timestamp,
                            })

                for com in comments:
                    comments_result.append({
                                'comment': com.comment,
                                'timestamp': com.timestamp,
                                })
                res = {"id": school_obj.id, "name": school_obj.name, "action_performed_by_school": sch_action.action.name if sch_action else None, "comments": comments_result}
                if res["action_performed_by_school"] or res["comments"]:
                    all_school_wise_action_performed.append(res)
                else:
                    pass

            user_timeline = list({v['name']:v  for v in user_timeline }.values())

            result={}
            cannot_view_number_permission = [{"school_id" : obj,"school_name": SchoolProfile.objects.filter(id=obj).values("name")[0]["name"], "phone_number_cannot_viewed" : "Yes"} for obj in list(set(all_schools)) if SchoolProfile.objects.filter(id=obj, phone_number_cannot_viewed=True) and ViewedParentPhoneNumberBySchool.objects.filter(school__id=obj).filter(Q(school_performed_action_on_enquiry__enquiry__id=id) | Q(enquiry__id=id) | Q(lead__enquiry__id=id) | Q(visit__enquiry__id=id))]
            number_view_permission = [{"school_id" : obj,"school_name": SchoolProfile.objects.filter(id=obj).values("name")[0]["name"], "phone_number_cannot_viewed" : "No"} for obj in list(set(all_schools)) if SchoolProfile.objects.filter(id=obj, phone_number_cannot_viewed=True) and not ViewedParentPhoneNumberBySchool.objects.filter(school__id=obj).filter(Q(school_performed_action_on_enquiry__enquiry__id=id)| Q(enquiry__id=id) | Q(lead__enquiry__id=id) | Q(visit__enquiry__id=id))]
            result['all_schools_number_view_permission'] = cannot_view_number_permission+number_view_permission
            result['user_cities']=new_user_cities
            result['user_enquiries'] = user_enquiry
            result['user_application'] = user_application
            result['user_timeline'] = user_timeline
            result['user_cart_items'] = user_cart_items
            result['user_school_history'] = user_school_visit
            result['user_comments']=user_comments
            result['lead_schools']=user_lead
            result['admission_done_schools'] = user_admission_done
            result['visit_scheduled_schools'] = user_visit_scheduled
            result['scheduled_visits_by_user'] = scheduled_visits_by_user
            result['all_school_wise_action_performed'] = all_school_wise_action_performed
            result['collab_non_collab_status'] = collab_non_collab_status
            result['related_enquiry_data'] = related_enquiry_data
            result['related_user_visit_scheduled'] = related_user_visit_scheduled
            return Response(result,status=status.HTTP_200_OK)
        elif type == 'Callscheduledbyparent':
            user_timeline = []
            if CounselingAction.objects.filter(call_scheduled_by_parent__id=id).exists():
                obj = CounselingAction.objects.get(call_scheduled_by_parent__id=id)
                current_action = obj.action.name if obj.action else "NA"

                first_Action = obj.first_action['action_name']
                first_Action_by = obj.counseling_user.user.user_ptr.name if f'{obj.counseling_user.user.user_ptr.first_name} {obj.counseling_user.user.user_ptr.last_name}' == obj.first_action['counsellor_name'] else obj.first_action['counsellor_name']
                time = str(obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")

                time2 = str(obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
                time2 = d.strftime("%Y-%m-%d %I:%M %p")
                if current_action == first_Action:
                    user_timeline.append({"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name})
                else:
                    d1 = {"name":current_action,"value":time,"by":obj.counseling_user.user.user_ptr.name}
                    d2 = {"name":first_Action,"value":time2,"by":first_Action_by}
                    user_timeline.extend((d1,d2))


            if ParentCallScheduled.objects.filter(id=id).exists():
                obj = ParentCallScheduled.objects.get(id=id)
                time = str(obj.time_slot.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                parent_call_scheduled.append({
                    'id':obj.id,
                    'name':obj.name,
                    'time_slot': time,
                    'message':obj.message,
                    'city': obj.city.name,
                    'user_phone_number': set(list(get_user_phone_numbers(obj.user.id)) + [obj.phone]) if obj.user else [obj.phone],
                })
            if AdmissionDoneData.objects.filter(call_scheduled_by_parent__id=id).exists():
                admission_done = AdmissionDoneData.objects.get(call_scheduled_by_parent__id=id)
                for school in admission_done.admission_done_for.all():
                    school_name = school.name
                    user_admission_done.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(admission_done.admissiomn_done_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if admission_done.counseling_user:
                    user_timeline.append({"name":"Admission Done","value":time,"by":admission_done.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Admission Done","value":time,"by":"School"})
            if VisitScheduleData.objects.filter(call_scheduled_by_parent__id=id).exists():
                visits = VisitScheduleData.objects.get(call_scheduled_by_parent__id=id)
                for school in visits.walk_in_for.all():
                    school_name = school.name
                    user_visit_scheduled.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(visits.walk_in_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                if visits.counseling_user:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":visits.counseling_user.user.user_ptr.name})
                else:
                    user_timeline.append({"name":"Visit Scheduled","value":time,"by":"School"})
            if LeadGenerated.objects.filter(call_scheduled_by_parent__id=id).exists():
                lead = LeadGenerated.objects.get(call_scheduled_by_parent__id=id)
                for school in lead.lead_for.all():
                    school_name = school.name
                    user_lead.append({
                        'id':school.id,
                        'name':school_name,
                        'slug':school.slug,
                    })
                time = str(lead.lead_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                d = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                time = d.strftime("%Y-%m-%d %I:%M %p")
                user_timeline.append({"name":"Lead Generated","value":time,"by":lead.counseling_user.user.user_ptr.name})
            if CommentSection.objects.filter(call_scheduled_by_parent__id=id).exists():
                user_comment = CommentSection.objects.filter(call_scheduled_by_parent__id=id).order_by("-timestamp")
                for comment in user_comment:
                    user_comments.append({
                        'comment': comment.comment,
                        'counsellor_name': comment.counseling.user.user_ptr.name,
                        'timestamp':comment.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    })
            new = set()
            new_user_cities = []
            for city in user_cities:
                t = tuple(city.items())
                if t not in new:
                    new.add(t)
                    new_user_cities.append(city)
            user_timeline = list({v['name']:v  for v in user_timeline }.values())
            result={}
            result['all_schools_number_view_permission'] = []
            result['all_school_wise_action_performed'] = all_school_wise_action_performed
            result['parent_call_scheduled'] = parent_call_scheduled
            result['user_cities'] = new_user_cities
            result['user_enquiries'] = user_enquiry
            result['user_application'] = user_application
            result['user_timeline'] = user_timeline
            result['user_cart_items'] = user_cart_items
            result['user_school_history'] = user_school_visit
            result['user_comments'] = user_comments
            result['lead_schools'] = user_lead
            result['admission_done_schools'] = user_admission_done
            result['visit_scheduled_schools'] = user_visit_scheduled
            result['scheduled_visits_by_user'] = scheduled_visits_by_user
            result['collab_non_collab_status'] = 'NA'
            result['related_enquiry_data'] = related_enquiry_data
            result['related_user_visit_scheduled'] = related_user_visit_scheduled
            return Response(result,status=status.HTTP_200_OK)
        else:
            return Response("Provide Valid Type",status=status.HTTP_400_BAD_REQUEST)


class CommentSectionCreateView(APIView):
    permission_classes = (IsExecutiveUser,)
    def post(self,request, id,*args, **kwargs):
        type=self.request.GET.get("type", 'user')
        if request.data:
            if type == 'user':
                comment = request.data['comment']
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                user_obj = User.objects.get(id=id)
                new_comment = CommentSection.objects.create(user=user_obj,counseling=counselor_obj,comment=comment)
                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            elif type == 'enquiry':
                comment = request.data['comment']
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                enq_obj = SchoolEnquiry.objects.get(id=id)
                new_comment = CommentSection.objects.create(enquiry_comment=enq_obj,counseling=counselor_obj,comment=comment)
                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            elif type == 'Callscheduledbyparent':
                comment = request.data['comment']
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                parent_obj = ParentCallScheduled.objects.get(id=id)
                new_comment = CommentSection.objects.create(call_scheduled_by_parent=parent_obj,counseling=counselor_obj,comment=comment)
                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":"Provide Valid Type"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":"Provide Payload"}, status=status.HTTP_400_BAD_REQUEST)

class ActionListView(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        category = self.request.GET.get('category', None)
        if category:
            all_actions = ActionSection.objects.filter(category__name=category.capitalize())
            data = []
            for action in all_actions:
                act = []
                if SubActionSection.objects.filter(action_realtion__id=action.id).exists():
                    sub_action = SubActionSection.objects.filter(action_realtion__id=action.id)
                    for sub_act in sub_action:
                        act.append({
                            'id':sub_act.id,
                            'name':sub_act.name,
                            'slug':sub_act.slug,
                            'datetime':sub_act.requires_datetime,
                        })
                data.append({
                    'id':action.id,
                    'name':action.name,
                    'slug':action.slug,
                    'datetime':action.requires_datetime,
                    'sub_action':act,
                })
        else:
            all_actions = ActionSection.objects.all()
            data = []
            for action in all_actions:
                act = []
                if SubActionSection.objects.filter(action_realtion__id=action.id).exists():
                    sub_action = SubActionSection.objects.filter(action_realtion__id=action.id)
                    for sub_act in sub_action:
                        act.append({
                            'id':sub_act.id,
                            'name':sub_act.name,
                            'slug':sub_act.slug,
                            'datetime':sub_act.requires_datetime,
                        })
                data.append({
                    'id':action.id,
                    'name':action.name,
                    'slug':action.slug,
                    'datetime':action.requires_datetime,
                    'sub_action':act,
                })
        return Response({"result":data}, status=status.HTTP_200_OK)

class CounselingActionView(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            if SchoolEnquiry.objects.filter(id=id,user__isnull=True).exists() and type=='enquiry':
                enq_obj = SchoolEnquiry.objects.get(id=id)
                if CounselingAction.objects.filter(enquiry_data=enq_obj).exists():
                    action_obj = CounselingAction.objects.get(enquiry_data=enq_obj)
                    response={}
                    response['enq'] = enq_obj.id
                    if action_obj.counseling_user:
                        response['counseling_user'] = action_obj.counseling_user.id
                        response['counsellor_name'] = action_obj.counseling_user.user.user_ptr.name
                    else:
                        response['counseling_user'] = None
                        response['counsellor_name'] = None
                    if action_obj.enquiry_action:
                        response['action'] = action_obj.enquiry_action.name
                    else:
                        response['action'] = None
                    if action_obj.sub_actiom:
                        response['sub_action'] = action_obj.sub_actiom.name
                    else:
                        response['sub_action'] = None
                    action_updated_time = str(action_obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_updated_time, '%Y-%m-%d %H:%M:%S')
                    action_updated_time = d.strftime("%Y-%m-%d %I:%M %p")

                    action_created_time = str(action_obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_created_time, '%Y-%m-%d %H:%M:%S')
                    action_created_time = d.strftime("%Y-%m-%d %I:%M %p")
                    response['action_updated_at'] = action_updated_time
                    response['action_created_at'] = action_created_time
                    if action_obj.scheduled_time:
                        scheduled_time = str(action_obj.scheduled_time.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                        d = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                        scheduled_time = d.strftime("%Y-%m-%d %I:%M %p")
                        response['scheduled_time'] = scheduled_time
                    else:
                        response['scheduled_time'] = None

                    final_result=[]
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
                else:
                    final_result=[]
                    response={}
                    response['enq'] = None
                    response['counseling_user'] = None
                    response['counsellor_name'] = None
                    response['action'] = None
                    response['sub_action'] = None
                    response['action_updated_at'] = None
                    response['action_created_at'] = None
                    response['scheduled_time'] = None
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
            elif User.objects.filter(id=id).exists() and type=='user':
                user_obj = User.objects.get(id=id)
                if CounselingAction.objects.filter(user=user_obj).exists():
                    action_obj = CounselingAction.objects.get(user=user_obj)
                    response={}
                    if action_obj.user:
                        response['user'] = action_obj.user.id
                    else:
                        response['user'] = None
                    if action_obj.counseling_user:
                        response['counseling_user'] = action_obj.counseling_user.id
                        response['counsellor_name'] = action_obj.counseling_user.user.user_ptr.name
                    else:
                        response['counseling_user'] = None
                        response['counsellor_name'] = None
                    if action_obj.action:
                        response['action'] = action_obj.action.name
                    else:
                        response['action'] = None
                    if action_obj.sub_actiom:
                        response['sub_action'] = action_obj.sub_actiom.name
                    else:
                        response['sub_action'] = None
                    action_updated_time = str(action_obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_updated_time, '%Y-%m-%d %H:%M:%S')
                    action_updated_time = d.strftime("%Y-%m-%d %I:%M %p")

                    action_created_time = str(action_obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_created_time, '%Y-%m-%d %H:%M:%S')
                    action_created_time = d.strftime("%Y-%m-%d %I:%M %p")
                    response['action_updated_at'] = action_updated_time
                    response['action_created_at'] = action_created_time
                    if action_obj.scheduled_time:
                        scheduled_time = str(action_obj.scheduled_time.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                        d = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                        scheduled_time = d.strftime("%Y-%m-%d %I:%M %p")
                        response['scheduled_time'] = scheduled_time
                    else:
                        response['scheduled_time'] = None

                    final_result=[]
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
                else:
                    final_result=[]
                    response={}
                    response['user'] = None
                    response['counseling_user'] = None
                    response['counsellor_name'] = None
                    response['action'] = None
                    response['sub_action'] = None
                    response['action_updated_at'] = None
                    response['action_created_at'] = None
                    response['scheduled_time'] = None
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
            elif ParentCallScheduled.objects.filter(id=id).exists() and type=='Callscheduledbyparent':
                user_obj = ParentCallScheduled.objects.get(id=id)
                if CounselingAction.objects.filter(call_scheduled_by_parent=user_obj).exists():
                    action_obj = CounselingAction.objects.get(call_scheduled_by_parent=user_obj)
                    response={}
                    if action_obj.call_scheduled_by_parent:
                        response['call_scheduled_by_parent'] = action_obj.call_scheduled_by_parent.id
                    else:
                        response['call_scheduled_by_parent'] = None
                    if action_obj.counseling_user:
                        response['counseling_user'] = action_obj.counseling_user.id
                        response['counsellor_name'] = action_obj.counseling_user.user.user_ptr.name
                    else:
                        response['counseling_user'] = None
                        response['counsellor_name'] = None
                    if action_obj.action:
                        response['action'] = action_obj.action.name
                    else:
                        response['action'] = None
                    if action_obj.sub_actiom:
                        response['sub_action'] = action_obj.sub_actiom.name
                    else:
                        response['sub_action'] = None
                    action_updated_time = str(action_obj.action_updated_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_updated_time, '%Y-%m-%d %H:%M:%S')
                    action_updated_time = d.strftime("%Y-%m-%d %I:%M %p")

                    action_created_time = str(action_obj.action_created_at.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                    d = datetime.strptime(action_created_time, '%Y-%m-%d %H:%M:%S')
                    action_created_time = d.strftime("%Y-%m-%d %I:%M %p")
                    response['action_updated_at'] = action_updated_time
                    response['action_created_at'] = action_created_time
                    if action_obj.scheduled_time:
                        scheduled_time = str(action_obj.scheduled_time.astimezone(pytz.timezone('Asia/Calcutta'))).split("+")[0].split(".")[0]
                        d = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                        scheduled_time = d.strftime("%Y-%m-%d %I:%M %p")
                        response['scheduled_time'] = scheduled_time
                    else:
                        response['scheduled_time'] = None

                    final_result=[]
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
                else:
                    final_result=[]
                    response={}
                    response['user'] = None
                    response['counseling_user'] = None
                    response['counsellor_name'] = None
                    response['action'] = None
                    response['sub_action'] = None
                    response['action_updated_at'] = None
                    response['action_created_at'] = None
                    response['scheduled_time'] = None
                    final_result.append({
                    'results':response
                    })
                    return Response(final_result, status=status.HTTP_200_OK)
            else:
                return Response({"result":'Provide valid id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            if SchoolEnquiry.objects.filter(id=id,user__isnull=True).exists() and type=='enquiry':
                if request.data.get("action_id"):
                    action = ActionSection.objects.get(id=request.data.get("action_id"))
                else:
                    return Response({"result":'Provide Action ID'}, status=status.HTTP_400_BAD_REQUEST)
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                if CounselingAction.objects.filter(enquiry_data__id=id).exists():
                    action_obj = CounselingAction.objects.get(enquiry_data__id=id)
                else:
                    enq_obj = SchoolEnquiry.objects.get(id=id)
                    action_obj = CounselingAction.objects.create(enquiry_data=enq_obj)
                    data = {}
                    data['action_name'] = str(action.name)
                    data['action_id'] = str(action.id)
                    data['counsellor_name'] = counselor_obj.user.user_ptr.name or counselor_obj.user.user_ptr.username
                    data['counsellor_id'] = counselor_obj.id
                    data['current_counsellor_id'] = counselor_obj.id
                    data['previous_counsellor'] = '' if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor']
                    data['previous_counsellor_id'] = 0 if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor_id']
                    action_obj.first_action = data
                    action_obj.save()
                action_obj.enquiry_action = None
                action_obj.counseling_user = None
                action_obj.sub_actiom = None
                action_obj.scheduled_time = None
                action_obj.save()
                action_obj.enquiry_action = action
                action_obj.counseling_user = counselor_obj
                action_obj.save()
                if request.data.get("sub_action_id") and request.data.get("sub_action_id") != None:
                    sub_action_obj = SubActionSection.objects.get(id=request.data.get("sub_action_id"))
                    action_obj.sub_actiom = sub_action_obj
                    action_obj.save()
                if request.data.get('scheduled_time') and request.data.get('scheduled_date') and request.data.get("scheduled_time") != None and request.data.get('scheduled_date') !=None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' '+request.data.get('scheduled_time')
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                elif request.data.get('scheduled_date') and request.data.get('scheduled_time') ==None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' 00:00:01'
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                else:
                    pass
                if request.data.get('comment'):
                    comment = request.data.get('comment')
                    enq_obj = SchoolEnquiry.objects.get(id=id)
                    new_comment = CommentSection.objects.create(enquiry_comment=enq_obj,counseling=counselor_obj,comment=comment)
                enq_obj = SchoolEnquiry.objects.get(id=id)
                all_related_enquiries = SchoolEnquiry.objects.filter(user__isnull=True,phone_no=enq_obj.phone_no).exclude(id=enq_obj.id).order_by("-timestamp")
                for enq in all_related_enquiries:
                    if CounselingAction.objects.filter(enquiry_data=enq).exists():
                        action_obj_temp = CounselingAction.objects.get(enquiry_data=enq)
                    else:
                        action_obj_temp = CounselingAction.objects.create(enquiry_data=enq)
                        data_temp = {}
                        data_temp['action_name'] = "Repeat"
                        data_temp['action_id'] = "15"
                        data_temp['counsellor_name'] = counselor_obj.user.user_ptr.name or counselor_obj.user.user_ptr.username
                        data_temp['counsellor_id'] = counselor_obj.id
                        data_temp['current_counsellor_id'] = counselor_obj.id
                        data_temp['previous_counsellor'] = '' if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor']
                        data_temp['previous_counsellor_id'] = 0 if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor_id']
                        action_obj_temp.first_action = data_temp
                        action_obj_temp.save()
                    action_obj_temp.enquiry_action = None
                    action_obj_temp.counseling_user = None
                    action_obj_temp.sub_actiom = None
                    action_obj_temp.scheduled_time = None
                    action_obj.save()
                    action_obj_temp.enquiry_action = ActionSection.objects.get(id=15)
                    action_obj_temp.counseling_user = counselor_obj
                    action_obj_temp.save()

                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            elif User.objects.filter(id=id).exists() and type=='user':
                if request.data.get("action_id"):
                    action = ActionSection.objects.get(id=request.data.get("action_id"))
                else:
                    return Response({"result":'Provide Action ID'}, status=status.HTTP_400_BAD_REQUEST)
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                if CounselingAction.objects.filter(user__id=id).exists():
                    action_obj = CounselingAction.objects.get(user__id=id)
                else:
                    user_obj = User.objects.get(id=id)
                    action_obj = CounselingAction.objects.create(user=user_obj)
                    data = {}
                    data['action_name'] = str(action.name)
                    data['action_id'] = str(action.id)
                    data['counsellor_name'] = counselor_obj.user.user_ptr.name or counselor_obj.user.user_ptr.username
                    data['counsellor_id'] = counselor_obj.id
                    data['current_counsellor_id'] = counselor_obj.id
                    data['previous_counsellor'] = '' if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor']
                    data['previous_counsellor_id'] = 0 if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor_id']
                    action_obj.first_action = data
                    action_obj.save()
                action_obj.action = None
                action_obj.counseling_user = None
                action_obj.sub_actiom = None
                action_obj.scheduled_time = None
                action_obj.save()
                action_obj.action = action
                action_obj.counseling_user = counselor_obj
                action_obj.save()
                if request.data.get("sub_action_id") and request.data.get("sub_action_id") != None:
                    sub_action_obj = SubActionSection.objects.get(id=request.data.get("sub_action_id"))
                    action_obj.sub_actiom = sub_action_obj
                    action_obj.save()
                if request.data.get('scheduled_time') and request.data.get('scheduled_date') and request.data.get("scheduled_time") != None and request.data.get('scheduled_date') !=None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' '+request.data.get('scheduled_time')
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                elif request.data.get('scheduled_date') and request.data.get('scheduled_time') ==None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' 00:00:01'
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                else:
                    pass
                if request.data.get('comment'):
                    comment = request.data.get('comment')
                    user_obj = User.objects.get(id=id)
                    new_comment = CommentSection.objects.create(user=user_obj,counseling=counselor_obj,comment=comment)
                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            elif ParentCallScheduled.objects.filter(id=id).exists() and type=='Callscheduledbyparent':
                if request.data.get("action_id"):
                    action = ActionSection.objects.get(id=request.data.get("action_id"))
                else:
                    return Response({"result":'Provide Action ID'}, status=status.HTTP_400_BAD_REQUEST)
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                if CounselingAction.objects.filter(call_scheduled_by_parent__id=id).exists():
                    action_obj = CounselingAction.objects.get(call_scheduled_by_parent__id=id)
                else:
                    user_obj = ParentCallScheduled.objects.get(id=id)
                    action_obj = CounselingAction.objects.create(call_scheduled_by_parent=user_obj)
                    data = {}
                    data['action_name'] = str(action.name)
                    data['action_id'] = str(action.id)
                    data['counsellor_name'] = counselor_obj.user.user_ptr.name or counselor_obj.user.user_ptr.username
                    data['counsellor_id'] = counselor_obj.id
                    data['current_counsellor_id'] = counselor_obj.id
                    data['previous_counsellor'] = '' if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor']
                    data['previous_counsellor_id'] = 0 if not 'previous_counsellor' in action_obj.first_action else action_obj.first_action['previous_counsellor_id']
                    action_obj.first_action = data
                    action_obj.save()
                action_obj.action = None
                action_obj.counseling_user = None
                action_obj.sub_actiom = None
                action_obj.scheduled_time = None
                action_obj.save()
                action_obj.action = action
                action_obj.counseling_user = counselor_obj
                action_obj.save()
                if request.data.get("sub_action_id") and request.data.get("sub_action_id") != None:
                    sub_action_obj = SubActionSection.objects.get(id=request.data.get("sub_action_id"))
                    action_obj.sub_actiom = sub_action_obj
                    action_obj.save()
                if request.data.get('scheduled_time') and request.data.get('scheduled_date') and request.data.get("scheduled_time") != None and request.data.get('scheduled_date') !=None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' '+request.data.get('scheduled_time')
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                elif request.data.get('scheduled_date') and request.data.get('scheduled_time') ==None:
                    scheduled_Datetime = request.data.get('scheduled_date')+' 00:00:01'
                    scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                    scheduled_Datetime = make_aware(scheduled_Datetime)
                    action_obj.scheduled_time = scheduled_Datetime
                    action_obj.save()
                else:
                    pass
                if request.data.get('comment'):
                    comment = request.data.get('comment')
                    user_obj = ParentCallScheduled.objects.get(id=id)
                    CommentSection.objects.create(call_scheduled_by_parent=user_obj,counseling=counselor_obj,comment=comment)
                return Response({"result":"Action Created/Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":'Provide valid id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)

def get_all_past_user_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    schedule_date = self.request.GET.get('schedule_date', None)
    action_id = self.request.GET.get('action_id', None)
    sub_action_id = self.request.GET.get('sub_action_id', None)
    only_comments = self.request.GET.get('only_comments', 'no')
    collab_status = self.request.GET.get('collab',"all")
    if collab_status == "all":
        collab_value=[True,False]
    elif collab_status == "true" or collab_status == True:
        collab_value=[True]
    elif collab_status == "false" or collab_status == False:
        collab_value=[False]
    action_id_list = []
    sub_action_id_list = []
    if action_id:
        action_id_list.append(action_id)
    if sub_action_id:
        sub_action_id_list.append(sub_action_id)
    if schedule_date and action_id:
        startDateTime =schedule_date +  ' 00:00:01'
        endDateTime =schedule_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        elif len(action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&schedule_date='+schedule_date+'&action_id='+str(action_id)
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,action__id__in=action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        else:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&schedule_date='+schedule_date
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&schedule_date='+schedule_date
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&schedule_date='+schedule_date
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
    elif start_date and end_date:
        startDateTime =start_date +  ' 00:00:01'
        endDateTime =end_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,enquiry_comment__isnull=True).order_by("-timestamp")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.user:
                    all_users.append({
                        'name':comment.user.name,
                        'id':comment.user.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        elif len(action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&action_id='+str(action_id)
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,action__id__in=action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        else:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,enquiry_comment__isnull=True).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.user:
                    all_users.append({
                        'name':comment.user.name,
                        'id':comment.user.id,
                    })
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
    else:
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&only_comments='+only_comments
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&only_comments='+only_comments
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&only_comments='+only_comments
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,enquiry_comment__isnull=True).order_by("-timestamp")[start_offset:end_offset]
            all_users= []
            for comment in all_comments:
                if comment.user:
                    all_users.append({
                        'name':comment.user.name,
                        'id':comment.user.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&action_id='+str(action_id)+'&sub_action_id='+str(sub_action_id)
            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        elif len(action_id_list) > 0:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)+'&action_id='+str(action_id)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)+'&action_id='+str(action_id)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)+'&action_id='+str(action_id)
            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action__id__in=action_id_list,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })
        else:
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_offset)
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_next_offset)
                prev_url = 'api/v2/admin_custom/past-user-list/?offset=' +str(new_prev_offset)
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,enquiry_comment__isnull=True).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,enquiry_data__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.user:
                    all_users.append({
                        'name':comment.user.name,
                        'id':comment.user.id,
                    })
            for action in all_actions:
                if action.user:
                    all_users.append({
                        'name':action.user.name,
                        'id':action.user.id,
                    })

    new = set()
    new_all_users = []
    for user in all_users:
        t = tuple(user.items())
        if t not in new:
            new.add(t)
            new_all_users.append(user)

    result = {}
    result['count'] =len(new_all_users)
    result['next'] =next_url
    result['previous'] =prev_url
    result['results'] =new_all_users
    return result

class PastUserList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_past_user_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_past_user_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)


class CounsellorWiseSchoolList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request,*args,**kwargs):
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
        start_offset = 0
        end_offset = 25
        next_url = None
        prev_url = None
        offset = int(self.request.GET.get('offset', 25))
        school_name_in = self.request.GET.get('school_name', None)
        if offset ==25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/counsellor-wise-school-list/?offset=' +str(new_offset)+'&school_name='
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/counsellor-wise-school-list/?offset=' +str(new_next_offset)+'&school_name='
            prev_url = 'api/v2/admin_custom/counsellor-wise-school-list/?offset=?offset=' +str(new_prev_offset)+'&school_name='

        city_list = []
        district_list = []
        district_region_list =[]
        if len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) ==0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in District.objects.filter(city__id__in=city_list):
                district_list.append(item.id)
            for item in DistrictRegion.objects.filter(district__id__in=district_list):
                district_region_list.append(item.id)

        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                for item in district_regions_via_dist:
                    district_region_list.append(item.id)
        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) >0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in counselor_obj.district_region.all():
                district_region_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                dist_ob = District.objects.get(id=item)
                if counselor_obj.district_region.filter(district__id=item).exists():
                    district_list.remove(item)
                else:
                    district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                    for item in district_regions_via_dist:
                        district_region_list.append(item.id)
        school_list = []
        if school_name_in:
            if len(city_list) > 0:
                all_schools = SchoolProfile.objects.filter(school_city__id__in=city_list,name__icontains=school_name_in,collab=True)
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            if len(district_list) > 0:
                all_schools = SchoolProfile.objects.filter(district__id__in=district_list,name__icontains=school_name_in,collab=True)
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            if len(district_region_list) > 0:
                all_schools = SchoolProfile.objects.filter(district_region__id__in=district_region_list,name__icontains=school_name_in,collab=True)
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            new = set()
            new_school_list = []
            for school in school_list:
                t = tuple(school.items())
                if t not in new:
                    new.add(t)
                    new_school_list.append(school)
            result = {}
            result['count'] =len(new_school_list)
            result['next'] =None
            result['previous'] =None
            result['results'] =new_school_list
        else:
            if len(city_list) > 0:
                all_schools = SchoolProfile.objects.filter(school_city__id__in=city_list,collab=True)[start_offset:end_offset]
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            if len(district_list) > 0:
                all_schools = SchoolProfile.objects.filter(district__id__in=district_list,collab=True)[start_offset:end_offset]
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            if len(district_region_list) > 0:
                all_schools = SchoolProfile.objects.filter(district_region__id__in=district_region_list,collab=True)[start_offset:end_offset]
                for school in all_schools:
                    school_list.append({
                        'id': school.id,
                        'name' : f"{school.name} ({school.district_region.name}, {school.district.name})",
                        'slug': school.slug
                        })
            new = set()
            new_school_list = []
            for school in school_list:
                t = tuple(school.items())
                if t not in new:
                    new.add(t)
                    new_school_list.append(school)
            result = {}
            result['count'] =len(new_school_list)
            result['next'] =next_url
            result['previous'] =prev_url
            result['results'] =new_school_list
        return Response(result, status=status.HTTP_200_OK)


class LeadGeneratedCreateUpdateView(APIView):
    permission_classes = (IsExecutiveUser,)
    def patch(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            if SchoolEnquiry.objects.filter(id=id,user__isnull=True).exists() and type=='enquiry':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                enq_obj = SchoolEnquiry.objects.get(id=id)
                if LeadGenerated.objects.filter(enquiry=enq_obj,counseling_user=counselor_obj).exists():
                    lead = LeadGenerated.objects.filter(enquiry=enq_obj,counseling_user=counselor_obj).last()
                else:
                    lead = LeadGenerated.objects.create(enquiry=enq_obj,counseling_user=counselor_obj)
                lead.user_name=enq_obj.parent_name
                lead.user_email = enq_obj.email
                phone_no_list = []
                if enq_obj.phone_no:
                    phone_no_list.append(int(enq_obj.phone_no))
                lead.user_phone_number = phone_no_list
                lead.save()
                if request.data:
                    lead.budget = request.data['budget']
                    lead.classes = request.data['class']
                    lead.location = request.data['location']
                    lead.save()
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            lead.lead_for.add(school_obj)
                            if school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
                                subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
                                lead_obj = {"phone_no": lead.user_phone_number, "name": lead.user_name}
                                lead_generated_whatsapp_trigger(school_obj.phone_number_cannot_viewed, subscriber_obj.phone_number, lead_obj)
                    lead.save()
                return Response({"result":"Lead Created/Updated"}, status=status.HTTP_200_OK)
            elif User.objects.filter(id=id).exists() and type=='user':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                user_obj = User.objects.get(id=id)
                if LeadGenerated.objects.filter(user=user_obj,counseling_user=counselor_obj).exists():
                    lead = LeadGenerated.objects.filter(user=user_obj,counseling_user=counselor_obj).last()
                else:
                    lead = LeadGenerated.objects.create(user=user_obj,counseling_user=counselor_obj)
                lead.user_name=user_obj.name
                lead.user_email = user_obj.email
                lead.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(user_obj.id))])
                lead.save()
                if request.data:
                    lead.budget = request.data['budget']
                    lead.classes = request.data['class']
                    lead.location = request.data['location']
                    lead.save()
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            lead.lead_for.add(school_obj)
                            if school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
                                subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
                                lead_obj = {"phone_no": lead.user_phone_number, "name": lead.user_name}
                                lead_generated_whatsapp_trigger(school_obj.phone_number_cannot_viewed, subscriber_obj.phone_number, lead_obj)
                    lead.save()
                return Response({"result":"Lead Created/Updated"}, status=status.HTTP_200_OK)
            elif ParentCallScheduled.objects.filter(id=id).exists() and type=='Callscheduledbyparent':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                parent_obj = ParentCallScheduled.objects.get(id=id)
                if LeadGenerated.objects.filter(call_scheduled_by_parent=parent_obj,counseling_user=counselor_obj).exists():
                    lead = LeadGenerated.objects.filter(call_scheduled_by_parent=parent_obj,counseling_user=counselor_obj).last()
                else:
                    lead = LeadGenerated.objects.create(call_scheduled_by_parent=parent_obj,counseling_user=counselor_obj)
                lead.user_name=parent_obj.name
                # lead.user_email = parent_obj.email
                lead.user_phone_number = parent_obj.phone
                lead.save()
                if request.data:
                    lead.budget = request.data['budget']
                    lead.classes = request.data['class']
                    lead.location = request.data['location']
                    lead.save()
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            lead.lead_for.add(school_obj)
                            if school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
                                subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
                                lead_obj = {"phone_no": lead.user_phone_number, "name": lead.user_name}
                                lead_generated_whatsapp_trigger(school_obj.phone_number_cannot_viewed, subscriber_obj.phone_number, lead_obj)
                    lead.save()
                return Response({"result":"Lead Created/Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":'Provide valid id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)

def get_all_enquiry_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    citys = self.request.GET.get('citys', None)
    districts = self.request.GET.get('districts', None)
    districtregions = self.request.GET.get('districtregions', None)
    boarding_schools = self.request.GET.get('boarding', "no")
    online_schools = self.request.GET.get('online', "no")
    collab_status = self.request.GET.get('collab',"all")
    visit_interest = self.request.GET.get('visit_interest',"none")
    if collab_status == "all":
        collab_value=[True,False]
    elif collab_status == "true" or collab_status == True:
        collab_value=[True]
    elif collab_status == "false" or collab_status == False:
        collab_value=[False]

    if visit_interest == "none":
        visit_interest_value=[True,False]
    elif visit_interest == "true" or visit_interest == True:
        visit_interest_value=[True]
    elif visit_interest == "false" or visit_interest == False:
        visit_interest_value=[False]
    city_list=[]
    district_list=[]
    district_region_list=[]
    filter_applied = False
    if districtregions:
        filter_applied = True
        district_region_list=districtregions.split(',')
        city_list=[]
        district_list=[]

    elif districts:
        filter_applied = True
        city_list=[]
        district_list=districts.split(',')
        district_region_list=[]
        dist_item = district_list[0]
        if counselor_obj.district_region.filter(district__id=dist_item).exists():
            district_list.remove(dist_item)
            dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
            for item in dist_region_obj:
                district_region_list.append(item.id)
        else:
            dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
            for item in dist_region_obj:
                district_region_list.append(item.id)

    elif citys:
        filter_applied = True
        city_list=citys.split(',')
        district_list=[]
        district_region_list=[]
        city_item = city_list[0]
        if counselor_obj.district.filter(city__id=city_item).exists():
            city_list.remove(city_item)
            dist_obj = counselor_obj.district.filter(city__id=city_item)
            for item in dist_obj:
                district_list.append(item.id)
        else:
            dist_obj = District.objects.filter(city__id=city_item)
            for item in dist_obj:
                district_list.append(item.id)

        for dist_item in district_list:
            if counselor_obj.district_region.filter(district__id=dist_item).exists():
                district_list.remove(dist_item)
                dist_region_obj = counselor_obj.district_region.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
            else:
                dist_region_obj = DistrictRegion.objects.filter(district__id=dist_item)
                for item in dist_region_obj:
                    district_region_list.append(item.id)
    elif boarding_schools == "yes" and counselor_obj.boarding_schools:
        filter_applied = True
        board_obj = City.objects.get(slug="boarding-schools")
        city_list.append(board_obj.id)
    elif online_schools == "yes" and counselor_obj.online_schools:
        filter_applied = True
        online_obj = City.objects.get(slug="online-schools")
        city_list.append(online_obj.id)
    else:
        if len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) ==0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in District.objects.filter(city__id__in=city_list):
                district_list.append(item.id)
            for item in DistrictRegion.objects.filter(district__id__in=district_list):
                district_region_list.append(item.id)

        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) ==0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                for item in district_regions_via_dist:
                    district_region_list.append(item.id)
        elif len(counselor_obj.city.all()) > 0 and len(counselor_obj.district.all()) > 0 and len(counselor_obj.district_region.all()) >0:
            if counselor_obj.boarding_schools:
                board_obj = City.objects.get(slug="boarding-schools")
                city_list.append(board_obj.id)
            if counselor_obj.online_schools:
                online_obj = City.objects.get(slug="online-schools")
                city_list.append(online_obj.id)
            for item in counselor_obj.city.all():
                city_list.append(item.id)
            for item in counselor_obj.district.all():
                district_list.append(item.id)
            for item in counselor_obj.district_region.all():
                district_region_list.append(item.id)
            for item in city_list:
                city_ob = City.objects.get(id=item)
                if counselor_obj.district.filter(city__id=item).exists():
                    city_list.remove(item)
                else:
                    districts_via_city = District.objects.filter(city__id=item)
                    for item in districts_via_city:
                        district_list.append(item.id)
            for item in district_list:
                dist_ob = District.objects.get(id=item)
                if counselor_obj.district_region.filter(district__id=item).exists():
                    district_list.remove(item)
                else:
                    district_regions_via_dist = DistrictRegion.objects.filter(district__id=item)
                    for item in district_regions_via_dist:
                        district_region_list.append(item.id)
    if start_date and end_date:
        if not citys:
            citys=''
        if not districts:
            districts=''
        if not districtregions:
            districtregions=''
        if offset ==25:
            new_offset = offset*2
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&citys='+citys+'&districts='+districts+'&districtregions='+districtregions+"&collab="+collab_status+"&visit_interest="+visit_interest
        startDateTime =start_date +  ' 00:00:01'
        endDateTime =end_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        all_users = []
        if counselor_obj.online_schools:
            if filter_applied:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,timestamp__date__lte=endDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,timestamp__date__lte=endDateTime,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                else:
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
            else:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                else:
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
        else:
            if len(city_list)>0:
                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_city:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })
            if len(district_list)>0:
                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_district:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })
            if len(district_region_list)>0:
                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_district_region:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })
        new = set()
        new_all_users = []
        for user in all_users:
            if not CounselingAction.objects.filter(enquiry_data__id=user['id']).exists() and not CommentSection.objects.filter(enquiry_comment__id=user['id']).exists():
                t = tuple(user.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(user)

        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users
    else:
        if not citys:
            citys=''
        if not districts:
            districts=''
        if not districtregions:
            districtregions=''
        if offset ==25:
            new_offset = offset*2
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest

            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            if boarding_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&boarding=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            elif online_schools== "yes":
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&online=yes'+"&collab="+collab_status+"&visit_interest="+visit_interest
            else:
                next_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_next_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/all-enquiry-list/?offset=' +str(new_prev_offset)+'&citys='+str(citys)+'&districts='+str(districts)+'&districtregions='+str(districtregions)+"&collab="+collab_status+"&visit_interest="+visit_interest
        all_users = []
        if counselor_obj.online_schools:
            if filter_applied:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                else:
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if online_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
            else:
                if boarding_schools == 'yes':
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                else:
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__online_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
        elif counselor_obj.boarding_schools:
            if filter_applied:
                if online_schools == 'yes':

                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                else:
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_city:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        if boarding_schools == 'yes':
                            enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                            for item in enquiry_items_district_region:
                                all_users.append({
                                    'name': item.parent_name.title(),
                                    'id': item.id
                                })
            else:
                if online_schools == 'yes':
                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                else:

                    if len(city_list)>0:
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_city:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_list)>0:
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                    if len(district_region_list)>0:
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
                        enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__boarding_school=True,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).order_by('-timestamp')[start_offset:end_offset]
                        for item in enquiry_items_district_region:
                            all_users.append({
                                'name': item.parent_name.title(),
                                'id': item.id
                            })
        else:
            if len(city_list)>0:
                enquiry_items_city = SchoolEnquiry.objects.filter(user__isnull=True,school__school_city__id__in=city_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_city:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })
            if len(district_list)>0:
                enquiry_items_district = SchoolEnquiry.objects.filter(user__isnull=True,school__district__id__in=district_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_district:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })
            if len(district_region_list)>0:
                enquiry_items_district_region = SchoolEnquiry.objects.filter(user__isnull=True,school__district_region__id__in=district_region_list,school__collab__in=collab_value,interested_for_visit__in=visit_interest_value).exclude(school__online_school=True).order_by('-timestamp')[start_offset:end_offset]
                for item in enquiry_items_district_region:
                    all_users.append({
                        'name': item.parent_name.title(),
                        'id': item.id
                    })

        new = set()
        new_all_users = []
        for user in all_users:
            if not CounselingAction.objects.filter(enquiry_data__id=user['id']).exists() and not CommentSection.objects.filter(enquiry_comment__id=user['id']).exists():
                t = tuple(user.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(user)

        result = {}
        result['count'] =len(new_all_users)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =new_all_users

    return result

class AnonymousSchoolEnquiryList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request, *args, **kwargs):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_enquiry_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                data = get_all_enquiry_list(self,request,additional_offset)
                additional_offset = additional_offset+25
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

def get_all_past_enquiry_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    action_id = self.request.GET.get('action_id', None)
    schedule_date = self.request.GET.get('schedule_date', None)
    sub_action_id = self.request.GET.get('sub_action_id', None)
    only_comments = self.request.GET.get('only_comments', 'no')
    collab_status = self.request.GET.get('collab',"all")
    visit_interest = self.request.GET.get('visit_interest',"none")
    transferred = self.request.GET.get('transferred', None)
    shared = self.request.GET.get('shared', None)
    if collab_status == "all":
        collab_value=[True,False]
    elif collab_status == "true" or collab_status == True:
        collab_value=[True]
    elif collab_status == "false" or collab_status == False:
        collab_value=[False]

    if visit_interest == "none":
        visit_interest_value=[True,False]
    elif visit_interest == "true" or visit_interest == True:
        visit_interest_value=[True]
    elif visit_interest == "false" or visit_interest == False:
        visit_interest_value=[False]
    action_id_list = []
    sub_action_id_list = []
    if action_id:
        action_id_list.append(action_id)
    if sub_action_id:
        sub_action_id_list.append(sub_action_id)
    if schedule_date and action_id:
        startDateTime =schedule_date +  ' 00:00:01'
        endDateTime =schedule_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_next_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_prev_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,enquiry_action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.enquiry_action:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
           # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_next_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_prev_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
        elif len(action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,enquiry_action__id__in=action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.enquiry_action:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
        else:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.enquiry_action.name == 'Call Scheduled' and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&schedule_date=' + schedule_date
                prev_url = None
            else:

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&schedule_date=' + schedule_date
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&schedule_date=' + schedule_date
    elif start_date and end_date:
        startDateTime =start_date +  ' 00:00:01'
        endDateTime =end_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,user__isnull=True,enquiry_comment__school__collab__in=collab_value,enquiry_comment__interested_for_visit__in=visit_interest_value).order_by("-timestamp")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.enquiry_comment:
                    all_users.append({
                        'name':comment.enquiry_comment.parent_name,
                        'id':comment.enquiry_comment.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.enquiry_action and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
        elif len(action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_action__id__in=action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.enquiry_action and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest

        else:
            start_offset = offset - 25
            end_offset = offset

            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,user__isnull=True,enquiry_comment__school__collab__in=collab_value,enquiry_comment__interested_for_visit__in=visit_interest_value).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.enquiry_comment:
                    all_users.append({
                        'name':comment.enquiry_comment.parent_name,
                        'id':comment.enquiry_comment.id,
                    })
            for action in all_actions:
                if not action.enquiry_action.name == 'Repeat' and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date
    else:
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_offset)+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_next_offset)+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' +str(new_prev_offset)+'&only_comments='+only_comments+"&collab="+collab_status+"&visit_interest="+visit_interest
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,user__isnull=True,enquiry_comment__school__collab__in=collab_value).order_by("-timestamp")[start_offset:end_offset]
            all_users= []
            for comment in all_comments:
                if comment.enquiry_comment:
                    all_users.append({
                        'name':comment.enquiry_comment.parent_name,
                        'id':comment.enquiry_comment.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset

            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,enquiry_action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if action.enquiry_action and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
        elif len(action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset

            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,enquiry_action__id__in=action_id_list,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if action.enquiry_action and action.enquiry_data:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_offset) + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_next_offset) + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(
                    new_prev_offset) + '&action_id=' + str(action_id)+"&collab="+collab_status+"&visit_interest="+visit_interest
        else:
            start_offset = offset - 25
            end_offset = offset

            all_comments = CommentSection.objects.filter(counseling=counselor_obj,user__isnull=True,enquiry_comment__school__collab__in=collab_value,enquiry_comment__interested_for_visit__in=visit_interest_value).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,user__isnull=True,enquiry_data__school__collab__in=collab_value,enquiry_data__interested_for_visit__in=visit_interest_value).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.enquiry_comment:
                    all_users.append({
                        'name':comment.enquiry_comment.parent_name,
                        'id':comment.enquiry_comment.id,
                    })
            for action in all_actions:
                if action.enquiry_data and action.enquiry_action:
                    all_users.append({
                        'name':action.enquiry_data.parent_name,
                        'id':action.enquiry_data.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_offset)
                prev_url = None
            else:

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_next_offset)+"&collab="+collab_status+"&visit_interest="+visit_interest
                prev_url = 'api/v2/admin_custom/past-enquiry-list/?offset=' + str(new_prev_offset)+"&collab="+collab_status+"&visit_interest="+visit_interest
    new = set()
    new_all_users = []
    for user in all_users:
        t = tuple(user.items())
        if t not in new:
            new.add(t)
            new_all_users.append(user)

    result = {}
    result['count'] =len(new_all_users)
    result['next'] =next_url
    result['previous'] =prev_url
    result['results'] =new_all_users
    return result

class PastEnquiryList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_past_enquiry_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_past_enquiry_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

def get_all_past_call_scheduled_list(self,request,additional_offset):
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset
    start_date = self.request.GET.get('start_date', None)
    end_date = self.request.GET.get('end_date', None)
    action_id = self.request.GET.get('action_id', None)
    schedule_date = self.request.GET.get('schedule_date', None)
    sub_action_id = self.request.GET.get('sub_action_id', None)
    only_comments = self.request.GET.get('only_comments', 'no')
    action_id_list = []
    sub_action_id_list = []
    # import ipdb;ipdb.set_trace()
    if action_id:
        action_id_list.append(action_id)
    if sub_action_id:
        sub_action_id_list.append(sub_action_id)
    if schedule_date:
        startDateTime =schedule_date +  ' 00:00:01'
        endDateTime =schedule_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&schedule_date='+schedule_date+'&only_comments='+only_comments
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.action.name == 'Call Scheduled' and not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = None
            else:

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_next_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_prev_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
        elif len(action_id_list) > 0:
            start_offset = offset-25
            end_offset = offset

            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__range=[startDateTime.date(), endDateTime.date()],action__id__in=action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.action.name == 'Call Scheduled' and not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
                # if len(all_users) > 0:
                if offset == 25:
                    new_offset = offset * 2
                    next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                        new_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)
                    prev_url = None
                else:
                    new_next_offset = offset + 25
                    new_prev_offset = offset - 25
                    if new_prev_offset == 0:
                        new_prev_offset = ''
                    next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                        new_next_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)
                    prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                        new_prev_offset) + '&schedule_date=' + schedule_date + '&action_id=' + str(action_id)
        else:
            start_offset = offset - 25
            end_offset = offset
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,scheduled_time__date__lte=endDateTime,scheduled_time__date__gte=startDateTime).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if action.action.name == 'Call Scheduled' and not action.enquiry_action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_offset) + '&schedule_date=' + schedule_date
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_next_offset) + '&schedule_date=' + schedule_date
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_prev_offset) + '&schedule_date=' + schedule_date

    elif start_date and end_date:
        startDateTime =start_date +  ' 00:00:01'
        endDateTime =end_date +  ' 23:59:59'
        startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
        endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&start_date=' +start_date+'&end_date='+end_date+'&only_comments='+only_comments
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by("-timestamp")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.call_scheduled_by_parent:
                    all_users.append({
                        'name':comment.call_scheduled_by_parent.name,
                        'id':comment.call_scheduled_by_parent.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset

            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id) + '&sub_action_id=' + str(sub_action_id)
        elif len(action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset

            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,action__id__in=action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for action in all_actions:
                if not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date + '&action_id=' + str(
                    action_id)
        else:
            start_offset = offset - 25
            end_offset = offset
            all_comments = CommentSection.objects.filter(counseling=counselor_obj,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.call_scheduled_by_parent:
                    all_users.append({
                        'name':comment.call_scheduled_by_parent.name,
                        'id':comment.call_scheduled_by_parent.id,
                    })
            for action in all_actions:
                if action.action and not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_offset) + '&start_date=' + start_date + '&end_date=' + end_date
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_next_offset) + '&start_date=' + start_date + '&end_date=' + end_date
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_prev_offset) + '&start_date=' + start_date + '&end_date=' + end_date
    else:
        if only_comments == 'yes':
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_offset)+'&only_comments='+only_comments
                prev_url = None
            else:
                # start_offset = offset
                # end_offset = end_offset+offset
                # new_next_offset = start_offset + 25
                # new_prev_offset = start_offset - 25
                start_offset = offset-25
                end_offset = offset
                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&only_comments='+only_comments
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&only_comments='+only_comments
            all_comments = CommentSection.objects.filter(counseling=counselor_obj).order_by("-timestamp")[start_offset:end_offset]
            all_users= []
            for comment in all_comments:
                if comment.call_scheduled_by_parent:
                    all_users.append({
                        'name':comment.call_scheduled_by_parent.name,
                        'id':comment.call_scheduled_by_parent.id,
                    })
        elif len(action_id_list) > 0 and len(sub_action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action__id__in=action_id_list,sub_actiom__id__in=sub_action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = None
            else:

                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_next_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(
                    new_prev_offset) + '&action_id=' + str(action_id) + '&sub_action_id=' + str(sub_action_id)
        elif len(action_id_list) > 0:
            start_offset = offset - 25
            end_offset = offset
            if offset ==25:
                new_offset = offset*2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_offset)+'&action_id='+str(action_id)
                prev_url = None
            else:

                new_next_offset = offset +25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_next_offset)+'&action_id='+str(action_id)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' +str(new_prev_offset)+'&action_id='+str(action_id)
            all_users= []
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj,action__id__in=action_id_list).order_by("-action_updated_at")[start_offset:end_offset]
            for action in all_actions:
                if not action.action.name == 'Repeat' and action.call_scheduled_by_parent:
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
        else:
            start_offset = offset - 25
            end_offset = offset
            all_comments = CommentSection.objects.filter(counseling=counselor_obj).order_by("-timestamp")[start_offset:end_offset]
            all_actions = CounselingAction.objects.filter(counseling_user=counselor_obj).order_by("-action_updated_at")[start_offset:end_offset]
            all_users = []
            for comment in all_comments:
                if comment.call_scheduled_by_parent:
                    all_users.append({
                        'name':comment.call_scheduled_by_parent.name,
                        'id':comment.call_scheduled_by_parent.id,
                    })
            for action in all_actions:
                if action.call_scheduled_by_parent and not action.action.name == 'Repeat':
                    all_users.append({
                        'name':action.call_scheduled_by_parent.name,
                        'id':action.call_scheduled_by_parent.id,
                    })
            # if len(all_users) > 0:
            if offset == 25:
                new_offset = offset * 2
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_offset)
                prev_url = None
            else:
                new_next_offset = offset + 25
                new_prev_offset = offset - 25
                if new_prev_offset == 0:
                    new_prev_offset = ''
                next_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_next_offset)
                prev_url = 'api/v2/admin_custom/past-parent-call-scheduled-list/?offset=' + str(new_prev_offset)

    new = set()
    new_all_users = []
    for user in all_users:
        t = tuple(user.items())
        if t not in new:
            new.add(t)
            new_all_users.append(user)

    result = {}
    result['count'] =len(new_all_users)
    result['next'] =next_url
    result['previous'] =prev_url
    result['results'] =new_all_users
    return result

class PastCallScheduldByParentList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        additional_offset = None
        response ={"count":0,"next":None,"previous":None,"results":[]}
        i=0
        local_result = []
        local_count = 0
        local_next = None
        local_previous =None
        data = get_all_past_call_scheduled_list(self,request,additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i <28:
            if local_count<20:
                additional_offset = additional_offset+25
                data = get_all_past_call_scheduled_list(self,request,additional_offset)
                i+=1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count":local_count,"next":local_next,"previous":local_previous,"results":local_result}
        return Response(response, status=status.HTTP_200_OK)

class VisitScheduleDataCreateUpdateView(APIView):
    permission_classes = (IsExecutiveUser,)
    def patch(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            if SchoolEnquiry.objects.filter(id=id,user__isnull=True).exists() and type=='enquiry':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                enq_obj = SchoolEnquiry.objects.get(id=id)
                if VisitScheduleData.objects.filter(enquiry=enq_obj).exists():
                    visit = VisitScheduleData.objects.get(enquiry=enq_obj)
                else:
                    visit = VisitScheduleData.objects.create(enquiry=enq_obj,counseling_user=counselor_obj)
                visit.user_name=enq_obj.parent_name
                visit.user_email = enq_obj.email
                phone_no_list = []
                if enq_obj.phone_no:
                    phone_no_list.append(int(enq_obj.phone_no))
                visit.user_phone_number = phone_no_list
                visit.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            visit.walk_in_for.add(school_obj)
                            if school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
                                subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
                                visit_obj = {"phone_no": visit.user_phone_number, "name": visit.user_name}
                                visit_scheduled_whatsapp_trigger(school_obj.phone_number_cannot_viewed, subscriber_obj.phone_number, visit_obj)
                    visit.save()
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            elif User.objects.filter(id=id).exists() and type=='user':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                user_obj = User.objects.get(id=id)
                if VisitScheduleData.objects.filter(user=user_obj).exists():
                    visit = VisitScheduleData.objects.get(user=user_obj)
                else:
                    visit = VisitScheduleData.objects.create(user=user_obj,counseling_user=counselor_obj)
                visit.user_name=user_obj.name
                visit.user_email = user_obj.email
                visit.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(user_obj.id))])
                visit.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            visit.walk_in_for.add(school_obj)
                            if school_obj.send_whatsapp_notification and WhatsappSubscribers.objects.filter(user=school_obj.user,is_Subscriber=True).exists():
                                subscriber_obj = WhatsappSubscribers.objects.get(user=school_obj.user,is_Subscriber=True)
                                visit_obj = {"phone_no": visit.user_phone_number, "name": visit.user_name}
                                visit_scheduled_whatsapp_trigger(school_obj.phone_number_cannot_viewed, subscriber_obj.phone_number, visit_obj)
                    visit.save()
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            elif ParentCallScheduled.objects.filter(id=id).exists() and type=='Callscheduledbyparent':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                parent_obj = ParentCallScheduled.objects.get(id=id)
                if VisitScheduleData.objects.filter(call_scheduled_by_parent=parent_obj).exists():
                    visit = VisitScheduleData.objects.get(call_scheduled_by_parent=parent_obj)
                else:
                    visit = VisitScheduleData.objects.create(call_scheduled_by_parent=parent_obj,counseling_user=counselor_obj)
                visit.user_name=parent_obj.name
                # visit.user_email = parent_obj.email
                visit.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(parent_obj.id))])
                visit.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            visit.walk_in_for.add(school_obj)
                    visit.save()
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":'Provide valid id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)


class AdmissionDoneDataCreateUpdateView(APIView):
    permission_classes = (IsExecutiveUser,)
    def patch(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            if SchoolEnquiry.objects.filter(id=id,user__isnull=True).exists() and type=='enquiry':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                enq_obj = SchoolEnquiry.objects.get(id=id)
                if AdmissionDoneData.objects.filter(enquiry=enq_obj).exists():
                    adm_done = AdmissionDoneData.objects.get(enquiry=enq_obj)
                else:
                    adm_done = AdmissionDoneData.objects.create(enquiry=enq_obj,counseling_user=counselor_obj)
                adm_done.user_name=enq_obj.parent_name
                adm_done.user_email = enq_obj.email
                adm_done.child_name = request.data.get('child_name')
                phone_no_list = []
                if enq_obj.phone_no:
                    phone_no_list.append(int(enq_obj.phone_no))
                adm_done.user_phone_number = phone_no_list
                adm_done.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            adm_done.admission_done_for.add(school_obj)
                    adm_done.save()
                send_admission_done_mail_to_school_heads(adm_done.id)
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            elif User.objects.filter(id=id).exists() and type=='user':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                user_obj = User.objects.get(id=id)
                if AdmissionDoneData.objects.filter(user=user_obj).exists():
                    adm_done = AdmissionDoneData.objects.get(user=user_obj)
                else:
                    adm_done = AdmissionDoneData.objects.create(user=user_obj,counseling_user=counselor_obj)
                adm_done.user_name=user_obj.name
                adm_done.user_email = user_obj.email
                adm_done.child_name = request.data.get('child_name')
                adm_done.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(user_obj.id))])
                adm_done.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            adm_done.admission_done_for.add(school_obj)
                    adm_done.save()
                send_admission_done_mail_to_school_heads(adm_done.id)
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            elif ParentCallScheduled.objects.filter(id=id).exists() and type=='Callscheduledbyparent':
                cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
                counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
                parent_obj = ParentCallScheduled.objects.get(id=id)
                if AdmissionDoneData.objects.filter(call_scheduled_by_parent=parent_obj).exists():
                    adm_done = AdmissionDoneData.objects.get(call_scheduled_by_parent=parent_obj)
                else:
                    adm_done = AdmissionDoneData.objects.create(call_scheduled_by_parent=parent_obj,counseling_user=counselor_obj)
                adm_done.user_name=parent_obj.name
                adm_done.child_name = request.data.get('child_name')
                adm_done.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(parent_obj.id))])
                adm_done.save()
                if request.data:
                    schools = request.data['schools']
                    for id in schools:
                        if SchoolProfile.objects.filter(id=int(id)).exists():
                            school_obj = SchoolProfile.objects.get(id=int(id))
                            adm_done.admission_done_for.add(school_obj)
                    adm_done.save()
                send_admission_done_mail_to_school_heads(adm_done.id)
                return Response({"result":"WalkIn Schedule Created/Updated"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":'Provide valid id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)


class CallReocrdView(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request,id,*args,**kwargs):
        type = self.request.GET.get('type', 'user')
        if id:
            cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
            counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
            todays_date = date.today()
            current_date_time = datetime.now()
            if User.objects.filter(id=id).exists() and type == 'user':
                record_data = CounsellorDailyCallRecord.objects.get_or_create(counsellor=counselor_obj,first_call_at__date=todays_date)
                record_data[0].total_number_of_calls+=1
                record_data[0].user_calls+=1
                record_data[0].save()
                return Response("User Call Recorded", status=status.HTTP_200_OK)
            elif SchoolEnquiry.objects.filter(id=id).exists() and type == 'enquiry':
                record_data = CounsellorDailyCallRecord.objects.get_or_create(counsellor=counselor_obj,first_call_at__date=todays_date)
                record_data[0].total_number_of_calls+=1
                record_data[0].anonymous_enquiry_calls+=1
                record_data[0].save()
                return Response("Enquiry Call Recorded", status=status.HTTP_200_OK)
            else:
                return Response("Provide Valid type", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("Provide Valid ID", status=status.HTTP_400_BAD_REQUEST)

# class AdminSideCounsellorDataView(APIView):
#     # permission_classes = (IsAdminUser,)
#     def get(self,request,id):
#         counsellor = CounselorCAdminUser.objects.get(id=id)
#         start_date = self.request.GET.get('start_date', None)
#         end_date = self.request.GET.get('end_date', None)
#         if start_date and end_date:
#             start_time = self.request.GET.get('start_time', '00:00:01')
#             end_time = self.request.GET.get('end_time', '23:59:59')
#             if start_time == '':
#                 start_time = '00:00:01'
#             if end_time == '':
#                 end_time = '23:59:59'
#             startDateTime = f"{start_date} {start_time}"
#             endDateTime =  f"{end_date} {end_time}"

#             startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
#             endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
#             result = {}
#             # getting all the call record:
#             all_calls = CounsellorDailyCallRecord.objects.filter(counsellor=counsellor,first_call_at__date__lte=end_date,first_call_at__date__gte=start_date)
#             result['total_actions'] =CounselingAction.objects.filter(counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['user_total_actions'] =CounselingAction.objects.filter(enquiry_data__isnull=True,counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['enquiry_total_action'] =CounselingAction.objects.filter(user__isnull=True,counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             total_calls = 0
#             total_user_calls = 0
#             total_anonymous_calls = 0
#             for calls in all_calls:
#                 total_calls += calls.total_number_of_calls
#                 total_user_calls+=calls.user_calls
#                 total_anonymous_calls+=calls.anonymous_enquiry_calls
#             result['total_calls'] =total_calls
#             result['user_total_calls'] =total_user_calls
#             result['enquiry_total_calls'] =total_anonymous_calls
#             result['total_lead_generated'] = CounselingAction.objects.filter(action__name='Lead Generated',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Lead Generated',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['total_visit_scheduled'] =CounselingAction.objects.filter(action__name='Visit Scheduled',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Visit Scheduled',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['total_admission_done'] =CounselingAction.objects.filter(action__name='Admission Done',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Admission Done',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             # getting all action record
#             # getting all base action record
#             all_base_actions = ActionSection.objects.filter(category__name='Base')
#             for base_action in all_base_actions:
#                 action_key = "user_"+str(base_action.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,first_action__counsellor_id=id,action__id=base_action.id,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#                 result[action_key]=total_action
#             all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
#             for enquiry_actions in all_enquiry_actions:
#                 action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True,first_action__counsellor_id=id,enquiry_action__id=enquiry_actions.id,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#                 result[action_key]=total_action

#             results =[]
#             for item in result:
#                 results.append({
#                     'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
#                     'value':result[item],
#                 })
#         else:
#             result = {}
#             # getting all the call record:
#             all_calls = CounsellorDailyCallRecord.objects.filter(counsellor=counsellor)
#             result['total_actions'] =CounselingAction.objects.filter(counseling_user=counsellor).count()
#             result['user_total_actions'] =CounselingAction.objects.filter(enquiry_data__isnull=True,counseling_user=counsellor).count()
#             result['enquiry_total_action'] =CounselingAction.objects.filter(user__isnull=True,counseling_user=counsellor).count()
#             total_calls = 0
#             total_user_calls = 0
#             total_anonymous_calls = 0
#             for calls in all_calls:
#                 total_calls += calls.total_number_of_calls
#                 total_user_calls+=calls.user_calls
#                 total_anonymous_calls+=calls.anonymous_enquiry_calls
#             result['total_calls'] =total_calls
#             result['user_total_calls'] =total_user_calls
#             result['enquiry_total_calls'] =total_anonymous_calls
#             result['total_lead_generated'] = CounselingAction.objects.filter(action__name='Lead Generated',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Lead Generated',counseling_user=counsellor).count()
#             result['total_visit_scheduled'] =CounselingAction.objects.filter(action__name='Visit Scheduled',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Visit Scheduled',counseling_user=counsellor).count()
#             result['total_admission_done'] =CounselingAction.objects.filter(action__name='Admission Done',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Admission Done',counseling_user=counsellor).count()
#             # getting all action record
#             # getting all base action record
#             all_base_actions = ActionSection.objects.filter(category__name='Base')
#             for base_action in all_base_actions:
#                 action_key = "user_"+str(base_action.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,first_action__counsellor_id=id,action__id=base_action.id).count()
#                 result[action_key]=total_action
#             all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
#             for enquiry_actions in all_enquiry_actions:
#                 action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True,first_action__counsellor_id=id,enquiry_action__id=enquiry_actions.id).count()
#                 result[action_key]=total_action
#             all_parent_call_actions = ActionSection.objects.filter(category__name='Callscheduledbyparent')
#             for actions in all_parent_call_actions:
#                 action_key = "call_scheduled_by_parent_"+str(actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,first_action__counsellor_id=id,action__id=actions.id).count()
#                 result[action_key]=total_action

#             results =[]
#             for item in result:
#                 results.append({
#                     'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
#                     'value':result[item],
#                 })
#         return Response(results, status=status.HTTP_200_OK)

class AdminSideCounsellorDataView(APIView):
    permission_classes = (IsAdminUser,)
    def get(self,request,id):
        counsellor = CounselorCAdminUser.objects.get(id=id)
        start_date = self.request.GET.get('action_start_date', None)
        end_date = self.request.GET.get('action_end_date', None)
        enquiry_start_date = self.request.GET.get('enquiry_start_date', None)
        enquiry_end_date = self.request.GET.get('enquiry_end_date', None)
        collab = self.request.GET.get('collab', "None")
        action_type = self.request.GET.get('action_type', None)
        result = {}
        total_sum =[]
        if collab == "true":
            collab = True
        elif collab == "false":
            collab= False
        else:
            collab = "None"

        city_list =[]
        district_list= []
        dist_region_list =[]

        for city in counsellor.city.all():
            if city not in city_list:
                city_list.append(city.id)

        for district in counsellor.district.all():
            if district not in district_list:
                district_list.append(district.id)

        for dr in counsellor.district_region.all():
            if dr not in dist_region_list:
                dist_region_list.append(dr.id)

        if counsellor.online_schools:
            city = City.objects.get(name="Online Schools")
            if city:
                if city not in city_list:
                    city_list.append(city.id)

        if counsellor.boarding_schools:
            city = City.objects.get(name="Boarding Schools")
            if city:
                if city not in city_list:
                    city_list.append(city.id)



        if action_type == "user":
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime =  f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    # result = {}
                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_actions in all_base_actions:
                        if base_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=base_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,enquiry_data__isnull=True,sub_actiom__id=i.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                                result[i.name]=total_action
                        action_key = "user_"+str(base_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,enquiry_data__isnull=True,action__id=base_actions.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                        result[action_key]=total_action
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })
                    return Response(results, status=status.HTTP_200_OK)
                else:
                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_actions in all_base_actions:
                        if base_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=base_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,enquiry_data__isnull=True,sub_actiom__id=i.id).count()
                                result[i.name]=total_action
                        action_key = "user_"+str(base_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,enquiry_data__isnull=True,action__id=base_actions.id).count()
                        result[action_key]=total_action

                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

            return Response(results, status=status.HTTP_200_OK)

        elif action_type == "enquiry":
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime =  f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')

                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })
                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)
                    total_action_performed = len(set(list(chain(action1, action2, action3))))

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : "NA", #len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA" ,#res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime =  f"{enquiry_end_date} {end_time}"

                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')


                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)
                    total_action_performed = len(set(list(chain(action1, action2, action3))))

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})
                else:
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list).values_list("id", flat=True)


                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

            elif collab == True or collab ==False:
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime =  f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__collab=collab).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__collab=collab).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__school_city__in=city_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__district__in=district_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime,enquiry_data__school__district_region__in=dist_region_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__lte=endDateTime,timestamp__date__gte=startDateTime,school__collab=collab).values_list("id", flat=True)


                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : "NA" ,#len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry" : "NA",#res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})


                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime =  f"{enquiry_end_date} {end_time}"

                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')


                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__collab=collab).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__collab=collab).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })
                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__collab=collab,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__collab=collab,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__timestamp__date__lte=enquiryenddatetime,enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__collab=collab,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__lte=enquiryenddatetime,timestamp__date__gte=enquirystartdatetime,school__collab=collab).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                else:
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,sub_actiom__id=i.id,enquiry_data__school__collab=collab).count()
                                result[i.name]=total_action
                        action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,user__isnull=True,enquiry_action__id=enquiry_actions.id,enquiry_data__school__collab=collab).count()
                        result[action_key]=total_action
                        total_sum.append(result[action_key])
                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })
                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,school__collab=collab).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})
            return Response(results, status=status.HTTP_200_OK)

        else:
            return Response("action type is invalid", status=status.HTTP_400_BAD_REQUEST)

class AdminSideAnalyticsDataView(APIView):
    permission_classes = (IsAdminUser,)
    def get(self,request):
        start_date = self.request.GET.get('action_start_date', None)
        end_date = self.request.GET.get('action_end_date', None)
        enquiry_start_date = self.request.GET.get('enquiry_start_date', None)
        enquiry_end_date = self.request.GET.get('enquiry_end_date', None)
        collab = self.request.GET.get('collab', "None")
        action_type = self.request.GET.get('action_type', None)

        if collab == "true":
            collab = True
        elif collab == "false":
            collab= False
        else:
            collab = "None"
        if action_type == "user":
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime =  f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    result = {}

                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_actions in all_base_actions:
                        if base_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=base_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,sub_actiom__id=i.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                                result[i.name]=total_action
                        action_key = "user_"+str(base_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,action__id=base_actions.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                        result[action_key]=total_action

                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

                else:
                    result = {}
                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_actions in all_base_actions:
                        if base_actions.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=base_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,sub_actiom__id=i.id).count()
                                result[i.name]=total_action
                        action_key = "user_"+str(base_actions.name.lower().replace(" ","_"))
                        total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,action__id=base_actions.id).count()
                        result[action_key]=total_action

                    results =[]
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                        })

            else:
                results =[]
            return Response(results, status=status.HTTP_200_OK)

        elif action_type == "enquiry":
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime = f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    result = {}

                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True, sub_actiom__id=i.id,
                                                                               action_updated_at__date__lte=endDateTime,
                                                                               action_updated_at__date__gte=startDateTime).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User",
                                                                                                           "User:-"),
                            'value': result[item],
                        })
                    total_action_performed = CounselingAction.objects.filter(user__isnull=True,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.filter(timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime).values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : "NA",#len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA",#res,
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime = f"{enquiry_end_date} {end_time}"

                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')
                    result = {}

                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True, sub_actiom__id=i.id,
                                                                               enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                               enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User","User:-"),
                            'value': result[item],
                        })
                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : "NA", #len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA" ,#res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})
                    total_action_performed = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.filter(timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime).values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res,
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                else:
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                               sub_actiom__id=i.id).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,counseling_user=True
                                                                       ).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User",
                                                                                                           "User:-"),
                            'value': result[item],
                        })
                    total_action_performed = CounselingAction.objects.filter(user__isnull=True).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

            elif collab == True or collab == False:
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime = f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    result = {}

                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True, sub_actiom__id=i.id,
                                                                               action_updated_at__date__lte=endDateTime,
                                                                               action_updated_at__date__gte=startDateTime,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User",
                                                                                                           "User:-"),
                            'value': result[item],
                        })
                    total_action_performed = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=endDateTime,
                                                                       enquiry_data__timestamp__date__gte=startDateTime
                                                                       ,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.filter(timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,school__collab=collab).values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : "NA",#len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA",#res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})


                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime = f"{enquiry_end_date} {end_time}"

                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')
                    result = {}

                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True, sub_actiom__id=i.id,
                                                                               enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                               enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User",
                                                                                                           "User:-"),
                            'value': result[item],
                        })
                    total_action_performed = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime
                                                                       ,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.filter(timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime,school__collab=collab).values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res,
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})
                else:
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(user__isnull=True, sub_actiom__id=i.id,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action

                    results = []
                    for item in result:
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User", "User:-"),
                            'value': result[item],
                        })

                    total_action_performed = CounselingAction.objects.filter(user__isnull=True,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    result=SchoolEnquiry.objects.filter(school__collab=collab).values_list("id", flat=True)

                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

            return Response(results, status=status.HTTP_200_OK)
        else:
            return Response("action type is invalid", status=status.HTTP_400_BAD_REQUEST)
# class AdminSideCounsellorSelfDataView(APIView):
#     # permission_classes = (IsExecutiveUser,)
#     def get(self,request):
#         cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
#         counsellor = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
#         id = counsellor.id
#         start_date = self.request.GET.get('start_date', None)
#         end_date = self.request.GET.get('end_date', None)
#         if start_date and end_date:
#             start_time = self.request.GET.get('start_time', '00:00:01')
#             end_time = self.request.GET.get('end_time', '23:59:59')
#             if start_time == '':
#                 start_time = '00:00:01'
#             if end_time == '':
#                 end_time = '23:59:59'
#             startDateTime = f"{start_date} {start_time}"
#             endDateTime =  f"{end_date} {end_time}"
#             startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
#             endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
#             result = {}
#             # getting all the call record:
#             all_calls = CounsellorDailyCallRecord.objects.filter(counsellor=counsellor,first_call_at__date__lte=end_date,first_call_at__date__gte=start_date)
#             result['total_actions'] =CounselingAction.objects.filter(counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['user_total_actions'] =CounselingAction.objects.filter(enquiry_data__isnull=True,counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['enquiry_total_action'] =CounselingAction.objects.filter(user__isnull=True,counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             total_calls = 0
#             total_user_calls = 0
#             total_anonymous_calls = 0
#             for calls in all_calls:
#                 total_calls += calls.total_number_of_calls
#                 total_user_calls+=calls.user_calls
#                 total_anonymous_calls+=calls.anonymous_enquiry_calls
#             result['total_calls'] =total_calls
#             result['user_total_calls'] =total_user_calls
#             result['enquiry_total_calls'] =total_anonymous_calls
#             result['total_lead_generated'] = CounselingAction.objects.filter(action__name='Lead Generated',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Lead Generated',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['total_visit_scheduled'] =CounselingAction.objects.filter(action__name='Visit Scheduled',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Visit Scheduled',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             result['total_admission_done'] =CounselingAction.objects.filter(action__name='Admission Done',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count() + CounselingAction.objects.filter(enquiry_action__name='Admission Done',counseling_user=counsellor,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#             # getting all action record
#             # getting all base action record
#             all_base_actions = ActionSection.objects.filter(category__name='Base')
#             for base_action in all_base_actions:
#                 action_key = "user_"+str(base_action.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,first_action__counsellor_id=id,action__id=base_action.id,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#                 result[action_key]=total_action
#             all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
#             for enquiry_actions in all_enquiry_actions:
#                 action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True,first_action__counsellor_id=id,enquiry_action__id=enquiry_actions.id,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#                 result[action_key]=total_action
#             all_parent_call_actions = ActionSection.objects.filter(category__name='Callscheduledbyparent')
#             for parent_call_actions in all_parent_call_actions:
#                 action_key = "call_scheduled_by_parent_"+str(all_parent_call_actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True,first_action__counsellor_id=id,action__id=parent_call_actions.id,action_created_at__date__lte=endDateTime,action_created_at__date__gte=startDateTime).count()
#                 result[action_key]=total_action

#             results =[]
#             for item in result:
#                 results.append({
#                     'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
#                     'value':result[item],
#                 })
#         else:
#             result = {}
#             # getting all the call record:
#             all_calls = CounsellorDailyCallRecord.objects.filter(counsellor=counsellor)
#             result['total_actions'] =CounselingAction.objects.filter(counseling_user=counsellor).count()
#             result['user_total_actions'] =CounselingAction.objects.filter(enquiry_data__isnull=True,counseling_user=counsellor).count()
#             result['enquiry_total_action'] =CounselingAction.objects.filter(user__isnull=True,counseling_user=counsellor).count()
#             total_calls = 0
#             total_user_calls = 0
#             total_anonymous_calls = 0
#             for calls in all_calls:
#                 total_calls += calls.total_number_of_calls
#                 total_user_calls+=calls.user_calls
#                 total_anonymous_calls+=calls.anonymous_enquiry_calls
#             result['total_calls'] =total_calls
#             result['user_total_calls'] =total_user_calls
#             result['enquiry_total_calls'] =total_anonymous_calls
#             result['total_lead_generated'] = CounselingAction.objects.filter(action__name='Lead Generated',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Lead Generated',counseling_user=counsellor).count()
#             result['total_visit_scheduled'] =CounselingAction.objects.filter(action__name='Visit Scheduled',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Visit Scheduled',counseling_user=counsellor).count()
#             result['total_admission_done'] =CounselingAction.objects.filter(action__name='Admission Done',counseling_user=counsellor).count() + CounselingAction.objects.filter(enquiry_action__name='Admission Done',counseling_user=counsellor).count()
#             # getting all action record
#             # getting all base action record
#             all_base_actions = ActionSection.objects.filter(category__name='Base')
#             for base_action in all_base_actions:
#                 action_key = "user_"+str(base_action.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(enquiry_data__isnull=True,first_action__counsellor_id=id,action__id=base_action.id).count()
#                 result[action_key]=total_action
#             all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
#             for enquiry_actions in all_enquiry_actions:
#                 action_key = "enquiry_"+str(enquiry_actions.name.lower().replace(" ","_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True,first_action__counsellor_id=id,enquiry_action__id=enquiry_actions.id).count()
#                 result[action_key]=total_action
#             all_parent_call_actions = ActionSection.objects.filter(category__name='Callscheduledbyparent')
#             for parent_call_actions in all_parent_call_actions:
#                 action_key = "call_scheduled_by_parent_" + str(parent_call_actions.name.lower().replace(" ", "_"))
#                 total_action = CounselingAction.objects.filter(user__isnull=True, first_action__counsellor_id=id,
#                                                                action__id=parent_call_actions.id).count()
#                 result[action_key] = total_action

#             results =[]
#             for item in result:
#                 results.append({
#                     'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
#                     'value':result[item],
#                 })
#         return Response(results, status=status.HTTP_200_OK)

class AdminSideCounsellorSelfDataView(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        counsellor = CounselorCAdminUser.objects.get(user=cadmin_user_obj.id)
        id = counsellor.id
        action_type = self.request.GET.get('action_type', None)
        start_date = self.request.GET.get('action_start_date', None)
        end_date = self.request.GET.get('action_end_date', None)
        enquiry_start_date = self.request.GET.get('enquiry_start_date', None)
        enquiry_end_date = self.request.GET.get('enquiry_end_date', None)
        collab = self.request.GET.get('collab', "None")
        if collab == "true":
            collab = True
        elif collab == "false":
            collab= False
        else:
            collab = "None"

        city_list =[]
        district_list= []
        dist_region_list =[]

        for city in counsellor.city.all():
            if city not in city_list:
                city_list.append(city.id)

        for district in counsellor.district.all():
            if district not in district_list:
                district_list.append(district.id)

        for dr in counsellor.district_region.all():
            if dr not in dist_region_list:
                dist_region_list.append(dr.id)

        if counsellor.online_schools:
            city = City.objects.get(name="Online Schools")
            if city:
                if city not in city_list:
                    city_list.append(city.id)

        if counsellor.boarding_schools:
            city = City.objects.get(name="Boarding Schools")
            if city:
                if city not in city_list:
                    city_list.append(city.id)


        if action_type == 'user':
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime =  f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    result = {}
                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_action in all_base_actions:
                        if base_action.name == "Not Interested":
                            total= SubActionSection.objects.filter(action_realtion=base_action)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=id,sub_actiom__id=i.id,action_updated_at__date__lte=endDateTime,action_updated_at__date__gte=startDateTime).count()
                                result[i.name]=total_action
                        action_key = "user_" + str(base_action.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=id,enquiry_data__isnull=True, action__id=base_action.id,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime).count()
                        result[action_key] = total_action
                    results =[]
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })
                # elif start_date and end_date:
                #     start_time = '00:00:01'
                #     end_time = '23:59:59'
                #     startdatetime = f"{start_date} {start_time}"
                #     enddatetime =  f"{end_date} {end_time}"
                #     startdatetime = datetime.strptime(startdatetime, '%Y-%m-%d %X')
                #     enddatetime = datetime.strptime(enddatetime, '%Y-%m-%d %X')
                #     result = {}
                #     all_base_actions = ActionSection.objects.filter(category__name='Base')
                #     for base_actions in all_base_actions:
                #         if base_actions.name == "Not Interested":
                #             total = SubActionSection.objects.filter(action_realtion=base_actions)
                #             for i in total:
                #                 total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, sub_actiom__id=i.id,
                #                                                                action_created_at__date__lte=enddatetime,
                #                                                                action_created_at__date__gte=startdatetime).count()
                #                 result[i.name] = total_action
                #         action_key = "user_" + str(base_actions.name.lower().replace(" ", "_"))
                #         total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, enquiry_data__isnull=True,
                #                                                        action__id=base_actions.id,
                #                                                        action_created_at__date__lte=enddatetime,
                #                                                        action_created_at__date__gte=startdatetime).count()
                #         result[action_key] = total_action
                #
                #     results =[]
                #     for item in result:
                #         results.append({
                #             'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                #             'value':result[item],
                #         })
                else:
                    result = {}
                    all_base_actions = ActionSection.objects.filter(category__name='Base')
                    for base_actions in all_base_actions:
                        if base_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=base_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, enquiry_data__isnull=True,sub_actiom__id=i.id).count()
                                result[i.name] = total_action
                        action_key = "user_" + str(base_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, enquiry_data__isnull=True,
                                                                       action__id=base_actions.id).count()
                        result[action_key] = total_action

                    results =[]
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry","Enquiry:-").replace("User","User:-"),
                            'value':result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })
            else:
                results =[]
            return Response(results, status=status.HTTP_200_OK)

        elif action_type == 'enquiry':
            if collab == "None":
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime = f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    total_sum =[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                               sub_actiom__id=i.id,
                                                                               action_updated_at__date__lte=endDateTime,
                                                                               action_updated_at__date__gte=startDateTime).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User", "User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    action_updated_at__date__lte=endDateTime,
                                                                    action_updated_at__date__gte=startDateTime,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : "NA", #len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA", #res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})


                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime = f"{enquiry_end_date} {end_time}"
                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')
                    total_sum =[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,
                                                                               user__isnull=True, sub_actiom__id=i.id,
                                                                               enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                               enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User","User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry":  res,
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})
                else:
                    total_sum =[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                               sub_actiom__id=i.id).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                    enquiry_action__id=enquiry_actions.id).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User", "User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                      enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                      enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                      enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

            elif collab == True or collab == False:
                if start_date and end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    startDateTime = f"{start_date} {start_time}"
                    endDateTime = f"{end_date} {end_time}"
                    startDateTime = datetime.strptime(startDateTime, '%Y-%m-%d %X')
                    endDateTime = datetime.strptime(endDateTime, '%Y-%m-%d %X')
                    total_sum=[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                               sub_actiom__id=i.id,
                                                                               action_updated_at__date__lte=endDateTime,
                                                                               action_updated_at__date__gte=startDateTime,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       action_updated_at__date__lte=endDateTime,
                                                                       action_updated_at__date__gte=startDateTime,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User","User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    action_updated_at__date__lte=endDateTime,
                                                                    action_updated_at__date__gte=startDateTime,
                                                                    enquiry_data__school__collab=collab,
                                                                    enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    action_updated_at__date__lte=endDateTime,
                                                                    action_updated_at__date__gte=startDateTime,
                                                                    enquiry_data__school__collab=collab,
                                                                    enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    action_updated_at__date__lte=endDateTime,
                                                                    action_updated_at__date__gte=startDateTime,
                                                                    enquiry_data__school__collab=collab,
                                                                    enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,school__collab=collab).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : "NA", #len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": "NA" ,#res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                elif enquiry_start_date and enquiry_end_date:
                    start_time = '00:00:01'
                    end_time = '23:59:59'
                    enquirystartdatetime = f"{enquiry_start_date} {start_time}"
                    enquiryenddatetime = f"{enquiry_end_date} {end_time}"
                    enquirystartdatetime = datetime.strptime(enquirystartdatetime, '%Y-%m-%d %X')
                    enquiryenddatetime = datetime.strptime(enquiryenddatetime, '%Y-%m-%d %X')
                    total_sum=[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=counsellor.id,
                                                                               user__isnull=True, sub_actiom__id=i.id,
                                                                               enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                               enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=counsellor.id, user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                       enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User","User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                     enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                     enquiry_data__school__school_city__in=city_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                     enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                    enquiry_data__school__district__in=district_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,
                                                                    enquiry_data__timestamp__date__lte=enquiryenddatetime,
                                                                    enquiry_data__timestamp__date__gte=enquirystartdatetime,
                                                                    enquiry_data__school__district_region__in=dist_region_list,enquiry_data__school__collab=collab).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,timestamp__date__gte=enquirystartdatetime,timestamp__date__lte=enquiryenddatetime,school__collab=collab).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

                else:
                    total_sum=[]
                    result = {}
                    all_enquiry_actions = ActionSection.objects.filter(category__name='Enquiry')
                    for enquiry_actions in all_enquiry_actions:
                        if enquiry_actions.name == "Not Interested":
                            total = SubActionSection.objects.filter(action_realtion=enquiry_actions)
                            for i in total:
                                total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                               sub_actiom__id=i.id,
                                                                               enquiry_data__school__collab=collab).count()
                                result[i.name] = total_action
                        action_key = "enquiry_" + str(enquiry_actions.name.lower().replace(" ", "_"))
                        total_action = CounselingAction.objects.filter(counseling_user=id, user__isnull=True,
                                                                       enquiry_action__id=enquiry_actions.id,
                                                                       enquiry_data__school__collab=collab).count()
                        result[action_key] = total_action
                        total_sum.append(result[action_key])
                    results = []
                    for item in result:
                        link_action = ActionSection.objects.filter(category__name='Base' if action_type == 'user' else action_type.title(),slug=item.lstrip('user_').lstrip('enquiry_').replace('_', '-')).first()
                        results.append({
                            'name': item.replace("_", " ").title().replace("Enquiry", "Enquiry:-").replace("User", "User:-"),
                            'value': result[item],
                            'link': f'api/v2/admin_custom/past-{item.split("_")[0]}-list/?action_id={link_action.id if link_action else ""}',
                        })

                    action1 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__school_city__in=city_list).values_list("enquiry_data", flat=True)
                    action2 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__district__in=district_list).values_list("enquiry_data", flat=True)
                    action3 = CounselingAction.objects.filter(counseling_user__id=counsellor.id,user__isnull=True,enquiry_data__school__collab=collab,enquiry_data__school__district_region__in=dist_region_list).values_list("enquiry_data", flat=True)

                    res1=SchoolEnquiry.objects.filter(school__school_city__in=city_list,school__collab=collab).values_list("id", flat=True)
                    res2=SchoolEnquiry.objects.filter(school__district__in=district_list,school__collab=collab).values_list("id", flat=True)
                    res3=SchoolEnquiry.objects.filter(school__district_region__in=dist_region_list,school__collab=collab).values_list("id", flat=True)

                    total_action_performed = list(set(list(chain(action1, action2, action3))))
                    result = list(set(list(chain(res1, res2, res3))))
                    res = len(result)
                    d = {
                        "Total not Processed" : len([i for i in result if i not in total_action_performed]),
                        "Total Enquiry": res
                        }
                    for i in d:
                        results.insert(0,{"name":i,"value":d[i]})

            return Response(results, status=status.HTTP_200_OK)

        else:
            return Response("action type is invalid", status=status.HTTP_400_BAD_REQUEST)



class SchoolWiseList(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self,request,slug,type):
        start_offset = 0
        end_offset = 25
        next_url = None
        prev_url = None
        offset = int(self.request.GET.get('offset', 25))
        if offset ==25:
            new_offset = offset*2
            next_url = f"api/v2/admin_custom/school/{slug}/{type}/list/?offset={str(new_offset)}"
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = f"api/v2/admin_custom/school/{slug}/{type}/list/?offset={str(new_next_offset)}"
            prev_url = f"api/v2/admin_custom/school/{slug}/{type}/list/?offset={str(new_prev_offset)}"
        new_data = []
        if type == 'leads' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = LeadGenerated.objects.filter(lead_for__slug=slug).order_by("-lead_updated_at")[start_offset:end_offset]
        elif type == 'visits' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = VisitScheduleData.objects.filter(walk_in_for__slug=slug).order_by("-walk_in_updated_at")[start_offset:end_offset]
        elif type == 'admissions' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = AdmissionDoneData.objects.filter(admission_done_for__slug=slug).order_by("-admissiomn_done_updated_at")[start_offset:end_offset]
            other_data = SchoolAction.objects.filter(school__slug=slug,visit__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            for item in other_data:
                if item.action.name == 'Admission Done' and item.lead:
                    new_data.append(item.lead)
                elif item.action.name == 'Admission Done' and item.visit:
                    new_data.append(item.visit)
                else:
                    pass
        else:
            return Response({"results":"Please Provide Slug/Type"},status=status.HTTP_404_NOT_FOUND)
        result = []
        for item in total_data:
            if (type=='leads' and not SchoolAction.objects.filter(lead=item,school__slug=slug).exists()) or (type=='visits' and not SchoolAction.objects.filter(visit=item,school__slug=slug).exists()) or (type=='admissions' and not SchoolAction.objects.filter(admissions=item,school__slug=slug).exists()):
                # all_field = []
                # for field in item._meta.get_fields():
                #     all_field.append(field.name)
                # location = ''
                # budget = ''
                # classes = ''
                # if 'location' in all_field:
                #     location = item.location
                # if 'budget' in all_field:
                #     budget = item.budget
                # if 'classes' in all_field:
                #     classes = item.classes
                if type == 'visits' or type=='admissions':
                    location = ''
                    budget = ''
                    classes = ''
                    timestamp = item.walk_in_updated_at if type=='visits' else item.admissiomn_done_updated_at
                else:
                    location = item.location
                    budget = item.budget
                    classes = item.classes
                    timestamp = item.lead_updated_at
                if item.user:
                    content_type = 'user'
                    if "[" in item.user_phone_number:
                        number = item.user_phone_number[1:-1].split(",")[0] if item.user_phone_number else None
                    else:
                        number = item.user_phone_number.split(",")[0] if item.user_phone_number else None
                elif item.enquiry:
                    content_type = 'enquiry'
                    if "[" in item.user_phone_number:
                        number = item.user_phone_number[1:-1].split(",")[0] if item.user_phone_number else None
                    else:
                        number = item.user_phone_number.split(",")[0] if item.user_phone_number else None

                elif item.call_scheduled_by_parent:
                    content_type = 'Callscheduledbyparent'
                    if "[" in item.user_phone_number:
                        number = item.user_phone_number[1:-1].split(",")[0] if item.user_phone_number else None
                    else:
                        number = item.user_phone_number.split(",")[0] if item.user_phone_number else None
                school = SchoolProfile.objects.get(id=self.request.user.current_school)
                if type == 'leads':
                    viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school,lead=item).count()
                elif type=="admissions":
                    viewed_no_count = 1
                elif type == 'visits':
                    if ViewedParentPhoneNumberBySchool.objects.filter(school=school, lead__user=item.user).exists():
                        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, lead__user=item.user).count()
                    elif ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry__user=item.user).exists():
                        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry__user=item.user).count()
                    else:
                        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, visit=item).count()
                elif type == 'enquiry':
                    viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school,enquiry=item).count()
                elif type == 'parent_called':
                    viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school,parent_called=item).count()

                if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
                    result.append({
                        'id':item.id,
                        'name':item.user_name,
                        'contact_numbers': number,
                        'type':content_type,
                        'location':location,
                        'budget':budget,
                        'classes':classes,
                        'timestamp':timestamp,
                        'viewed': True
                    })
                elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
                    n = number.replace(" ", "").split(",") if number else []
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
                    result.append({
                        'id': item.id,
                        'name': item.user_name,
                        'contact_numbers': hidden_number,
                        'type': content_type,
                        'location': location,
                        'budget': budget,
                        'classes': classes,
                        'timestamp': timestamp,
                        'viewed': False
                    })

        result1 = {}
        result1['count'] =len(result)
        result1['next'] =next_url
        result1['previous'] =prev_url
        result1['results'] =result
        return Response(result1,status=status.HTTP_200_OK)

class SchoolWiseActionUpdateCreateView(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self,request,slug,id,category):
        if category == 'lead' and LeadGenerated.objects.filter(id=id,lead_for__slug=slug).exists():
            lead = LeadGenerated.objects.get(id=id,lead_for__slug=slug)
            return Response({"results":"result"},status=status.HTTP_200_OK)
        elif category == 'visit' and VisitScheduleData.objects.filter(id=id,walk_in_for__slug=slug).exists():
            visit = VisitScheduleData.objects.get(id=id,walk_in_for__slug=slug)
            return Response({"results":"result"},status=status.HTTP_200_OK)
        elif category == 'admissions' and AdmissionDoneData.objects.filter(id=id,admission_done_for__slug=slug).exists():
            admission = AdmissionDoneData.objects.get(id=id,admission_done_for__slug=slug)
            return Response({"results":"result"},status=status.HTTP_200_OK)
        else:
            return Response({"results":"Please Provide Slug/Type"},status=status.HTTP_404_NOT_FOUND)


class SearchByPhoneNumberUserList(APIView):
    permission_classes = (IsExecutiveUser,)
    def get(self,request):
        if self.request.GET.get('phone', None) and len(self.request.GET.get('phone')) ==10:
            all_users_varified = PhoneNumber.objects.filter(number=str(self.request.GET.get('phone')))
            all_address = ParentAddress.objects.filter(phone_no=str(self.request.GET.get('phone')))
            all_parent = ParentProfile.objects.filter(phone=str(self.request.GET.get('phone')))
            all_call_scheduled_by_parent = ParentCallScheduled.objects.filter(phone=str(self.request.GET.get('phone')))
            all_enquiry = SchoolEnquiry.objects.filter(user__isnull=True,phone_no=str(self.request.GET.get('phone')))
            all_reg_enquiry = SchoolEnquiry.objects.filter(user__isnull=False,phone_no=str(self.request.GET.get('phone')))
            all_visit_scheduled = SchoolEnquiry.objects.filter(user__isnull=True,second_number=str(self.request.GET.get('phone')))
            all_visit_scheduled_user = SchoolEnquiry.objects.filter(user__isnull=False,second_number=str(self.request.GET.get('phone')))
            all_users = []
            for item in all_address:
                all_users.append({
                    'name': item.user.name.title(),
                    'id': item.user.id,
                    'type': 'user',
                })
            for item in all_users_varified:
                all_users.append({
                    'name': item.user.name.title(),
                    'id': item.user.id,
                    'type': 'user',
                })
            for item in all_parent:
                all_users.append({
                    'name': item.user.name.title(),
                    'id': item.user.id,
                    'type': 'user',
                })
            for item in all_enquiry:
                all_users.append({
                    'name': item.parent_name.title(),
                    'id': item.id,
                    'type': 'enquiry',
                })
            for item in all_reg_enquiry:
                all_users.append({
                    'name': item.user.name.title(),
                    'id': item.user.id,
                    'type': 'user',
                })
            for item in all_visit_scheduled:
                all_users.append({
                    'name': item.parent_name.title(),
                    'id': item.id,
                    'type': 'enquiry',
                })
            for item in all_visit_scheduled_user:
                all_users.append({
                    'name': item.user.name.title(),
                    'id': item.user.id,
                    'type': 'user',
                })
            for item in all_call_scheduled_by_parent:
                all_users.append({
                    'name': item.name.title(),
                    'id': item.id,
                    'type': 'Callscheduledbyparent',
                })
            new = set()
            new_all_users = []
            for user in all_users:
                t = tuple(user.items())
                if t not in new:
                    new.add(t)
                    new_all_users.append(user)

            result = {}
            result['count'] =len(new_all_users)
            result['next'] =None
            result['previous'] =None
            result['results'] =new_all_users
            return Response({"results":result},status=status.HTTP_200_OK)
        else:
            return Response({"results":'Provide 10 digit number'},status=status.HTTP_400_BAD_REQUEST)

class SchoolActionListView(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self,request):
        category = self.request.GET.get('category', None)
        if category:
            all_actions = SchoolDashboardActionSection.objects.filter(category__name=category.capitalize())
            data = []
            for action in all_actions:
                data.append({
                    'id':action.id,
                    'name':action.name,
                    'slug':action.slug,
                    'datetime':action.requires_datetime,
                })
        else:
            all_actions = SchoolDashboardActionSection.objects.all()
            data = []
            for action in all_actions:
                data.append({
                    'id':action.id,
                    'name':action.name,
                    'slug':action.slug,
                    'datetime':action.requires_datetime,
                })
        return Response({"results":data}, status=status.HTTP_200_OK)

class SchoolCommentSectionCreateRetriveView(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self,request, id,*args, **kwargs):
        type=self.request.GET.get("type", None)
        if LeadGenerated.objects.filter(id=id).exists() and type == 'leads':
            user = User.objects.get(id=self.request.user.id)
            school = SchoolProfile.objects.get(id=user.current_school)
            lead_obj = LeadGenerated.objects.get(id=id)
            comments = SchoolCommentSection.objects.filter(school=school,lead=lead_obj).order_by("-timestamp")
            result = []
            for com in comments:
                result.append({
                'comment':com.comment,
                'timestamp':com.timestamp,
                })
            return Response({"results":result}, status=status.HTTP_200_OK)
        elif VisitScheduleData.objects.filter(id=id).exists() and type == 'visits':
            user = User.objects.get(id=self.request.user.id)
            school = SchoolProfile.objects.get(id=user.current_school)
            visit_obj = VisitScheduleData.objects.get(id=id)
            comments = SchoolCommentSection.objects.filter(school=school,visit=visit_obj).order_by("-timestamp")
            result = []
            for com in comments:
                result.append({
                'comment':com.comment,
                'timestamp':com.timestamp,
                })
            return Response({"results":result}, status=status.HTTP_200_OK)
        elif AdmissionDoneData.objects.filter(id=id).exists() and type == 'admissions':
            user = User.objects.get(id=self.request.user.id)
            school = SchoolProfile.objects.get(id=user.current_school)
            admission_obj = AdmissionDoneData.objects.get(id=id)
            comments = SchoolCommentSection.objects.filter(school=school,admissions=admission_obj).order_by("-timestamp")
            result = []
            for com in comments:
                result.append({
                'comment':com.comment,
                'timestamp':com.timestamp,
                })
            return Response({"results":result}, status=status.HTTP_200_OK)
        elif SchoolEnquiry.objects.filter(id=id,school__id=self.request.user.current_school).exists() and type == 'schoolenquiry':
            comments = SchoolPerformedCommentEnquiry.objects.filter(enquiry__school__id=self.request.user.current_school,enquiry__id=id).order_by("-timestamp")
            result = []
            for com in comments:
                result.append({
                'comment':com.comment,
                'timestamp':com.timestamp,
                })
            return Response({"results":result}, status=status.HTTP_200_OK)
        else:
            return Response({"results":"Provide Valid Type"}, status=status.HTTP_400_BAD_REQUEST)
    def post(self,request, id,*args, **kwargs):
        type=self.request.GET.get("type", None)
        if request.data:
            if LeadGenerated.objects.filter(id=id).exists() and type == 'leads':
                comment = request.data['comment']
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                lead_obj = LeadGenerated.objects.get(id=id)
                new_comment = SchoolCommentSection.objects.create(school=school,lead=lead_obj,comment=comment)
                return Response({"result":"Comment Created"}, status=status.HTTP_200_OK)
            elif VisitScheduleData.objects.filter(id=id).exists() and type == 'visits':
                comment = request.data['comment']
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                visit_obj = VisitScheduleData.objects.get(id=id)
                new_comment = SchoolCommentSection.objects.create(school=school,visit=visit_obj,comment=comment)
                return Response({"result":"Comment Created"}, status=status.HTTP_200_OK)
            elif AdmissionDoneData.objects.filter(id=id).exists() and type == 'admissions':
                comment = request.data['comment']
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                admission_obj = AdmissionDoneData.objects.get(id=id)
                new_comment = SchoolCommentSection.objects.create(school=school,admissions=admission_obj,comment=comment)
                return Response({"result":"Comment Created"}, status=status.HTTP_200_OK)
            elif SchoolEnquiry.objects.filter(id=id,school__id=self.request.user.current_school).exists() and type == 'schoolenquiry':
                comment = request.data['comment']
                enquiry = SchoolEnquiry.objects.get(id=id)
                new_comment = SchoolPerformedCommentEnquiry.objects.create(comment=comment,enquiry=enquiry)
                if enquiry.user:
                    new_comment.user = enquiry.user
                    new_comment.save()
                return Response({"result":"Comment Created"}, status=status.HTTP_200_OK)
            else:
                return Response({"result":"Provide Valid Type"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result":"Provide Payload"}, status=status.HTTP_400_BAD_REQUEST)

class SchoolActionView(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self, request, id, *args, **kwargs):
        type = self.request.GET.get('type', None)
        if id:
            if LeadGenerated.objects.filter(id=id).exists() and type == 'leads':
                lead_obj = LeadGenerated.objects.get(id=id)
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get(lead=lead_obj,school=school)
                final_result=[]
                response={}
                response['action'] = action_data.action.id
                response['action_name'] = action_data.action.name
                response['child_name'] = action_data.admissions.child_name if action_data.admissions else ""
                response['action_updated_at'] = action_data.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                response['action_created_at'] = action_data.action_created_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                if action_data.scheduled_time:
                    response['scheduled_time'] = action_data.scheduled_time.strftime("%a, %d-%b-%Y, %I:%M %p")
                else:
                    response['scheduled_time'] = None
                final_result.append({
                'results':response
                })
                return Response(final_result, status=status.HTTP_200_OK)
            elif VisitScheduleData.objects.filter(id=id).exists() and type == 'visits':
                visit_obj = VisitScheduleData.objects.get(id=id)
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get(visit=visit_obj,school=school)
                final_result=[]
                response={}
                response['action'] = action_data.action.id
                response['action_name'] = action_data.action.name
                response['child_name'] = action_data.admissions.child_name if action_data.admissions else ""
                response['action_updated_at'] = action_data.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                response['action_created_at'] = action_data.action_created_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                if action_data.scheduled_time:
                    response['scheduled_time'] = action_data.scheduled_time.strftime("%a, %d-%b-%Y, %I:%M %p")
                else:
                    response['scheduled_time'] = None
                final_result.append({
                'results':response
                })
                return Response(final_result, status=status.HTTP_200_OK)
            elif AdmissionDoneData.objects.filter(id=id).exists() and type == 'admissions':
                admission_obj = AdmissionDoneData.objects.get(id=id)
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get(admissions=admission_obj,school=school)
                final_result=[]
                response={}
                response['action'] = action_data.action.id
                response['action_name'] = action_data.action.name
                response['child_name'] = action_obj.child_name if action_obj.child_name else ""
                response['action_updated_at'] = action_data.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                response['action_created_at'] = action_data.action_created_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                if action_data.scheduled_time:
                    response['scheduled_time'] = action_data.scheduled_time.strftime("%a, %d-%b-%Y, %I:%M %p")
                else:
                    response['scheduled_time'] = None
                final_result.append({
                'results':response
                })
                return Response(final_result, status=status.HTTP_200_OK)
            elif SchoolPerformedActionOnEnquiry.objects.filter(enquiry__id=id).exists() and type=='schoolenquiry':
                action_obj = SchoolPerformedActionOnEnquiry.objects.get(enquiry__id=id)
                final_result=[]
                response={}
                response['action'] = action_obj.action.id
                response['action_name'] = action_obj.action.name
                response['child_name'] = action_obj.child_name if action_obj.child_name else ""
                response['action_updated_at'] = action_obj.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                response['action_created_at'] = action_obj.action_created_at.strftime("%a, %d-%b-%Y, %I:%M %p")
                if action_obj.scheduled_time:
                    response['scheduled_time'] = action_obj.scheduled_time.strftime("%a, %d-%b-%Y, %I:%M %p")
                else:
                    response['scheduled_time'] = None
                final_result.append({
                'results':response
                })
                return Response(final_result, status=status.HTTP_200_OK)
            else:
                final_result=[]
                response={}
                response['action'] = None
                response['action_created_at'] = None
                response['action_updated_at'] = None
                response['scheduled_time'] = None
                final_result.append({
                'results':response
                })
                return Response(final_result, status=status.HTTP_200_OK)
        else:
            return Response({"results":'ID can not be null'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, id, *args, **kwargs):
        type=self.request.GET.get("type", None)
        if request.data:
            if LeadGenerated.objects.filter(id=id).exists() and type == 'leads':
                lead_obj = LeadGenerated.objects.get(id=id)
                counsellor = lead_obj.counseling_user
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get_or_create(lead=lead_obj,school=school)
                action_obj = SchoolDashboardActionSection.objects.get(id=request.data['action_id'])
                if action_obj.name == 'Visit Scheduled':
                    if lead_obj.user:
                        if VisitScheduleData.objects.filter(user=lead_obj.user,counseling_user__isnull=True).exists():
                            visit_obj = VisitScheduleData.objects.get(user=lead_obj.user,counseling_user__isnull=True)
                        else:
                            visit_obj = VisitScheduleData.objects.create(user=lead_obj.user)
                        visit_obj.user_name=lead_obj.user.name
                        visit_obj.user_email = lead_obj.user.email
                        visit_obj.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(lead_obj.user.id))])
                        visit_obj.save()
                        visit_obj.walk_in_for.add(school)
                        visit_obj.save()
                    elif lead_obj.enquiry:
                        if VisitScheduleData.objects.filter(enquiry=lead_obj.enquiry,counseling_user__isnull=True).exists():
                            visit_obj = VisitScheduleData.objects.get(enquiry=lead_obj.enquiry,counseling_user__isnull=True)
                        else:
                            visit_obj = VisitScheduleData.objects.create(enquiry=lead_obj.enquiry)
                        visit_obj.user_name=lead_obj.enquiry.parent_name
                        visit_obj.user_email = lead_obj.enquiry.email
                        phone_no_list = []
                        if lead_obj.enquiry.phone_no:
                            phone_no_list.append(int(lead_obj.enquiry.phone_no))
                        visit_obj.user_phone_number = phone_no_list
                        visit_obj.save()
                        visit_obj.walk_in_for.add(school)
                        visit_obj.save()
                    elif lead_obj.call_scheduled_by_parent:
                        if VisitScheduleData.objects.filter(call_scheduled_by_parent=lead_obj.call_scheduled_by_parent,
                                                            counseling_user__isnull=True).exists():
                            adm_obj = VisitScheduleData.objects.get(
                                call_scheduled_by_parent=lead_obj.call_scheduled_by_parent,
                                counseling_user__isnull=True)
                        else:
                            adm_obj = VisitScheduleData.objects.create(
                                call_scheduled_by_parent=lead_obj.call_scheduled_by_parent)
                        adm_obj.user_name = lead_obj.call_scheduled_by_parent.name
                        # adm_obj.user_email = visit_obj.enquiry.email
                        phone_no_list = []
                        if lead_obj.call_scheduled_by_parent.phone:
                            phone_no_list.append(int(lead_obj.call_scheduled_by_parent.phone))
                        adm_obj.user_phone_number = phone_no_list
                        adm_obj.save()
                        adm_obj.walk_in_for.add(school)
                        adm_obj.save()

                elif action_obj.name == 'Admission Done':
                    if lead_obj.user:
                        if AdmissionDoneData.objects.filter(user=lead_obj.user,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(user=lead_obj.user,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(user=lead_obj.user)
                        adm_obj.user_name=lead_obj.user.name
                        adm_obj.child_name=request.data.get('child_name', "")
                        adm_obj.user_email = lead_obj.user.email
                        adm_obj.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(lead_obj.user.id))])
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        send_admission_done_mail_to_school_heads(adm_obj.id)
                    elif lead_obj.enquiry:
                        if AdmissionDoneData.objects.filter(enquiry=lead_obj.enquiry,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(enquiry=lead_obj.enquiry,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(enquiry=lead_obj.enquiry)
                        adm_obj.user_name=lead_obj.enquiry.parent_name
                        adm_obj.child_name = request.data.get('child_name', "")
                        adm_obj.user_email = lead_obj.enquiry.email
                        phone_no_list = []
                        if lead_obj.enquiry.phone_no:
                            phone_no_list.append(int(lead_obj.enquiry.phone_no))
                        adm_obj.user_phone_number = phone_no_list
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        adm_obj.save()
                        send_admission_done_mail_to_school_heads(adm_obj.id)
                    elif lead_obj.call_scheduled_by_parent:
                        if AdmissionDoneData.objects.filter(call_scheduled_by_parent=lead_obj.call_scheduled_by_parent,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(call_scheduled_by_parent=lead_obj.call_scheduled_by_parent,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(call_scheduled_by_parent=lead_obj.call_scheduled_by_parent)
                        adm_obj.user_name=lead_obj.call_scheduled_by_parent.name
                        phone_no_list = []
                        if lead_obj.call_scheduled_by_parent.phone:
                            phone_no_list.append(int(lead_obj.call_scheduled_by_parent.phone))
                        adm_obj.user_phone_number = list(set(phone_no_list))
                        adm_obj.child_name = request.data.get('child_name', "")
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        send_admission_done_mail_to_school_heads(adm_obj.id)
            elif VisitScheduleData.objects.filter(id=id).exists() and type == 'visits':
                visit_obj = VisitScheduleData.objects.get(id=id)
                counsellor = visit_obj.counseling_user
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get_or_create(visit=visit_obj,school=school)
                action_obj = SchoolDashboardActionSection.objects.get(id=request.data['action_id'])
                if action_obj.name == 'Admission Done':
                    if visit_obj.user:
                        if AdmissionDoneData.objects.filter(user=visit_obj.user,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(user=visit_obj.user,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(user=visit_obj.user)
                        adm_obj.user_name=visit_obj.user.name
                        adm_obj.user_email = visit_obj.user.email
                        adm_obj.child_name = request.data.get('child_name', "")
                        adm_obj.user_phone_number = ', '.join([str(number) for number in list(get_user_phone_numbers(visit_obj.user.id))])
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        adm_obj.save()
                        send_admission_done_mail_to_school_heads(adm_obj.id)
                    elif visit_obj.enquiry:
                        if AdmissionDoneData.objects.filter(enquiry=visit_obj.enquiry,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(enquiry=visit_obj.enquiry,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(enquiry=visit_obj.enquiry)
                        adm_obj.user_name=visit_obj.enquiry.parent_name
                        adm_obj.user_email = visit_obj.enquiry.email
                        adm_obj.child_name = request.data.get('child_name', "")
                        phone_no_list = []
                        if visit_obj.enquiry.phone_no:
                            phone_no_list.append(int(visit_obj.enquiry.phone_no))
                        adm_obj.user_phone_number = phone_no_list
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        adm_obj.save()
                        send_admission_done_mail_to_school_heads(adm_obj.id)
                    elif visit_obj.call_scheduled_by_parent:
                        if AdmissionDoneData.objects.filter(call_scheduled_by_parent=visit_obj.call_scheduled_by_parent,counseling_user__isnull=True).exists():
                            adm_obj = AdmissionDoneData.objects.get(call_scheduled_by_parent=visit_obj.call_scheduled_by_parent,counseling_user__isnull=True)
                        else:
                            adm_obj = AdmissionDoneData.objects.create(call_scheduled_by_parent=visit_obj.call_scheduled_by_parent)
                        adm_obj.user_name=visit_obj.call_scheduled_by_parent.name
                        adm_obj.child_name = request.data.get('child_name', "")
                        phone_no_list = []
                        if visit_obj.call_scheduled_by_parent.phone:
                            phone_no_list.append(int(visit_obj.call_scheduled_by_parent.phone))
                        adm_obj.user_phone_number = phone_no_list
                        adm_obj.save()
                        adm_obj.admission_done_for.add(school)
                        send_admission_done_mail_to_school_heads(adm_obj.id)
            elif AdmissionDoneData.objects.filter(id=id).exists() and type == 'admissions':
                admission_obj = AdmissionDoneData.objects.get(id=id)
                counsellor = admission_obj.counseling_user
                user = User.objects.get(id=self.request.user.id)
                school = SchoolProfile.objects.get(id=user.current_school)
                action_data = SchoolAction.objects.get_or_create(admissions=admission_obj,school=school)
                action_obj = SchoolDashboardActionSection.objects.get(id=request.data['action_id'])

            elif SchoolEnquiry.objects.filter(id=id, school__id=self.request.user.current_school).exists() and type=='schoolenquiry':
                enquiry_obj = SchoolEnquiry.objects.get(id=id,school__id=self.request.user.current_school)
                action_data = SchoolPerformedActionOnEnquiry.objects.get_or_create(enquiry=enquiry_obj)
                action_obj = SchoolDashboardActionSection.objects.get(id=request.data['action_id'])

            else:
                return Response({"result":"Provide Valid Type"}, status=status.HTTP_400_BAD_REQUEST)
            action_data=action_data[0]
            action_data.scheduled_time = None
            action_data.action = action_obj
            if not type=='schoolenquiry':
                action_data.counsellor = counsellor
            else:
                if enquiry_obj.user:
                    action_data.user = enquiry_obj.user
                    action_data.save()
                if action_obj.name == 'Admission Done':
                    action_data.child_name = request.data.get('child_name', "")
                    action_data.save()
                    send_admission_done_mail_to_school_heads_from_school_dashboard(action_data.id)
            action_data.save()
            if request.data.get('scheduled_time') and request.data.get('scheduled_date') and request.data.get("scheduled_time") != None and request.data.get('scheduled_date') !=None:
                scheduled_Datetime = request.data.get('scheduled_date')+' '+request.data.get('scheduled_time')
                scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                scheduled_Datetime = make_aware(scheduled_Datetime)
                action_data.scheduled_time = scheduled_Datetime
                action_data.save()
            elif request.data.get('scheduled_date') and request.data.get('scheduled_time') ==None:
                scheduled_Datetime = request.data.get('scheduled_date')+' 00:00:01'
                scheduled_Datetime = datetime.strptime(scheduled_Datetime, '%Y-%m-%d %X')
                scheduled_Datetime = make_aware(scheduled_Datetime)
                action_data.scheduled_time = scheduled_Datetime
                action_data.save()
            else:
                pass
            return Response({"results":"Action Creation/Updation Completed"}, status=status.HTTP_200_OK)
        else:
            return Response({"result":"Prove Payload"}, status=status.HTTP_400_BAD_REQUEST)

class SchoolPastDataList(APIView):
    permission_classes = (SchoolCounsellingDataPermission,)
    def get(self,request,slug,type):
        start_offset = 0
        end_offset = 10
        next_url = None
        prev_url = None
        offset = int(self.request.GET.get('offset', 10))
        if offset ==10:
            new_offset = offset*2
            next_url = f"api/v2/admin_custom/school/{slug}/{type}/past-list/?offset={str(new_offset)}"
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-10
            end_offset = offset
            new_next_offset = offset +10
            new_prev_offset = offset - 10
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = f"api/v2/admin_custom/school/{slug}/{type}/past-list/?offset={str(new_next_offset)}"
            prev_url = f"api/v2/admin_custom/school/{slug}/{type}/past-list/?offset={str(new_prev_offset)}"
        new_data = []
        if type == 'leads' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = SchoolAction.objects.filter(school__slug=slug,visit__isnull=True,admissions__isnull=True).exclude(Q(action__name='Admission Done') | Q(action__name='Visit Scheduled')).order_by("-action_updated_at")[start_offset:end_offset]
        elif type == 'visits' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = SchoolAction.objects.filter(school__slug=slug,lead__isnull=True,admissions__isnull=True).exclude(action__name='Admission Done').order_by("-action_updated_at")[start_offset:end_offset]
            other_data = SchoolAction.objects.filter(school__slug=slug,visit__isnull=True,counsellor__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            for item in other_data:
                if item.action.name == 'Visit Scheduled':
                    new_data.append(item)
        elif type == 'admissions' and SchoolProfile.objects.filter(slug=slug).exists():
            total_data = SchoolAction.objects.filter(school__slug=slug,lead__isnull=True,visit__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            other_data = SchoolAction.objects.filter(school__slug=slug,admissions__isnull=True,counsellor__isnull=True).order_by("-action_updated_at")[start_offset:end_offset]
            for item in other_data:
                if item.action.name == 'Admission Done':
                    new_data.append(item)
        else:
            return Response({"results":"Please Provide Slug/Type"},status=status.HTTP_404_NOT_FOUND)
        data_list = list(chain(total_data, new_data))
        return_result = getAllList(data_list, type, self.request.user.current_school)
        result = {}
        result['count'] =len(return_result)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =return_result
        return Response(result,status=status.HTTP_200_OK)

class SchoolDashboardEnquiryList(APIView):
    def get(self,request):
        start_offset = 0
        end_offset = 25
        next_url = None
        prev_url = None
        offset = int(self.request.GET.get('offset', 25))
        if offset ==25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/school-enquiry-list/?offset=' +str(new_offset)
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/school-enquiry-list/?offset=' +str(new_next_offset)
            prev_url = 'api/v2/admin_custom/school-enquiry-list/?offset=' +str(new_prev_offset)
        past_data = SchoolPerformedActionOnEnquiry.objects.filter(enquiry__school__id=self.request.user.current_school).values("enquiry__id")
        queryset= SchoolEnquiry.objects.filter(school__id=self.request.user.current_school).exclude(id__in=[sub['enquiry__id'] for sub in past_data]).order_by("-timestamp")[start_offset:end_offset]
        data = []
        school = SchoolProfile.objects.get(id=self.request.user.current_school)
        for item in queryset:
            viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, enquiry=item).count()
            if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
                data.append({
                    'id':item.id,
                    'name':item.parent_name,
                    'phone': item.phone_no,
                    'email':item.email,
                    'class':item.class_relation.name if item.class_relation else 'N/A',
                    'query':item.query,
                    'timestamp':item.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    'viewed': True
                })
            elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
                n = item.phone_no.replace(" ", "").split(",") if item.phone_no else []
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
                data.append({
                    'id': item.id,
                    'name': item.parent_name,
                    'phone': hidden_number,
                    'email': item.email,
                    'class': item.class_relation.name if item.class_relation else 'N/A',
                    'query': item.query,
                    'timestamp': item.timestamp.strftime("%a, %d-%b-%Y, %I:%M %p"),
                    'viewed':False,
                })
        result = {}
        result['count'] =len(data)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =data
        result['enquiries_count'] = data
        return Response(result,status=status.HTTP_200_OK)

class SchoolDashboardPastEnquiryList(APIView):
    def get(self,request):
        start_offset = 0
        end_offset = 25
        next_url = None
        prev_url = None
        offset = int(self.request.GET.get('offset', 25))
        if offset ==25:
            new_offset = offset*2
            next_url = 'api/v2/admin_custom/school-past-enquiry-list/?offset=' +str(new_offset)
            prev_url = None
        else:
            # start_offset = offset
            # end_offset = end_offset+offset
            # new_next_offset = start_offset + 25
            # new_prev_offset = start_offset - 25
            start_offset = offset-25
            end_offset = offset
            new_next_offset = offset +25
            new_prev_offset = offset - 25
            if new_prev_offset == 0:
                new_prev_offset = ''
            next_url = 'api/v2/admin_custom/school-past-enquiry-list/?offset=' +str(new_next_offset)
            prev_url = 'api/v2/admin_custom/school-past-enquiry-list/?offset=' +str(new_prev_offset)
        queryset= SchoolPerformedActionOnEnquiry.objects.filter(enquiry__school__id=self.request.user.current_school).order_by("-action_updated_at")[start_offset:end_offset]
        data = []
        school = SchoolProfile.objects.get(id=self.request.user.current_school)
        for item in queryset:
            viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school).filter(Q(school_performed_action_on_enquiry=item) | Q(enquiry=item.enquiry)).count()
            if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
                if item.action.name != 'Not Interested':
                    data.append({
                        'id':item.enquiry.id,
                        'name':item.enquiry.parent_name,
                        'phone': item.enquiry.phone_no,
                        'email':item.enquiry.email,
                        'class':item.enquiry.class_relation.name if item.enquiry.class_relation else 'NA',
                        'query':item.enquiry.query,
                        'timestamp':item.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p"),
                        'viewed': True
                    })
            elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
                n = item.enquiry.phone_no.replace(" ", "").split(",") if item.enquiry.phone_no else []
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
                if item.action.name != 'Not Interested':
                    data.append({
                        'id':item.enquiry.id,
                        'name':item.enquiry.parent_name,
                        'phone': hidden_number,
                        'email':item.enquiry.email,
                        'class':item.enquiry.class_relation.name if item.enquiry.class_relation else 'NA',
                        'query':item.enquiry.query,
                        'timestamp':item.action_updated_at.strftime("%a, %d-%b-%Y, %I:%M %p"),
                        'viewed': False
                    })
        result = {}
        result['count'] =len(data)
        result['next'] =next_url
        result['previous'] =prev_url
        result['results'] =data
        return Response(result,status=status.HTTP_200_OK)


class ParentCallScheduledView(APIView):

    def post(self, request, *args, **kwargs):
        data = self.request.data
        user = request.user if request.user else None
        current_time = [{"id": '10', "val": '10'}, {"id": '11', "val": '11'}, {"id": '12', "val": '12'},
                        {"id": '01', "val": '13'}, {"id": '02', "val": '14'}, {"id": '03', "val": '15'},
                        {"id": '04', "val": '16'}, {"id": '05', "val": '17'}, {"id": '06', "val": '18'}]
        result_datetime = data["time_slot"].split(" ")
        result_datetime = result_datetime[0]+" "+result_datetime[1]
        timeslot = datetime.strptime(result_datetime, '%Y-%m-%d %H:%M:%S')
        new_time = timeslot.astimezone(pytz.timezone('Asia/Calcutta'))
        for c_time in current_time:
            if c_time['id'] == str(new_time).split(" ")[1].split(":")[0]:
                new_time = str(new_time).split(" ")[0] + " " + c_time['val'] + ":" + \
                           str(new_time).split(" ")[1].split(":")[1] + ":" + str(new_time).split(" ")[1].split(":")[
                               2] + ":" + str(new_time).split(" ")[1].split(":")[3]
                data["time_slot"] = new_time.split("+")[0]
                serializer = ParentCallScheduledSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                result = serializer.save(validated_data=data, user=user)
                parent_obj = ParentCallScheduled.objects.get(id=result)
                serializer = ParentCallScheduledSerializer(parent_obj)
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )

    def get(self, request, *args, **kwargs):
        try:
            try:
                parent_id = self.kwargs["id"]
                if ParentCallScheduled.objects.filter(
                        id=parent_id,
                ).exists():
                    blog = ParentCallScheduled.objects.get(
                        id=parent_id,
                    )
                    serializer = ParentCallScheduledSerializer(blog)
                    return Response(serializer.data)
                else:
                    return Response(
                        data={"message": "Details Not Found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except:
                parent_objs = ParentCallScheduled.objects.filter().order_by(
                    '-timestamp')
                serializer = ParentCallScheduledSerializer(parent_objs, many=True)
                return Response(serializer.data)
        except Exception as e:
            return Response(
                data={"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GetCounsellorCityListView(APIView):
    permission_classes = (IsExecutiveUser,)

    def get(self, request):
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
        city_obj = [{"id":city.id, "name":city.name} for city in counselor_obj.city.filter() if counselor_obj.city]
        district_obj = [{"id":district.city.id, "name":district.city.name} for district in counselor_obj.district.filter() if counselor_obj.district]
        district_region_obj = [{"id":district_region.city.id, "name":district_region.city.name} for district_region in counselor_obj.district_region.filter() if counselor_obj.district_region]
        online_obj = [{"id":online.id, "name":online.name} for online in City.objects.filter(slug="online-schools") if counselor_obj.online_schools]
        boarding_obj = [{"id":boarding.id, "name":boarding.name} for boarding in City.objects.filter(slug="boarding-schools") if counselor_obj.boarding_schools]
        res = city_obj + district_obj + district_region_obj + online_obj + boarding_obj
        res = list({v['id']:v for v in res}.values())
        return Response(res)


class TimeSlotView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        date_str = request.query_params.get("date")
        city = request.query_params.get("city")
        # date_time_str = '2022-05-20'
        date_time = datetime.strptime(date_str, '%Y-%m-%d')
        if date_time.isoweekday() == 7:
            return Response({"res":["No slots available on sunday."]})
        if date_time.day in weekendDays(date_time.year,date_time.month):
            return Response({"res":["No slots available today."]})
        city = City.objects.filter(id=city).first()
        parent_call_sche_timeslot = [str(parent_date.time_slot.astimezone(pytz.timezone('Asia/Calcutta')).time()) for parent_date in ParentCallScheduled.objects.filter(time_slot__date=date_time)]
        HOUR_LIST = ['10', '11', '12', '01', '02', '03', '04', '05', '06']
        current_time = [{"id":'10',"val":'10'}, {"id":'11',"val":'11'},{"id":'12',"val":'12'},{"id":'01',"val":'13'},{"id":'02',"val":'14'},{"id":'03',"val":'15'},
                        {"id":'04',"val":'16'},{"id":'05',"val":'17'},{"id":'06',"val":'18'}]
        MINUTE_LIST = [
            '00:00',
            '15:00',
            '30:00',
            '45:00',
        ]
        res = [hour+":"+minutes for hour in HOUR_LIST for minutes in MINUTE_LIST]
        for result in res[2:-3]:
            result_datetime = date_str + " " + result
            timeslot = datetime.strptime(result_datetime, '%Y-%m-%d %H:%M:%S')
            new_time = timeslot.astimezone(pytz.timezone('Asia/Calcutta'))
            for c_time in current_time:
                if c_time['id'] == str(new_time).split(" ")[1].split(":")[0]:
                    new_time = str(new_time).split(" ")[0]+" "+c_time['val']+":"+str(new_time).split(" ")[1].split(":")[1]+":"+str(new_time).split(" ")[1].split(":")[2]+":"+str(new_time).split(" ")[1].split(":")[3]
                    if ParentCallScheduled.objects.filter(time_slot=new_time, city=city).exists():
                        parent_count = ParentCallScheduled.objects.filter(time_slot=new_time, city=city).count()
                        counsellor_count = CounselorCAdminUser.objects.filter(city__in=[city]).count()
                        if parent_count == counsellor_count:
                            res.remove(result)
        for result in res[2:-3]:
            result_datetime = date_str + " " + result
            timeslot = datetime.strptime(result_datetime, '%Y-%m-%d %H:%M:%S')
            if timeslot.date() == date.today():
                if timeslot < datetime.now():
                    res.remove(result)
        new_res=[]
        for result in res[2:-3]:
            if str(result).split(":")[0] == '12':
                new_res.append(result + " PM")
            elif str(result).split(":")[0].startswith("0"):
                new_res.append(result + " PM")
            else:
                new_res.append(result + " AM")
        results = {
            "res":new_res if new_res else ["No slots available."],
            # "parent_call_sche_timeslot": parent_call_sche_timeslot,
        }
        return Response(results)

class DatabaseInsideSchoolsListView(ListCreateAPIView):
    serializer_class = SchoolProfileInsideSerializer
    permission_classes = (IsDatabaseAdminUser,)
    queryset = SchoolProfile.objects.filter(is_active=True).order_by("-id")
    search_fields = ("name",)
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    filterset_fields = [
        "collab",
        "is_verified",
        "is_featured",
        "school_city__id",
        "school_state__id",
        "district__id",
        "district_region__id"
        ]


class GetAllSchoolsDetailCountView(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def get(self, request):
        # cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        # db_user_obj = DatabaseCAdminUser.objects.get(user=cadmin_user_obj)
        all_school = SchoolProfile.objects.filter(is_active=True).count()
        all_collab_school = SchoolProfile.objects.filter(is_active=True, collab=True).count()
        all_verified_school = SchoolProfile.objects.filter(is_active=True, is_verified=True).count()
        all_non_verified_school = SchoolProfile.objects.filter(is_active=True, is_verified=False).count()
        all_featured_school = SchoolProfile.objects.filter(is_active=True, is_featured=True).count()
        currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
        all_school_admission_open = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=True) if AdmmissionOpenClasses.objects.filter(school=sch_obj).filter(Q(session=currentSession) | Q(session=nextSession))])
        all_collab_school_no_fees = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=True) if not FeeStructure.objects.filter(school=sch_obj).filter(Q(session=currentSession) | Q(session=nextSession))])
        all_collab_school_no_facilities = len([sch_obj for sch_obj in SchoolProfile.objects.filter(is_active=True, collab=True) if not Feature.objects.filter(school=sch_obj)])
        result = {
            "all_schools":all_school,
            "all_collab_school":all_collab_school,
            "all_verified_school":all_verified_school,
            "all_non_verified_school":all_non_verified_school,
            "all_featured_school":all_featured_school,
            "all_collab_school_no_fees":all_collab_school_no_fees,
            "all_collab_school_no_facilities":all_collab_school_no_facilities,
            "all_school_admission_open":all_school_admission_open,
        }
        return Response(result)


class GetAllCitywiseSchoolsDetailCountView(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def get(self, request):
        # cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=self.request.user.id)
        # db_user_obj = DatabaseCAdminUser.objects.get(user=cadmin_user_obj)
        cities = [city for city in City.objects.filter()]
        res = []
        for city in cities:
            all_school = SchoolProfile.objects.filter(is_active=True, school_city=city).count()
            res.append({"city":city.name, "count": all_school})

        return Response(res, status=status.HTTP_200_OK)


class DatabaseAdmissionOpenClassesView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    serializer_class = serializers.DatabaseAdmmissionOpenClassesSerializer
    permission_classes = [HasSchoolChildModelPermissionOrReadOnly]
    filterset_class = AdmissionOpenClassesFilter

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = AdmmissionOpenClasses.objects.filter(school=school)
        return queryset


class DatabaseAdmissionOpenClassesDetailView(SchoolPerformCreateUpdateMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.DatabaseAdmmissionOpenClassesSerializer
    lookup_field = "pk"

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = AdmmissionOpenClasses.objects.filter(school=school)
        return queryset

class DatabaseSchoolAdmissionFormFeeCreateView(APIView):
    serializer_class = serializers.DatabaseSchoolAdmissionFormFeeSerializer

    def post(self,request,slug,format=None):
        serializer = serializers.DatabaseSchoolAdmissionFormFeeSerializer(data=request.data)
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



class DatabaseSearchView(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        admission_open_no_class = request.query_params.get("admission_open_no_class")
        avg_cal_fee_zero = request.query_params.get("avg_cal_fee_zero")
        admission_open_no_form_fee = request.query_params.get("admission_open_no_form_fee")
        location_blank = request.query_params.get("location_blank")
        no_fee_structure = request.query_params.get("no_fee_structure")
        low_facilities = request.query_params.get("low_facilities")

        writer = csv.writer(response)

        if admission_open_no_form_fee:
            response['Content-Disposition'] = 'attachment; filename="admission_open_no_form_fee.csv"'

            writer.writerow(
                ['ID', 'School ID', 'School Slug', 'School Name', 'Collab', 'Class Relation ID', 'Class Relation Name', 'Form Price', 'Convenience Fee'])
            result = []
            # result = [writer.writerow([sch_obj.id,sch_obj.school_relation.id, sch_obj.school_relation.slug, sch_obj.school_relation.name, sch_obj.school_relation.collab,sch_obj.class_relation.id,sch_obj.class_relation.name,sch_obj.form_price])
            #           for sch in SchoolProfile.objects.filter(is_active=True) for sch_cls in sch.class_relation.filter()
            #           for obj in AdmmissionOpenClasses.objects.filter(school=sch).filter(class_relation=sch_cls, admission_open='OPEN')
            #           for sch_obj in SchoolAdmissionFormFee.objects.filter(class_relation=sch_cls,school_relation=sch).filter(Q(form_price__isnull=True)|Q(form_price=0)) ]
            for sch in SchoolProfile.objects.filter(is_active=True, is_verified=True):
                for sch_cls in sch.class_relation.filter():
                    if AdmmissionOpenClasses.objects.filter(school=sch).filter(class_relation=sch_cls, admission_open='OPEN').exists():
                        if SchoolAdmissionFormFee.objects.filter(class_relation=sch_cls, school_relation=sch).exists():
                            sch_obj = SchoolAdmissionFormFee.objects.filter(class_relation=sch_cls, school_relation=sch)
                            for sch_adm_form_fee in sch_obj:
                                if ((sch_adm_form_fee.form_price == 0 or sch_adm_form_fee.form_price is None) and sch_adm_form_fee.school_relation.convenience_fee == 0 or sch_adm_form_fee.school_relation.convenience_fee is None) or sch_adm_form_fee.form_price == 0 or sch_adm_form_fee.form_price is None:
                                    result = [writer.writerow(
                                        [sch_adm_form_fee.id, sch_adm_form_fee.school_relation.id, sch_adm_form_fee.school_relation.slug,
                                         sch_adm_form_fee.school_relation.name, sch_adm_form_fee.school_relation.collab,
                                         sch_adm_form_fee.class_relation.id, sch_adm_form_fee.class_relation.name, sch_adm_form_fee.form_price, sch_adm_form_fee.school_relation.convenience_fee])]
            if result:
                return response
            else:
                return Response({"status": "No Data Found"}, status=status.HTTP_200_OK)
        elif avg_cal_fee_zero:
            response['Content-Disposition'] = 'attachment; filename="avg_cal_fee_zero.csv"'

            writer.writerow(
                ['School ID', 'School Slug', 'School Name', 'Collab', 'Average Fee', 'Calculated Average Fee'])

            result = [writer.writerow([sch_obj.id,sch_obj.slug, sch_obj.name, sch_obj.collab, sch_obj.avg_fee, sch_obj.calculated_avg_fee]) for sch_obj in SchoolProfile.objects.filter(is_active=True, is_verified=True).filter(Q(Q(calculated_avg_fee__isnull=True) | Q(calculated_avg_fee="")), Q(Q(avg_fee__isnull=True) | Q(avg_fee=0)))]
            return response
        elif no_fee_structure:
            response['Content-Disposition'] = 'attachment; filename="no_fee_structure.csv"'

            writer.writerow(
                ['School ID', 'School Slug', 'School Name', 'Collab', 'Fee Price', 'School City ID', 'School City Name'])

            result = [writer.writerow([sch_obj.id,sch_obj.slug,sch_obj.name,sch_obj.collab,sch_obj.fee_price, sch_obj.school_city.id if sch_obj.school_city else None, sch_obj.school_city.name if sch_obj.school_city else None]) for sch_obj in SchoolProfile.objects.filter(is_active=True, is_verified=True) if not FeeStructure.objects.filter(active=True, school=sch_obj, class_relation__isnull=False)]
            if result:
                return response
            else:
                return Response({"status": "No Data Found"}, status=status.HTTP_200_OK)
        elif low_facilities:
            response['Content-Disposition'] = 'attachment; filename="low_facilities.csv"'

            writer.writerow(
                ['School ID', 'School Slug', 'School Name', 'Collab', 'School City ID', 'School City Name'])
            result = []
            # result = [writer.writerow([sch_obj.id, sch_obj.slug, sch_obj.name, sch_obj.collab, sch_obj.school_city.id if sch_obj.school_city else None, sch_obj.school_city.name if sch_obj.school_city else None]) for sch_obj in SchoolProfile.objects.filter(is_active=True) if Feature.objects.filter(school=sch_obj, exist="Undefined").filter(features__lt=20)]
            for sch_obj in SchoolProfile.objects.filter(is_active=True, is_verified=True):
                count = 0
                if Feature.objects.filter(school=sch_obj).exists():
                    obj = Feature.objects.filter(school=sch_obj)
                    for fee_obj in obj:
                        if fee_obj.exist == "Undefined":
                            count = count+1
                if count > 20:
                    result = [writer.writerow([sch_obj.id, sch_obj.slug, sch_obj.name, sch_obj.collab, sch_obj.school_city.id if sch_obj.school_city else None, sch_obj.school_city.name if sch_obj.school_city else None])]
            if result:
                return response
            else:
                return Response({"status": "No Data Found"}, status=status.HTTP_200_OK)
        elif admission_open_no_class:
            response['Content-Disposition'] = 'attachment; filename="admission_open_no_class.csv"'

            writer.writerow(
                ['ID', 'School Name', 'School Slug', 'Collab', 'District Region', 'District',
                 'City'])

            currentSession, nextSession = AdmissionSession.objects.all().order_by('-id')[:2][1], AdmissionSession.objects.all().order_by('-id')[:2][0]
            all_schools = list(AdmmissionOpenClasses.objects.filter(school__collab=True,session__in=[currentSession,nextSession]).values("school__id"))
            new = set()
            new_all_schools = []
            for school in all_schools:
                t = tuple(school.items())
                if t not in new:
                    new.add(t)
                    new_all_schools.append(school)
            school_list = []
            for school in new_all_schools:
                prof = SchoolProfile.objects.get(id=school['school__id'])
                if len(prof.class_relation.all()) == 0:
                    school_list.append({
                        'id': prof.id,
                        'name' : prof.name,
                        'slug' : prof.slug,
                        'collab' : prof.collab,
                        'district_region': prof.district_region.name,
                        'district': prof.district.name,
                        'city': prof.school_city.name,
                    })

            result = [writer.writerow([item['id'],item['name'],item['slug'],item['collab'],item['district_region'],item['district'],item['city']]) for item in school_list]

            if result:
                return response
            else:
                return Response({"status": "No Data Found"}, status=status.HTTP_200_OK)

        elif location_blank:
            response['Content-Disposition'] = 'attachment; filename="location_blank.csv"'

            writer.writerow(['School ID', 'School Slug', 'School Name', 'Collab','District ID', 'District Name','District Region ID', 'District Region Name','City ID', 'City Name','State ID', 'State Name','Country ID', 'Country Name','Short Address', 'Street Address'])

            result = [writer.writerow([sch_obj.id,sch_obj.slug,sch_obj.name,sch_obj.collab, sch_obj.district.id if sch_obj.district else None, sch_obj.district.name if sch_obj.district else None, sch_obj.district_region.id if sch_obj.district_region else None, sch_obj.district_region.name if sch_obj.district_region else None, sch_obj.school_city.id if sch_obj.school_city else None, sch_obj.school_city.name if sch_obj.school_city else None, sch_obj.school_state.id if sch_obj.school_state else None, sch_obj.school_state.name if sch_obj.school_state else None, sch_obj.school_country.id if sch_obj.school_country else None, sch_obj.school_country.name if sch_obj.school_country else None, sch_obj.short_address, sch_obj.street_address]) for sch_obj in SchoolProfile.objects.filter(Q(district__isnull=True) | Q(district_region__isnull=True) | Q(school_city__isnull=True)| Q(school_state__isnull=True) | Q(school_country__isnull=True) | Q(short_address__isnull=True) | Q(short_address="") | Q(street_address__isnull=True) | Q(street_address=""))]
            if result:
                return response
            else:
                return Response({"status": "No Data Found"}, status=status.HTTP_200_OK)
        else:
            return None


class UploadDataForSchoolProfileView(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def post(self, request):
        csv_file = request.FILES['file']
        type = request.data['type']
        try:
            data = csv_file.read().decode('UTF-8')
        except:
            data = csv_file.read().decode('cp1252')
        io_string = io.StringIO(data)
        import pandas as pd
        data = pd.read_csv(io_string)
        user_obj = {"name": self.request.user.name, "email": self.request.user.email}
        if type == "fee_structure":
            # ---------------------------Uploading fees---------------------------------------
            try:
                if len(data) < 150:
                    lst = [row.to_dict() for index, row in data.iterrows()]
                    lines = [
                        f"{csv_file.name} is in process, it takes time to complete the task. We will inform you via mail once it gets completed. - {str(datetime.now())} - Running"]
                    with open('on_process.txt', 'a+') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    upload_school_fee_structure.delay(lst, user_obj, lines[0])
                else:
                    return Response("Only 150 data can be uploaded at a time.",
                            status=status.HTTP_400_BAD_REQUEST)
                return Response("Data will be upload in the background, we will mail you once its get completed.", status=status.HTTP_200_OK)


            except Exception as e:
                message = f"The request is not valid. {str(e)}"

                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif type == "school_profile":
            # ---------------------SchoolProfile---------------------------
            try:
                if len(data) < 50:
                    lst = [row.to_dict() for index, row in data.iterrows()]
                    lines = [
                        f"{csv_file.name} is in process, it takes time to complete the task. We will inform you via mail once it gets completed. - {str(datetime.now())} - Running"]
                    with open('on_process.txt', 'a+') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    upload_school_profiles.delay(lst, user_obj, lines[0])
                else:
                    return Response("Only 50 data can be uploaded at a time.", status=status.HTTP_400_BAD_REQUEST)
                return Response("Data will be upload in the background, we will mail you once its get completed.", status=status.HTTP_200_OK)
            except Exception as e:
                message = f"The request is not valid. {str(e)}"
                # explanation = "The server could not accept your request because it was not valid. Please try again and if the error keeps happening get in contact with us."

                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif type == "facilities":
            # ---------------------SchoolFacilities---------------------------
            try:
                if len(data) < 150:
                    lst = [row.to_dict() for index, row in data.iterrows()]
                    lines = [
                        f"{csv_file.name} is in process, it takes time to complete the task. We will inform you via mail once it gets completed. - {str(datetime.now())} - Running"]
                    with open('on_process.txt', 'a+') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    upload_school_facilities.delay(lst, user_obj, lines[0])

                else:
                    return Response("Only 150 data can be uploaded at a time.",
                                                status=status.HTTP_400_BAD_REQUEST)

                return Response("Data will be upload in the background, we will mail you once its get completed.", status=status.HTTP_200_OK)
            except Exception as e:
                message = f"The request is not valid. {str(e)}"

                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif type == "district_region":
            # ---------------------SchoolDistrictRegion---------------------------
            try:
                if len(data) < 50:
                    lst = [row.to_dict() for index, row in data.iterrows()]
                    lines = [
                        f"{csv_file.name} is in process, it takes time to complete the task. We will inform you via mail once it gets completed. - {str(datetime.now())} - Running"]
                    with open('on_process.txt', 'a+') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    upload_district_region.delay(lst, user_obj, lines[0])


                else:
                    return Response("Only 50 data can be uploaded at a time.",
                            status=status.HTTP_400_BAD_REQUEST)
                return Response("Data will be upload in the background, we will mail you once its get completed.", status=status.HTTP_200_OK)
            except Exception as e:
                message = f"The request is not valid. {str(e)}"

                return Response(
                    message,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            message = f"The request is not valid. Please provide a valid type."
            return Response(
                message,
                status=status.HTTP_400_BAD_REQUEST,
            )

class DatabaseSchoolRegisterView(RegisterView):
    serializer_class = serializers.DatabaseSchoolRegisterSerializer

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


class Response404And500View(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def get(self, request):
        generate = request.query_params.get("generate", "no")
        file_name = "get_404_500_api_responses.csv"
        if generate == "yes":
            user_obj = {"name": self.request.user.name, "email": self.request.user.email}
            current_date_time = str(datetime.now())
            new_link = get_404_500_api_responses.delay(user_obj, current_date_time, file_name)
            if new_link == "0":
                return Response(
                    "All Good, There's no 404 or 500 response in the school profile API.",
                    status=status.HTTP_200_OK)
            else:
                for root, dirs, files in os.walk(f'{settings.MEDIA_ROOT}/'):
                    if file_name in files:
                        os.remove(os.path.join(root, file_name))
                return Response("Data will be downloading in the background, it will take 1-2 days to the complete the process. We will mail you once it gets completed.",
                                status=status.HTTP_200_OK)
        if generate == "no":
            for root, dirs, files in os.walk(f'{settings.MEDIA_ROOT}/'):
                if not file_name in files:
                    return Response({"msg": "No new file found."}, status=status.HTTP_200_OK)
                else:
                    return Response({"link": f"https://ezyschooling-1.s3.amazonaws.com/{file_name}"}, status=status.HTTP_200_OK)

class UploadDataProgressStatusView(APIView):
    permission_classes = (IsDatabaseAdminUser,)

    def get(self, request):
        with open("on_process.txt", "r") as f:
            lines = f.readlines()
        with open("on_process.txt", "w") as f:
            for l in lines:
                if not datetime.strptime(l.split(" - ")[-2].split(" ")[0], "%Y-%m-%d").date() < datetime.today().date():
                    f.write(l)
        return Response({"results":lines}, status=status.HTTP_200_OK)


class DatabaseSchoolFeatureApiView(APIView):
    serializer_class = SchoolFeaturesSerializer

    def get(self, request, slug, format=None):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        queryset = Feature.objects.filter(school=school).order_by("features__parent__id")
        serializer = SchoolFeaturesSerializer(queryset ,many=True)
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
        serializer = SchoolFeaturesSerializer(queryset ,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


class DatabaseFeeStructureView(SchoolPerformCreateUpdateMixin, generics.ListCreateAPIView):
    permission_classes = [IsDatabaseAdminUser, ]
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
            return FeeStructureSerializer
        if self.request.method == "POST":
            return FeeStructureCreateUpdateSeirializer


class CounselorListView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        result = {}
        user = self.request.user if self.request.user else None
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=user.id)
        counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
        if CounselorCAdminUser.objects.filter(user__user_type__category_name='Counselor', user__is_executive=True).exclude(id=counselor_obj.id).exists():
            couns = CounselorCAdminUser.objects.filter(user__user_type__category_name='Counselor', user__is_executive=True).exclude(id=counselor_obj.id)
            serializer = serializers.CounselorUserListSerializer(couns, many=True)
            result["results"] = serializer.data
            return Response(result, status=status.HTTP_200_OK)
        else:
            result["results"] = " User Not found"
            return Response(result, status=status.HTTP_200_OK)

def get_all_shared_data(self, request, type, additional_offset):
    result = {}
    user = self.request.user if self.request.user else None
    cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=user.id)
    counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
    couns_action_from = request.query_params.get("couns_action_from", '')
    couns_action_to = request.query_params.get("couns_action_to", '')
    shared_transfer_from = request.query_params.get("shared_transfer_from", '')
    shared_transfer_to = request.query_params.get("shared_transfer_to", '')
    all_users = []

    if couns_action_from == '' and couns_action_to == '':
        couns_action_from = datetime.strptime('2000-01-01', "%Y-%m-%d").date()
        couns_action_to = datetime.now().date()
    if shared_transfer_from == '' and shared_transfer_to == '':
        shared_transfer_from = datetime.strptime('2000-01-01', "%Y-%m-%d").date()
        shared_transfer_to = datetime.now().date()
    start_offset = 0
    end_offset = 25
    next_url = None
    prev_url = None
    offset = int(self.request.GET.get('offset', 25))
    if additional_offset:
        offset = additional_offset

    res = []
    if type == "all":
        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], call_scheduled_by_parent__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], call_scheduled_by_parent__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False,call_scheduled_by_parent=item.call_scheduled_by_parent,action_updated_at__date__range=(couns_action_from, couns_action_to)).order_by("-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'Callscheduledbyparent'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'Callscheduledbyparent'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj, call_scheduled_by_parent__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj, call_scheduled_by_parent__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id, call_scheduled_by_parent=item.call_scheduled_by_parent,action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action["current_counsellor_id"]:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'Callscheduledbyparent'
                    })

        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], enquiry__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], enquiry__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False, enquiry_data=item.enquiry, action_updated_at__date__range=(couns_action_from, couns_action_to)).order_by("-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'enquiry'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'enquiry'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj, enquiry__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj, enquiry__isnull=False,timestamp__date__range=(shared_transfer_from,shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id,enquiry_data=item.enquiry,action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action["current_counsellor_id"]:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'enquiry'
                    })
        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], user__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[
               start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj],user__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False,user=item.user, action_updated_at__date__range=(couns_action_from, couns_action_to)).order_by("-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'user'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'user'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj, user__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[
               start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj,user__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id,user=item.user, action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action["current_counsellor_id"]:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'user'
                    })
    elif type == 'Callscheduledbyparent':
        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj],call_scheduled_by_parent__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[
               start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj],call_scheduled_by_parent__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False,call_scheduled_by_parent=item.call_scheduled_by_parent,action_updated_at__date__range=(couns_action_from, couns_action_to)).order_by("-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'Callscheduledbyparent'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'Callscheduledbyparent'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj,call_scheduled_by_parent__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj,call_scheduled_by_parent__isnull=False,timestamp__date__range=(shared_transfer_from,shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id, call_scheduled_by_parent=item.call_scheduled_by_parent,action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action["current_counsellor_id"]:
                    all_users.append({
                        'name': item.call_scheduled_by_parent.name,
                        'id': item.call_scheduled_by_parent.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'Callscheduledbyparent'
                    })
    elif type == 'enquiry':
        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], enquiry__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[
               start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj],enquiry__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('timestamp'):
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False, enquiry_data=item.enquiry,
                                                            action_updated_at__date__range=(
                                                            couns_action_from, couns_action_to)).order_by(
                    "-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'enquiry'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'enquiry'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj, enquiry__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj,enquiry__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id,enquiry_data=item.enquiry,action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action[
                    "current_counsellor_id"]:
                    all_users.append({
                        'name': item.enquiry.parent_name,
                        'id': item.enquiry.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'enquiry'
                    })
    elif type == 'user':
        if len(SharedCounsellor.objects.filter(shared_with__in=[counselor_obj], user__isnull=False,timestamp__date__range=(shared_transfer_from, shared_transfer_to))[
               start_offset:end_offset]) > 0:
            for item in SharedCounsellor.objects.filter(shared_with__in=[counselor_obj],user__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__isnull=False, user=item.user,action_updated_at__date__range=(couns_action_from, couns_action_to)).order_by("-action_updated_at").first()
                if couns_obj and item.timestamp > couns_obj.action_updated_at:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'user'
                    })
                if not couns_obj:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Shared by {item.counsellor.user.user_ptr.name}.', 'action': 'shared',
                        'type': 'user'
                    })
        if len(TransferredCounsellor.objects.filter(transfer_to=counselor_obj,user__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to))[start_offset:end_offset]) > 0:
            for item in TransferredCounsellor.objects.filter(transfer_to=counselor_obj,user__isnull=False, timestamp__date__range=(shared_transfer_from, shared_transfer_to)).order_by('-timestamp')[start_offset:end_offset]:
                couns_obj = CounselingAction.objects.filter(counseling_user__id=counselor_obj.id,user=item.user, action_updated_at__date__range=(couns_action_from, couns_action_to)).first()
                if couns_obj and couns_obj.first_action["previous_counsellor_id"] == couns_obj.first_action[
                    "current_counsellor_id"]:
                    all_users.append({
                        'name': item.user.name,
                        'id': item.user.id,
                        'msg': f'Transferred by {item.transfer_by.user.user_ptr.name}.', 'action': 'transfer',
                        'type': 'user'
                    })
    new = set()
    new_all_users = []
    for user in all_users:
        t = tuple(user.items())
        if t not in new:
            new.add(t)
            new_all_users.append(user)

    if offset == 25:
        new_offset = offset * 2
        next_url = f'api/v2/admin_custom/shared-transfer-counselor/{type}/?offset={new_offset}&couns_action_from={couns_action_from}&couns_action_to={couns_action_to}&shared_transfer_from={shared_transfer_from}&shared_transfer_to={shared_transfer_to}'
        prev_url = None
    else:
        start_offset = offset - 25
        end_offset = offset
        new_next_offset = offset + 25
        new_prev_offset = offset - 25
        if new_prev_offset == 0:
            new_prev_offset = ''
        next_url = f'api/v2/admin_custom/shared-transfer-counselor/{type}/?offset={new_next_offset}&couns_action_from={couns_action_from}&couns_action_to={couns_action_to}&shared_transfer_from={shared_transfer_from}&shared_transfer_to={shared_transfer_to}'
        prev_url = f'api/v2/admin_custom/shared-transfer-counselor/{type}/?offset={new_prev_offset}&couns_action_from={couns_action_from}&couns_action_to={couns_action_to}&shared_transfer_from={shared_transfer_from}&shared_transfer_to={shared_transfer_to}'
    result = {}
    result['count'] = len(new_all_users)
    result['next'] = next_url
    result['previous'] = prev_url
    result['results'] = new_all_users
    return result

class SharedTransferredCounselorView(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]

    def post(self, request, type, *args, **kwargs):
        data = self.request.data
        user = request.user if request.user else None
        cadmin_user_obj = CAdminUser.objects.get(user_ptr__id=user.id)
        counselor_obj = CounselorCAdminUser.objects.get(user=cadmin_user_obj)
        if data["action_name"] == "transfer":
            if type == 'Callscheduledbyparent':
                obj = TransferredCounsellor.objects.create(
                    call_scheduled_by_parent=ParentCallScheduled.objects.get(id=data["id"]),
                    transfer_by=CounselorCAdminUser.objects.get(id=counselor_obj.id),
                    transfer_to=CounselorCAdminUser.objects.get(id=data["counsellor"]),
                )
                couns_obj = CounselingAction.objects.filter(call_scheduled_by_parent__id=data["id"]).first()
                comment_obj = CommentSection.objects.filter(call_scheduled_by_parent__id=data["id"])
                for cmnt in comment_obj:
                    cmnt.counseling = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                    cmnt.save()
                couns_obj.counseling_user = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                couns_obj.first_action["previous_counsellor"] = counselor_obj.user.user_ptr.name
                couns_obj.first_action["previous_counsellor_id"] = counselor_obj.id
                couns_obj.first_action["counsellor_id"] = obj.transfer_to.id
                couns_obj.first_action["current_counsellor_id"] = counselor_obj.id
                couns_obj.first_action["counsellor_name"] = obj.transfer_to.user.user_ptr.name
                couns_obj.save()
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )
            elif type == 'enquiry':
                obj = TransferredCounsellor.objects.create(
                    enquiry=SchoolEnquiry.objects.get(id=data["id"]),
                    transfer_by=CounselorCAdminUser.objects.get(id=counselor_obj.id),
                    transfer_to=CounselorCAdminUser.objects.get(id=data["counsellor"]),
                )
                couns_obj = CounselingAction.objects.filter(enquiry_data__id=data["id"]).first()
                comment_obj = CommentSection.objects.filter(enquiry_comment__id=data["id"])
                for cmnt in comment_obj:
                    cmnt.counseling = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                    cmnt.save()
                couns_obj.counseling_user = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                couns_obj.first_action["previous_counsellor"] = counselor_obj.user.user_ptr.name
                couns_obj.first_action["previous_counsellor_id"] = counselor_obj.id
                couns_obj.first_action["counsellor_id"] = obj.transfer_to.id
                couns_obj.first_action["current_counsellor_id"] = counselor_obj.id
                couns_obj.first_action["counsellor_name"] = obj.transfer_to.user.user_ptr.name
                couns_obj.save()
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )
            elif type == 'user':
                    obj = TransferredCounsellor.objects.create(
                        user=User.objects.get(id=data["id"]),
                        transfer_by=CounselorCAdminUser.objects.get(id=counselor_obj.id),
                        transfer_to=CounselorCAdminUser.objects.get(id=data["counsellor"]),
                    )
                    couns_obj = CounselingAction.objects.filter(user__id=data["id"]).first()
                    comment_obj = CommentSection.objects.filter(user__id=data["id"])
                    for cmnt in comment_obj:
                        cmnt.counseling = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                        cmnt.save()
                    couns_obj.counseling_user = CounselorCAdminUser.objects.get(id=obj.transfer_to.id)
                    couns_obj.first_action["previous_counsellor"] = counselor_obj.user.user_ptr.name
                    couns_obj.first_action["previous_counsellor_id"] = counselor_obj.id
                    couns_obj.first_action["current_counsellor_id"] = counselor_obj.id
                    couns_obj.first_action["counsellor_id"] = obj.transfer_to.id
                    couns_obj.first_action["counsellor_name"] = obj.transfer_to.user.user_ptr.name
                    couns_obj.save()
                    return Response(
                        data={"message": "Data submitted successfully."},
                        status=status.HTTP_200_OK,
                    )
        elif data["action_name"] == "shared":
            if type == 'Callscheduledbyparent':
                obj,_ = SharedCounsellor.objects.get_or_create(
                    call_scheduled_by_parent=ParentCallScheduled.objects.get(id=data["id"]),
                    counsellor=CounselorCAdminUser.objects.get(id=counselor_obj.id),
                    )
                for i in CounselorCAdminUser.objects.filter(id__in=[data["counsellor"]]):
                    obj.shared_with.add(i)
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )
            elif type == 'enquiry':
                obj,_ = SharedCounsellor.objects.get_or_create(
                    enquiry=SchoolEnquiry.objects.get(id=data["id"]),
                    counsellor=CounselorCAdminUser.objects.get(id=counselor_obj.id),

                    )
                for i in CounselorCAdminUser.objects.filter(id__in=[data["counsellor"]]):
                    obj.shared_with.add(i)
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )
            elif type == 'user':
                obj,_ = SharedCounsellor.objects.get_or_create(
                    user=User.objects.get(id=data["id"]),
                    counsellor=CounselorCAdminUser.objects.get(id=counselor_obj.id),
                    )
                for i in CounselorCAdminUser.objects.filter(id__in=[data["counsellor"]]):
                    obj.shared_with.add(i)
                return Response(
                    data={"message": "Data submitted successfully."},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                data={"message": "No data found."},
                status=status.HTTP_200_OK,
            )

    def get(self, request, type, *args, **kwargs):
        additional_offset = None
        response = {"count": 0, "next": None, "previous": None, "results": []}
        i = 0
        local_result = []
        local_count = 0
        local_next = None
        local_previous = None
        data = get_all_shared_data(self, request, type, additional_offset)
        local_result = data["results"]
        local_count = data["count"]
        local_next = data["next"]
        local_previous = data["previous"]
        current_offset = int(data["next"].split("offset=")[1].split("&")[0])
        additional_offset = current_offset
        i = 0
        while i < 28:
            if local_count < 20:
                additional_offset = additional_offset + 25
                data = get_all_shared_data(self, request, type, additional_offset)
                i += 1
                local_result = local_result + data["results"]
                local_result = unique_a_list_of_dict(local_result)
                local_count = len(local_result)
                local_next = data["next"]
                local_previous = data["previous"]
            else:
                break

        response = {"count": local_count, "next": local_next, "previous": local_previous, "results": local_result}
        return Response(response, status=status.HTTP_200_OK)
