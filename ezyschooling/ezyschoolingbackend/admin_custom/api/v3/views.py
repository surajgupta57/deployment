import csv
import io
import json
import os
import random
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from . import serializers
from backend.logger import info_logger, error_logger
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.utils.timezone import make_aware
from celery.utils.log import get_task_logger
from accounts.models import User
from admin_custom.permissions import IsExecutiveUser
from admin_custom.models import CounselorCAdminUser, CounselingAction, CAdminUser, ActionSection, SubActionSection, LeadGenerated, VisitScheduleData, AdmissionDoneData, CommentSection
from django.utils.translation import gettext_lazy as _
import pytz
from itertools import chain
from django.db.models import Q
from schools.models import City, SchoolEnquiry

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
        collab = self.request.GET.get('collab', "none")
        if collab == "":
            collab = "none"
        if collab == "true" or collab == True:
            collab_value=[True]
        elif collab == "false" or collab == False:
            collab_value=[False]
        else:
            collab_value=[True,False]

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
        if start_date and end_date:
            if collab == "none":
                startDateTime = make_aware(datetime.strptime(f"{start_date} 00:00:01", '%Y-%m-%d %X'))
                endDateTime = make_aware(datetime.strptime(f"{end_date} 23:59:59", '%Y-%m-%d %X'))
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,action_updated_at__date__gte=startDateTime,action_updated_at__date__lte=endDateTime).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()
                followUps = CounselingAction.objects.filter(counseling_user=counsellor).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).filter(Q(scheduled_time__date__gte=startDateTime)|Q(enquiry_scheduled_time__date__gte=startDateTime)).filter(Q(scheduled_time__date__lte=endDateTime)|Q(enquiry_scheduled_time__date__lte=endDateTime)).count()
                result = []
                pendingEnquiries = "NA"
            else:
                startDateTime = make_aware(datetime.strptime(f"{start_date} 00:00:01", '%Y-%m-%d %X'))
                endDateTime = make_aware(datetime.strptime(f"{end_date} 23:59:59", '%Y-%m-%d %X'))
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,action_updated_at__date__gte=startDateTime,action_updated_at__date__lte=endDateTime,user__isnull=True,enquiry_data__enquiry_data__isnull=False,enquiry_data__school__collab__in=collab_value).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()
                followUps = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__enquiry_data__isnull=False,enquiry_data__school__collab__in=collab_value).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).filter(Q(scheduled_time__date__gte=startDateTime)|Q(enquiry_scheduled_time__date__gte=startDateTime)).filter(Q(scheduled_time__date__lte=endDateTime)|Q(enquiry_scheduled_time__date__lte=endDateTime)).count()
                result = []
                pendingEnquiries = "NA"
        elif enquiry_start_date and enquiry_end_date:
            if collab == "none":
                startDateTime = make_aware(datetime.strptime(f"{enquiry_start_date} 00:00:01", '%Y-%m-%d %X'))
                endDateTime = make_aware(datetime.strptime(f"{enquiry_end_date} 23:59:59", '%Y-%m-%d %X'))
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False, enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()
                followUps = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).count()

                allEnquiries = SchoolEnquiry.objects.filter(Q(school__school_city__id__in=city_list) | Q(school__district__id__in=district_list)|Q(school__district_region__id__in=dist_region_list)).filter(timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,user__isnull=True).count()
                allActionsOnEnquiries = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime).count()
                pendingEnquiries = allEnquiries-allActionsOnEnquiries
            else:
                startDateTime = make_aware(datetime.strptime(f"{enquiry_start_date} 00:00:01", '%Y-%m-%d %X'))
                endDateTime = make_aware(datetime.strptime(f"{enquiry_end_date} 23:59:59", '%Y-%m-%d %X'))
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False, enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime,enquiry_data__school__collab__in=collab_value).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()
                followUps = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime,enquiry_data__school__collab__in=collab_value).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).count()

                allEnquiries = SchoolEnquiry.objects.filter(school__collab__in=collab_value).filter(Q(school__school_city__id__in=city_list) | Q(school__district__id__in=district_list)|Q(school__district_region__id__in=dist_region_list)).filter(timestamp__date__gte=startDateTime,timestamp__date__lte=endDateTime,user__isnull=True).count()

                allActionsOnEnquiries = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date__gte=startDateTime,enquiry_data__timestamp__date__lte=endDateTime,enquiry_data__school__collab__in=collab_value).count()
                pendingEnquiries = allEnquiries-allActionsOnEnquiries
        else:
            if collab == "none":
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                todaysDate = date.today()
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,action_updated_at__date=todaysDate).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()

                followUps = CounselingAction.objects.filter(counseling_user=counsellor).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).filter(Q(scheduled_time__date=todaysDate)|Q(enquiry_scheduled_time__date=todaysDate)).count()

                allEnquiries = SchoolEnquiry.objects.filter(Q(school__school_city__id__in=city_list) | Q(school__district__id__in=district_list)|Q(school__district_region__id__in=dist_region_list)).filter(timestamp__date=todaysDate,user__isnull=True).count()

                allActionsOnEnquiries = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date=todaysDate).count()
                pendingEnquiries = allEnquiries-allActionsOnEnquiries
            else:
                allFollowUpActions = ["Lead Generated", "Visit Scheduled", "Call Scheduled"]
                todaysDate = date.today()
                callDone = CounselingAction.objects.filter(counseling_user=counsellor,action_updated_at__date=todaysDate,user__isnull=True,enquiry_data__isnull=False,enquiry_data__school__collab__in=collab_value).filter(Q(action__considered_as_call_done=True)|Q(sub_actiom__considered_as_call_done=True)|Q(enquiry_action__considered_as_call_done=True)).count()

                followUps = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__school__collab__in=collab_value).filter(Q(action__name__in=allFollowUpActions)|Q(enquiry_action__name__in=allFollowUpActions)).filter(Q(scheduled_time__date=todaysDate)|Q(enquiry_scheduled_time__date=todaysDate)).count()

                allEnquiries = SchoolEnquiry.objects.filter(school__collab__in=collab_value).filter(Q(school__school_city__id__in=city_list) | Q(school__district__id__in=district_list)|Q(school__district_region__id__in=dist_region_list)).filter(timestamp__date=todaysDate,user__isnull=True).count()

                allActionsOnEnquiries = CounselingAction.objects.filter(counseling_user=counsellor,user__isnull=True,enquiry_data__isnull=False,enquiry_data__timestamp__date=todaysDate,enquiry_data__school__collab__in=collab_value).count()
                pendingEnquiries = allEnquiries-allActionsOnEnquiries
        result = [{"name": "Calls Done:-", "value":callDone},{"name": "Pending Followups:-", "value":followUps},{"name": "Unprocessd Enquiries:-", "value":pendingEnquiries}]
        return Response(result,status=status.HTTP_200_OK)
