from django.contrib import admin
from import_export.admin import ExportActionMixin, ExportMixin

from .models import ClickLogEntry, PageVisited


@admin.register(PageVisited)
class PageVisitedAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "path",
        "user",
        "client_ip",
        "timestamp",
    )
    list_filter = ("content_type", "timestamp")
    raw_id_fields = ["user"]
    list_per_page = 50
    date_hierarchy = "timestamp"


@admin.register(ClickLogEntry)
class ClickLogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "path",
        "user",
        "client_ip",
        "action_time",
    )
    list_filter = ("content_type", "action_time")
    raw_id_fields = ["user"]
