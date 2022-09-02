from django.contrib import admin
from webpush.admin import PushInfoAdmin
from webpush.models import PushInformation

from schools.models import SchoolProfile
from notification.models import WhatsappSubscribers
from .models import DeviceRegistrationToken,PushNotificationData, UserSelectedCity
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from parents.models import ParentProfile

admin.site.unregister(PushInformation)

@admin.register(UserSelectedCity)
class UserSelectedCityAdmin(admin.ModelAdmin):
    list_display = ['id','user_name','city',"boarding_school","online_school","timestamp"]
    list_filter = (('timestamp', DateTimeRangeFilter),"is_boarding_school","is_online_school","city")
    search_fields = ["user__name","city__name" ]
    raw_id_fields = ["user","city" ]

    def user_name(self,obj):
        parent = ParentProfile.objects.get(id=obj.user.current_parent)
        return parent.name

    def boarding_school(self, obj):
        if obj.is_boarding_school and obj.is_boarding_school == True:
            return "Yes"
        else:
            return "No"

    def online_school(self, obj):
        if obj.is_online_school and obj.is_online_school == True:
            return "Yes"
        else:
            return "No"

@admin.register(PushInformation)
class PushInformation(PushInfoAdmin):
    raw_id_fields = ["user", ]
    change_list_template = "notification/admin_changelist.html"


@admin.register(DeviceRegistrationToken)
class DeviceRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'timestamp', ]
    list_filter = (('timestamp', DateTimeRangeFilter),'is_boarding_school','is_online_school')
    search_fields = ["user__name", ]
    raw_id_fields = ["user", ]
    change_list_template = "notification/new/admin_changelist.html"
    # def has_delete_permission(self, request, obj=None):
    #     return False

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(DeviceRegistrationTokenAdmin, self).change_view(request, object_id, extra_context=extra_context)

@admin.register(PushNotificationData)
class PushNotificationDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'title','city','mobile_or_pc', 'timestamp',]
    list_filter = (('timestamp', DateTimeRangeFilter),)
    search_fields = ["title",'message']
    raw_id_fields = ['city',]
    change_list_template = "notification/new/admin_changelist.html"

    def mobile_or_pc(self,obj):
        if obj.for_desktop_users and obj.for_mobile_users:
            return "Both"
        elif obj.for_desktop_users:
            return "Desktop"
        elif obj.for_mobile_users:
            return "Mobile"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        extra_context['show_save_and_add_another'] = False
        return super(PushNotificationDataAdmin, self).change_view(request, object_id, extra_context=extra_context)

class WhatsappSubscribersAdmin(admin.ModelAdmin):
    list_display = ['user', 'enquiry', 'is_Subscriber', 'phone_number', 'timestamp', 'updated_at']
    raw_id_fields = ['user', 'enquiry']
    search_fields = ['school_name', 'user__id', 'enquiry__id']

    def school_name(self,obj):
        if obj.user and SchoolProfile.objects.filter(user=obj.user).exists():
            sch_obj = SchoolProfile.objects.filter(user=obj.user).first()
            return sch_obj.name

admin.site.register(WhatsappSubscribers,WhatsappSubscribersAdmin)
