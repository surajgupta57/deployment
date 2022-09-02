from django.contrib import admin

from .models import BrandEnquiry, BrandProfile

from rangefilter.filter import DateTimeRangeFilter

@admin.register(BrandProfile)
class BrandProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "slug", "timestamp", "views")
    list_filter = ("user", "timestamp")
    search_fields = ("slug",)


@admin.register(BrandEnquiry)
class BrandEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "phone_number",
        "message",
        "timestamp",
        "brand",
    )
    list_filter = (('timestamp', DateTimeRangeFilter), "brand")
    search_fields = ("name",)
