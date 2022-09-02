from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin

from .models import CustomTag, Tagged, CustomSkillTag, SkillTagged, MustSkillTagged, CustomMustSkillTag


@admin.register(CustomTag)
class CustomTagAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug")
    list_per_page = 50
    # raw_id_fields = ("similar_tag",)
    list_filter = ["featured"]
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    actions = ["mark_featured", "mark_not_featured"]

    def mark_featured(self, request, queryset):
        rows_updated = queryset.update(featured=True)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as featured.",
                          level=messages.SUCCESS)
    mark_featured.short_description = 'Mark selected items as featured'
    mark_featured.allowed_permissions = ('change',)

    def mark_not_featured(self, request, queryset):
        rows_updated = queryset.update(featured=False)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as not featured.",
                          level=messages.SUCCESS)
    mark_not_featured.short_description = 'Mark selected items as not featured'
    mark_not_featured.allowed_permissions = ('change', )


@admin.register(Tagged)
class TaggedAdmin(ImportExportModelAdmin):
    list_display = ("id", "content_type", "object_id", "tag", "timestamp")
    list_filter = ("content_type", "tag", "timestamp")


@admin.register(CustomSkillTag)
class CustomSkillTagAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug")
    list_per_page = 50
    # raw_id_fields = ("similar_tag",)
    list_filter = ["featured"]
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    actions = ["mark_featured", "mark_not_featured"]

    def mark_featured(self, request, queryset):
        rows_updated = queryset.update(featured=True)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as featured.",
                          level=messages.SUCCESS)
    mark_featured.short_description = 'Mark selected items as featured'
    mark_featured.allowed_permissions = ('change',)

    def mark_not_featured(self, request, queryset):
        rows_updated = queryset.update(featured=False)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as not featured.",
                          level=messages.SUCCESS)
    mark_not_featured.short_description = 'Mark selected items as not featured'
    mark_not_featured.allowed_permissions = ('change', )

@admin.register(SkillTagged)
class SkillTaggedAdmin(ImportExportModelAdmin):
    list_display = ("id", "content_type", "object_id", "tag", "timestamp")
    list_filter = ("content_type", "tag", "timestamp")
# dfsdfsdfssssssssssss



@admin.register(CustomMustSkillTag)
class CustomMustSkillTagAdmin(ImportExportModelAdmin):
    list_display = ("name", "slug")
    list_per_page = 50
    # raw_id_fields = ("similar_tag",)
    list_filter = ["featured"]
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    actions = ["mark_featured", "mark_not_featured"]

    def mark_featured(self, request, queryset):
        rows_updated = queryset.update(featured=True)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as featured.",
                          level=messages.SUCCESS)
    mark_featured.short_description = 'Mark selected items as featured'
    mark_featured.allowed_permissions = ('change',)

    def mark_not_featured(self, request, queryset):
        rows_updated = queryset.update(featured=False)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as not featured.",
                          level=messages.SUCCESS)
    mark_not_featured.short_description = 'Mark selected items as not featured'
    mark_not_featured.allowed_permissions = ('change', )

@admin.register(MustSkillTagged)
class MustSkillTaggedAdmin(ImportExportModelAdmin):
    list_display = ("id", "content_type", "object_id", "tag", "timestamp")
    list_filter = ("content_type", "tag", "timestamp")
