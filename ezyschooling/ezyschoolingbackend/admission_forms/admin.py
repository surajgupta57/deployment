from django.contrib import admin
from import_export.admin import ExportMixin
import nested_admin

from .models import *
from .resources import *

from django.db.models import Q

from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

import csv
from django.http import HttpResponse


@admin.register(CommonRegistrationForm)
class CommonRegistrationFormAdmin(ExportMixin,admin.ModelAdmin):
    resource_class = CommonRegistrationFormresource
    list_display = (
        "id",
        "child",
        "email",
        "phone_no",
        "pincode",
        "timestamp",
        "street_address",
        "city",
    )
    search_fields = ["child__name","city","pincode","street_address"]
    list_filter = (
        "single_child",
        "first_child",
        "single_parent",
        "first_girl_child",
        "staff_ward",
        ('timestamp', DateTimeRangeFilter),
        "city",
        "pincode",
    )
    raw_id_fields = ["user", "father", "mother", "guardian", "child",
                     "sibling1_alumni_school_name", "sibling2_alumni_school_name",'father_staff_ward_school_name','mother_staff_ward_school_name','guardian_staff_ward_school_name']

@admin.register(CommonRegistrationFormAfterPayment)
class CommonRegistrationFormAfterAdmin(admin.ModelAdmin):
     resource_class = CommonRegistrationFormresource
     list_display = (
         "id",
#         "child",
         "email",
         "phone_no",
         "pincode",
         "timestamp",
         "street_address",
         "city",
     )
     raw_id_fields = ["user",'sibling1_alumni_school_name','sibling2_alumni_school_name',"father_alumni_school_name","mother_alumni_school_name","mother_alumni_school_name"]


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        resource = self.resource_class()
        dataset = resource.export(queryset)
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.__class__.__name__}.csv"'
        return response

class PhoneNumberFilter(admin.SimpleListFilter):


    title = 'Phone Number filter'
    parameter_name = 'form'

    def lookups(self,request,model_admin):
        return(
                ('has_phone_number','Phone Number Present'),
        )

    def queryset(self,request,queryset):
        if not self.value():
            return queryset
        if self.value().lower() == 'has_phone_number':
            return queryset.exclude(Q(form__mother__phone = None) & Q(form__father__phone = None) & Q(form__guardian__phone = None) )

@admin.register(ChildSchoolCart)
class ChildSchoolCartAdmin(ExportMixin,ExportCsvMixin, admin.ModelAdmin):
    resource_class = ChildSchoolCartResource
    raw_id_fields = ["user","child", "form", "school"]
    list_display = ["child", "form", "school","timestamp"]
    list_filter = [('timestamp', DateTimeRangeFilter),PhoneNumberFilter,"ad_source","school__school_city","school__name"]
    search_fields = ["child__name","school__name","school__slug","form__father__name","form__mother__name","form__guardian__name"]
    readonly_fields = ("ad_source",)
    actions = ['export_as_csv']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "school",
            "child",
            "form",
            "form__user",
            "child__class_applying_for")



@admin.register(FormReceipt)
class FormReceiptAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ["receipt_id", "school_applied", "form_fee", "timestamp"]
    raw_id_fields = ["school_applied"]
    list_filter = [('timestamp', DateTimeRangeFilter)]
    resource_class = FormReceiptresource



@admin.register(ChildPointsPreference)
class ChildPointsPreferenceAdmin(admin.ModelAdmin):
    search_fields = ["child__name"]
    list_display = ["child", "updated_at","id"]
    list_filter = [('updated_at', DateTimeRangeFilter),"state","city","pincode"]
    raw_id_fields = ["child"]
    list_per_page = 50


@admin.register(ApplicationStatus)
class ApplicationStatusAdmin(admin.ModelAdmin):
    list_display = ["id","name", "rank", "type","mail_content","sms_content"]


@admin.register(ApplicationStatusLog)
class ApplicationStatusLogAdmins(admin.ModelAdmin):
    list_display = ["id","status","timestamp"]

class ApplicationStatusLogAdmin(nested_admin.NestedTabularInline):
    model=ApplicationStatusLog
    list_display = ["status","timestamp"]



@admin.register(SchoolApplication)
class SchoolApplicationAdmin(nested_admin.NestedModelAdmin):
    list_display = ["id","user", "school", "apply_for","timestamp"]
    search_fields = ["child__name","user__username","school__name"]
    raw_id_fields = ["apply_for", "user", "school", "form", "child","registration_data"]
    list_filter = [('timestamp', DateTimeRangeFilter),"ad_source","form__city","form__state","form__pincode"]
    readonly_fields = ("ad_source",)
    actions = ['export_as_csv']
    inlines=[ApplicationStatusLogAdmin,]




@admin.register(ChildPointsPreferenceSchoolWise)
class ChildPointsPreferenceSchoolWiseAdmin(admin.ModelAdmin):
      list_display = ["school","name","email","total_points"]
      search_fields = ["school__name"]

      def name(self,obj):
        try:
            if obj.pref:
                return obj.pref.child.name
            return 'N/A'
        except:
            return 'N/A'

      def email(self, obj):
        try:
            if obj.pref:
                return obj.pref.child.email
            return 'N/A'
        except:
            return 'N/A'
