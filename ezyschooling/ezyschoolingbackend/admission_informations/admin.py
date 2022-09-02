from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from categories.models import Board, ExpertUserVideoCategory, SubCategory

from .forms import AdmissionInformationArticleAdminForm, AdmissionInformationNewsAdminForm, AdmissionInformationUserVideoAdminForm
from .models import (
            AdmissionInformationArticle,
            AdmissionInformationArticleComment,
            AdmissionInformationNews,
            AdmissionInformationNewsHeadline,
            AdmissionInformationUserVideo,
            AdmissionInformationVideoComment
        )


@admin.register(AdmissionInformationArticle)
class AdmissionInformationArticleAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "title",
        "thumbnail",
        "slug",
        "board",
        "sub_category",
        "created_by",
        "views",
        "status",
        "timestamp",
    )
    form = AdmissionInformationArticleAdminForm
    list_filter = ("board", "sub_category", "created_by", "timestamp")
    raw_id_fields = ("likes", "tags")
    search_fields = ("slug",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "board":
            kwargs["queryset"] = Board.objects.filter(active=True)
        if db_field.name == "sub_category":
            kwargs["queryset"] = SubCategory.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AdmissionInformationArticleComment)
class AdmissionInformationArticleCommentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "article",
        "timestamp",
        "parent_comment",
        "anonymous_user",
    )
    list_filter = ("timestamp",)
    raw_id_fields = ("likes",)


@admin.register(AdmissionInformationUserVideo)
class AdmissionInformationUserVideoAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "expert",
        "title",
        "url",
        "category",
        "board",
        "sub_category",
        "slug",
        "is_featured",
        "status",
        "views",
        "timestamp",
    )
    list_filter = (
        "expert",
        "category",
        "board",
        "sub_category",
        "is_featured",
        "timestamp",
    )
    raw_id_fields = ("likes", "tags")
    search_fields = ("slug",)
    form = AdmissionInformationUserVideoAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "board":
            kwargs["queryset"] = Board.objects.filter(active=True)
        if db_field.name == "category":
            kwargs["queryset"] = ExpertUserVideoCategory.objects.filter(active=True)
        if db_field.name == "sub_category":
            kwargs["queryset"] = SubCategory.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AdmissionInformationVideoComment)
class AdmissionInformationVideoCommentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "video",
        "timestamp",
        "parent_comment",
        "anonymous_user",
    )
    list_filter = ("timestamp", "parent_comment")
    raw_id_fields = ("likes",)



class AdmissionInformationNewsHeadlineAdmin(admin.TabularInline):
    model = AdmissionInformationNewsHeadline


@admin.register(AdmissionInformationNews)
class AdmissionInformationNewsAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "timestamp",
        "image",
        "is_featured",
        "views",
        "status",
        "board",
    )
    inlines = [
        AdmissionInformationNewsHeadlineAdmin,
    ]
    list_filter = ("timestamp", "is_featured", "board")
    raw_id_fields = ("tags",)
    search_fields = ("slug",)
    form = AdmissionInformationNewsAdminForm

