from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Board, ExpertUserVideoCategory, SubCategory, PopupCategory


@admin.register(Board)
class BoardAdmin(ImportExportModelAdmin):
    list_display = (
        "name",
        "min_age",
        "max_age",
        "description",
        "slug",
        "thumbnail",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):
    list_display = (
        "name",
        "slug",
        "description",
        "thumbnail",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(ExpertUserVideoCategory)
class ExpertUserVideoCategoryAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug", "active")
    search_fields = ("name", "slug")
    list_filter = ["active"]
    prepopulated_fields = {"slug": ["name"]}

@admin.register(PopupCategory)
class PopupCategoryAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "name",
        "image",
        "link",
    )
    list_filter = ("name",)
    search_fields = ("name",)
