from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from accounts.models import User

from .models import ExpertUserProfile


@admin.register(ExpertUserProfile)
class ExpertUserProfileAdmin(ImportExportModelAdmin):
    list_display = (
        "name",
        "designation",
        "is_expert_panel",
        "timestamp",
    )
    list_filter = ("is_expert_panel", "timestamp")
    raw_id_fields = ["user"]
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "user":
    #         kwargs["queryset"] = User.objects.filter(current_parent=-1)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)
