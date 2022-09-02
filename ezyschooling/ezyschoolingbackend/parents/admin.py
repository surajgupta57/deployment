from django.contrib import admin
from import_export.admin import (ExportActionMixin, ExportMixin,
                                 ImportExportModelAdmin)

from .models import ParentAddress, ParentProfile,ParentTracker
from .resources import ParentProfileResource,ParentTrackResource,ParentAddressResource
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

@admin.register(ParentProfile)
class ParentProfileAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ParentProfileResource
    list_per_page = 150
    date_hierarchy = "timestamp"
    list_display = (
        "name",
        "email",
        "date_of_birth",
        "gender",
        "phone",
        "parent_type",
    )
    raw_id_fields = [
        "bookmarked_articles",
        "bookmarked_discussions",
        "bookmarked_videos",
        "follow_tags",
        "user",
        "alumni_school_name"
    ]
    list_filter = ("date_of_birth", "parent_type", ('timestamp', DateTimeRangeFilter))
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(ParentAddress)
class ParentAddressAdmin(ExportMixin,admin.ModelAdmin):
    resource_class=ParentAddressResource
    list_display = (
        "id",
        "parent",
        "street_address",
        "city",
        "state",
        "pincode",
        "country",
        "monthly_budget",
        "timestamp",
    )
    list_filter = ("state","city")
    raw_id_fields =["user","region","parent"]
    search_fields=["pincode","city","state","parent__name"]


class ScrapeStatusFilter(SimpleListFilter):
  title = 'Income status' # a label for our filter
  parameter_name = 'pages' # you can put anything here

  def lookups(self, request, model_admin):
    # This is where you create filter options; we have two:
    return [
        ('incomefilled', 'Income filled')
    ]

  def queryset(self, request, queryset):
    # This is where you process parameters selected by use via filter options:
    if self.value() == 'incomefilled':
        # Get websites that have at least one page.
        return ParentTracker.objects.all().filter(Q(parent__income__isnull=False))


@admin.register(ParentTracker)
class ParentTrackerAdmin(ExportMixin,admin.ModelAdmin):
    resource_class=ParentTrackResource
    model = ParentTracker
    list_display = ('name','email','phone','timestamp','income','region','street_address','city','state','pincode')
    list_filter = [ScrapeStatusFilter,('timestamp', DateTimeRangeFilter),'address__region','address__city']
    def name(self,obj):
        try:
            if obj.parent:
                return obj.parent.name
            return 'N/A'
        except:
            return 'N/A'

    def email(self, obj):
        try:
            if obj.parent:
                return obj.parent.email
            return 'N/A'
        except:
            return 'N/A'



    def phone(self, obj):
        try:
            if obj.parent:
                return obj.parent.phone
            return 'N/A'
        except:
            return 'N/A'


    def income(self,obj):
        try:
            if obj.parent:
                return obj.parent.income
            return 'N/A'
        except:
            return 'N/A'



    def street_address(self,obj):
        try:
            if obj.address:
                return obj.address.street_address
            return 'N/A'
        except:
            return 'N/A'

    def city(self,obj):
        try:
            if obj.address:
                return obj.address.city
            return 'N/A'
        except:
            return 'N/A'


    def state(self,obj):
        try:
            if obj.address:
                return obj.address.state
            return 'N/A'
        except:
            return 'N/A'


    def pincode(self,obj):
        try:
            if obj.address:
                return obj.address.pincode
            return 'N/A'
        except:
            return 'N/A'


    def region(self,obj):
        try:
            if obj.address:
                return obj.address.region
            return 'N/A'
        except:
            return 'N/A'
