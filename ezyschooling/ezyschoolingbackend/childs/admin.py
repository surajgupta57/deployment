from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Child

from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

@admin.register(Child)
class ChildAdmin(ImportExportModelAdmin):
    list_display = (
        "name",
        "user",
        "date_of_birth",
        "gender",
        "date_of_birth",
        "timestamp",
    )
    list_filter = ("gender", "no_school", ('timestamp', DateTimeRangeFilter))
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    raw_id_fields = ["user", "class_applying_for"]
