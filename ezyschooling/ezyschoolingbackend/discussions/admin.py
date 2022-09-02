from django.contrib import admin
from django.template.defaultfilters import truncatechars
from import_export.admin import ImportExportModelAdmin

from categories.models import Board, SubCategory

from .forms import DiscussionAdminForm
from .models import Discussion, DiscussionComment


@admin.register(Discussion)
class DiscussionAdmin(ImportExportModelAdmin):
    list_display = (
        "title",
        "anonymous_user",
        "board",
        "sub_category",
        "status",
        "timestamp",
    )
    list_filter = ("status", "board", "sub_category", "timestamp")
    raw_id_fields = ("likes", "tags")
    search_fields = ("slug",)
    form = DiscussionAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "board":
            kwargs["queryset"] = Board.objects.filter(active=True)
        if db_field.name == "sub_category":
            kwargs["queryset"] = SubCategory.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DiscussionComment)
class DiscussionCommentAdmin(ImportExportModelAdmin):
    list_display = (
        "custom_comment",
        "discussion",
        "parent_comment",
        "timestamp",
    )
    list_filter = ("discussion", "timestamp", "parent_comment")
    raw_id_fields = ("likes", "parent", "discussion")

    def custom_comment(self, obj):
        return truncatechars(obj.comment, 80)
