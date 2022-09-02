from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from categories.models import Board, SubCategory

from .forms import ExpertArticleAdminForm
from .models import ExpertArticle, ExpertArticleComment


@admin.register(ExpertArticle)
class ExpertArticleAdmin(ImportExportModelAdmin):
    list_display = (
        "title",
        "slug",
        "board",
        "sub_category",
        "created_by",
        "views",
        "status",
        "timestamp",
    )
    form = ExpertArticleAdminForm
    list_filter = ("board", "sub_category", "status",
                   "pinned", "created_by", "timestamp")
    filter_horizontal = ["for_schools",]
    list_per_page = 50
    raw_id_fields = ("likes", "tags")
    search_fields = ("title", "slug",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "board":
            kwargs["queryset"] = Board.objects.filter(active=True)
        if db_field.name == "sub_category":
            kwargs["queryset"] = SubCategory.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ExpertArticleComment)
class ExpertArticleCommentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "article",
        "timestamp",
        "parent_comment",
        "anonymous_user",
    )
    list_filter = (
        "timestamp",
    )
    raw_id_fields = ("article", "likes", "parent", "parent_comment")
