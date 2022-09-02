from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from .models import User, Token
from import_export.admin import ImportExportModelAdmin
import csv
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from django.contrib.admin.models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    # to have a date-based drilldown navigation in the admin page
    date_hierarchy = 'action_time'

    # to filter the resultes by users, content types and action flags
    list_filter = [
        'content_type',
        'action_flag',
        'action_time',
    ]

    # when searching the user will be able to search in both object_repr and change_message
    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'content_type',
        'action_flag',
    ]

@admin.register(User)
class UserAdmin(AuthUserAdmin):
    fieldsets = (
        (
            "User Profile",
            {
                "fields": (
                    "is_parent",
                    "is_school",
                    "is_expert",
                    "is_brand",
                    "is_uniform_app",
                    "is_facebook_user",
                    "current_parent",
                    "current_child",
                    "current_school",
                    "name",
                    "ad_source"
                )
            },
        ),
    ) + AuthUserAdmin.fieldsets

    actions = ["export_as_csv"]
    list_filter = [('date_joined', DateTimeRangeFilter),"ad_source","is_school", "is_parent", "is_expert", "is_staff", "is_uniform_app","is_superuser", "last_login",]
    readonly_fields = ("ad_source",)
    date_hierarchy = "date_joined"

    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field)
                                   for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(Token)
class TokenAdmin(ImportExportModelAdmin):
    list_display = ["key", "user", "created"]
    search_fields = ["user__username"]
    list_per_page = 50
    list_filter = ("created", )
    fields = ["user", "key", "created"]
    raw_id_fields = ["user"]
    readonly_fields = ["created"]


@admin.register(Session)
class SessionAdmin(ImportExportModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()

    list_display = ["session_key", "_session_data", "expire_date"]
