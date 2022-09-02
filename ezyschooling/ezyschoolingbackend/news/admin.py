from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .forms import NewsAdminForm
from .models import News, NewsHeadline


class NewsHeadlineAdmin(admin.TabularInline):
    model = NewsHeadline


@admin.register(News)
class NewsAdmin(ImportExportModelAdmin):
    change_list_template = "news/admin_changelist.html"
    list_display = (
        "mini_title",
        "board",
        "status",
        "is_featured",
        "views",
        "timestamp",
    )
    autocomplete_fields = ["author"]
    list_per_page = 50
    inlines = [NewsHeadlineAdmin, ]
    filter_horizontal = ["for_schools",]
    list_filter = ("timestamp", "is_featured", "status", "board", "author")
    raw_id_fields = ("tags", )
    search_fields = ("slug", "title", "mini_title")
    form = NewsAdminForm


# @admin.register(NewsHeadline)
# class NewsHeadlineAdmin(admin.ModelAdmin):
#     list_display = ("id", "title", "timestamp")
#     list_filter = ("timestamp",)
