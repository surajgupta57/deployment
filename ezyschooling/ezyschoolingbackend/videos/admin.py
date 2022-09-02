from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from categories.models import Board, ExpertUserVideoCategory, SubCategory

from .forms import ExpertUserVideoAdminForm
from .models import ExpertUserVideo, ExpertVideoComment


@admin.register(ExpertUserVideo)
class ExpertUserVideoAdmin(ImportExportModelAdmin):
    list_display = (
        "title",
        "expert",
        "category",
        "is_featured",
        "status",
        "views",
        "timestamp",
    )
    list_filter = (
        "status",
        "category",
        "board",
        "sub_category",
        "expert",
        "is_featured",
        "timestamp",
    )
    raw_id_fields = ("likes", "tags")
    search_fields = ("slug",)
    form = ExpertUserVideoAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "board":
            kwargs["queryset"] = Board.objects.filter(active=True)
        if db_field.name == "category":
            kwargs["queryset"] = ExpertUserVideoCategory.objects.filter(
                active=True)
        if db_field.name == "sub_category":
            kwargs["queryset"] = SubCategory.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ExpertVideoComment)
class ExpertVideoCommentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "video",
        "timestamp",
        "parent_comment",
        "anonymous_user",
    )
    list_filter = ("timestamp", "parent_comment")
    raw_id_fields = ("expert", "likes", "parent", "parent_comment", "video")
