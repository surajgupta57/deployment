from ipaddress import collapse_addresses
from django.contrib import admin
from .resources import LeadGeneratedResource, AdmissionDoneDataResource, VisitScheduleDataResource,CounselingActionResource
from .models import *
# Register your models here.
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from import_export.admin import ImportExportModelAdmin

admin.site.register(UserType)

@admin.register(CAdminUser)
class CAdminUserAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("user_ptr",'is_admin','is_executive','designation','user_type')
    raw_id_fields = ["user_ptr",'user_type']
    search_fields = ("user_ptr__name", 'user_ptr__email')
@admin.register(DatabaseCAdminUser)
class DatabaseCAdminUserAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "user", "delete_permission", "edit_permission",
    )
    raw_id_fields = ["user"]
    search_fields = ("user__name",)

    # def get_user_type(self, obj):
    #     if obj.user.is_executive:
    #         return "Executive"
    #     elif obj.user.is_admin:
    #         return "Admin"
    #     else:
    #         return "-"
    #
    # get_user_type.short_description = 'User Type's

@admin.register(SalesCAdminUser)
class SalesCAdminUserAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = (
        "user",
        "city",
        "district",
        "district_region",
        "state",
        "get_user_type",
    )
    filter_horizontal = ["assigned_schools"]
    raw_id_fields = ["user", "city", "district", "district_region", "state", ]
    search_fields = ("user__name", "city__name", "district__name", "district_region__name", "state__name")

    def get_user_type(self, obj):
        if obj.user.is_executive:
            return "Executive"
        elif obj.user.is_admin:
            return "Admin"
        else:
            return "-"

    get_user_type.short_description = 'User Type'

@admin.register(CounselorCAdminUser)
class CounselorCAdminUserAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ("user","get_user_type",)
    list_filter = ["city",'online_schools','boarding_schools',"district","district_region",]
    filter_horizontal = ["city","district","district_region",]
    search_fields = ("user__name","city__name","district__name","district_region__name")
    raw_id_fields = ["user",]
    def get_user_type(self, obj):
        if obj.user.is_executive:
            return "Executive"
        elif obj.user.is_admin:
            return "Admin"
        else:
            return "-"
    get_user_type.short_description = 'User Type'

@admin.register(MasterActionCategory)
class MasterActionCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(ViewedParentPhoneNumberBySchool)
class ViewedParentPhoneNumberBySchoolAdmin(admin.ModelAdmin):
    list_display = ['id', 'school', 'lead', 'visit', 'enquiry', 'parent_called', 'school_view', 'school_performed_action_on_enquiry', 'timestamp']
    raw_id_fields = ['school', 'lead', 'visit', 'enquiry', 'parent_called', 'school_view', 'school_performed_action_on_enquiry', 'ongoing_application',]

@admin.register(ActionSection)
class ActionSectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'category']
    list_filter = ["category",]
    raw_id_fields = ["category",]

@admin.register(SubActionSection)
class ActionSectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'action_realtion', 'requires_datetime']
    list_filter = ["action_realtion","requires_datetime"]
    raw_id_fields = ["action_realtion",]

@admin.register(SchoolDashboardMasterActionCategory)
class SchoolDashboardMasterActionCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(SchoolDashboardActionSection)
class SchoolDashboardActionSectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', 'category',"requires_datetime"]
    list_filter = ["category","requires_datetime"]
    raw_id_fields = ["category",]

@admin.register(CommentSection)
class CommentSectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'counseling', 'timestamp']
    search_fields = ["counseling__user__user_ptr__name","child__name"]
    list_filter = (('timestamp', DateTimeRangeFilter),"counseling")
    raw_id_fields = ["user", "counseling", "child",'enquiry_comment','call_scheduled_by_parent']


@admin.register(CounselingAction)
class CounselingActionAdmin(ImportExportModelAdmin):
    resource_class =CounselingActionResource
    list_display = ['id', 'user_name_', 'enquiry_data_name','counseling_user', 'enquiry_action', 'action', 'action_updated_at']
    search_fields = ["counseling_user__user__user_ptr__name","user"]
    list_filter = (('action_created_at', DateTimeRangeFilter),('action_updated_at', DateTimeRangeFilter),"counseling_user")
    raw_id_fields = ["user", "counseling_user",'enquiry_data','enquiry_action','action','call_scheduled_by_parent','sub_actiom']

    def enquiry_data_name(self, obj):
        if obj.enquiry_data:
            return obj.enquiry_data.parent_name.title() or obj.enquiry_data.user.name.title() or obj.enquiry_data.user.username.title()
        else:
            return "-"
    def user_name_(self, obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.call_scheduled_by_parent:
            return obj.call_scheduled_by_parent.name
        else:
            return "-"

# @admin.register(LeadGenerated)
# class LeadGeneratedAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'enquiry','counseling_user', 'lead_updated_at']
#     search_fields = ["counseling__user__user_ptr__name","user_name"]
#     list_filter = (('lead_created_at', DateTimeRangeFilter),('lead_updated_at', DateTimeRangeFilter),"counseling_user")
#     raw_id_fields = ["user", "counseling_user",'enquiry']
#     filter_horizontal = ['lead_for',]

@admin.register(LeadGenerated)
class LeadGeneratedAdmin(ImportExportModelAdmin):
    resource_class = LeadGeneratedResource
    list_display = ['id', 'user_name_', 'enquiry_person', 'user_phone_number','user_email', 'counseling_user', 'leads_for', 'classes', 'budget', 'lead_updated_at']
    search_fields = ["lead_for__name", "counseling_user__user__user_ptr__name", "location",]
    list_filter = (('lead_updated_at', DateTimeRangeFilter), "counseling_user", "lead_for__name")
    raw_id_fields = ["user", "counseling_user",'enquiry','call_scheduled_by_parent']
    filter_horizontal = ['lead_for',]

    def leads_for(self, obj):
        return ", ".join([school.name for school in obj.lead_for.all()])

    def enquiry_person(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name.title() or obj.enquiry.user.name.title() or obj.enquiry.user.username.title()
        else:
            return "-"

    def user_name_(self, obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.call_scheduled_by_parent:
            return obj.call_scheduled_by_parent.name
        else:
            return "-"

@admin.register(VisitScheduleData)
class VisitScheduleDataAdmin(ImportExportModelAdmin):
    resource_class = VisitScheduleDataResource
    list_display = ['id', 'user_name_', 'enquiry_person', 'call_scheduled_by_parent', 'scheduled_by', 'walk_in', 'walk_in_updated_at']
    search_fields = ["walk_in_for__name", "counseling_user__user__user_ptr__name", ]
    list_filter = (('walk_in_updated_at', DateTimeRangeFilter), "counseling_user", "walk_in_for__name")
    raw_id_fields = ["user", "counseling_user",'enquiry','call_scheduled_by_parent']
    filter_horizontal = ['walk_in_for',]

    def walk_in(self, obj):
        return ", ".join([school.name for school in obj.walk_in_for.all()])

    def enquiry_person(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name.title() or obj.enquiry.user.name.title() or obj.enquiry.user.username.title()
        else:
            return "-"

    def user_name_(self, obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.call_scheduled_by_parent:
            return obj.call_scheduled_by_parent.name
        else:
            return "-"

    def scheduled_by(self, obj):
        if obj.counseling_user:
            return obj.counseling_user.user.user_ptr.name.title()
        else:
            return obj.walk_in_for.all().first().name.title()

@admin.register(AdmissionDoneData)
class AdmissionDoneDataAdmin(ImportExportModelAdmin):
    resource_class = AdmissionDoneDataResource
    list_display = ['id', 'user_name_', 'enquiry_person', 'call_scheduled_by_parent', 'done_by', 'admission_done', 'admissiomn_done_updated_at']
    search_fields = ["admission_done_for__name", "counseling_user__user__user_ptr__name", ]
    list_filter = (('admissiomn_done_updated_at', DateTimeRangeFilter), "counseling_user", "admission_done_for__name")
    raw_id_fields = ["user", "counseling_user",'enquiry','call_scheduled_by_parent']
    filter_horizontal = ['admission_done_for',]

    def admission_done(self, obj):
        return ", ".join([school.name for school in obj.admission_done_for.all()])

    def enquiry_person(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name.title() or obj.enquiry.user.name.title() or obj.enquiry.user.username.title()
        else:
            return "-"

    def user_name_(self, obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.call_scheduled_by_parent:
            return obj.call_scheduled_by_parent.name
        else:
            return "-"

    def done_by(self, obj):
        if obj.counseling_user:
            return obj.counseling_user.user.user_ptr.name.title()
        else:
            return obj.admission_done_for.all().first().name.title()

@admin.register(CounsellorDailyCallRecord)
class CounsellorDailyCallRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'counsellor', 'total_number_of_calls', 'first_call_at','latest_call_at']
    search_fields = ["counsellor__user__user_ptr__name"]
    list_filter = (('first_call_at', DateTimeRangeFilter),('latest_call_at', DateTimeRangeFilter),"counsellor")
    raw_id_fields = ["counsellor"]
    readonly_fields = ('counsellor','total_number_of_calls', 'anonymous_enquiry_calls','user_calls','first_call_at','latest_call_at')
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(SchoolAction)
class SchoolActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'lead','visit','admissions','school', 'action_created_at','action_updated_at']
    search_fields = ["school__name"]
    list_filter = (('action_created_at', DateTimeRangeFilter),('action_updated_at', DateTimeRangeFilter),"counsellor")
    raw_id_fields = ['parent_action','counsellor',"lead",'visit','admissions','school','action']

@admin.register(ParentCallScheduled)
class ParentCallScheduledAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','user','phone','city', 'time_slot','timestamp']
    search_fields = ["city__name",'name','phone']
    list_filter = (('timestamp', DateTimeRangeFilter),('time_slot', DateTimeRangeFilter))
    raw_id_fields = ['city','user']

@admin.register(SchoolCommentSection)
class SchoolCommentSectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'lead', 'visit', 'admissions','school','comment']
    search_fields = ["school__name",]
    list_filter = (('timestamp', DateTimeRangeFilter),"counsellor")
    raw_id_fields = ["lead", "visit", "admissions",'school','counsellor','action']

@admin.register(SchoolPerformedActionOnEnquiry)
class SchoolPerformedActionOnEnquiryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'query','school_name','action','action_updated_at']
    list_filter = (('action_created_at', DateTimeRangeFilter),('action_updated_at', DateTimeRangeFilter),)
    search_fields = ["enquiry__school__name",]
    raw_id_fields = ["user", "enquiry", "action"]

    def school_name(self, obj):
        if obj.enquiry and obj.enquiry.school:
            return obj.enquiry.school.name.title()
        else:
            return "-"

    def user_name(self, obj):
        return obj.enquiry.parent_name.title()

    def query(self, obj):
        if obj.enquiry:
            return obj.enquiry.query
        else:
            return "-"

@admin.register(SchoolPerformedCommentEnquiry)
class SchoolPerformedCommentEnquiryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'query','school_name','comment','timestamp']
    list_filter = (('timestamp', DateTimeRangeFilter),)
    search_fields = ["enquiry__school__name",]
    raw_id_fields = ["user", "enquiry",]

    def school_name(self, obj):
        if obj.enquiry and obj.enquiry.school:
            return obj.enquiry.school.name.title()
        else:
            return "-"

    def user_name(self, obj):
        return obj.enquiry.parent_name.title()

    def query(self, obj):
        if obj.enquiry:
            return obj.enquiry.query
        else:
            return "-"


@admin.register(TransferredCounsellor)
class TransferredCounsellorAdmin(admin.ModelAdmin):
    list_display = ['id','user','enquiry','call_scheduled_by_parent','transfer_by','transfer_to','timestamp']
    list_filter = (('timestamp', DateTimeRangeFilter),)
    raw_id_fields = ['user','enquiry','call_scheduled_by_parent','transfer_by','transfer_to',]


@admin.register(SharedCounsellor)
class SharedCounsellorAdmin(admin.ModelAdmin):
    list_display = ['id','user','enquiry','call_scheduled_by_parent','counsellor','timestamp']
    filter_horizontal = ["shared_with",]
    list_filter = (('timestamp', DateTimeRangeFilter),)
    raw_id_fields = ['user','enquiry','call_scheduled_by_parent','counsellor',]
