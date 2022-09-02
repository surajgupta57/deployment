import nested_admin
from django.contrib import admin, messages
from django.db.models import Count
from import_export.admin import ExportMixin, ImportExportModelAdmin

from parents.models import ParentProfile,ParentAddress
from accounts.models import User
from admission_forms.models import ChildSchoolCart, SchoolApplication
from admin_custom.models import LeadGenerated, VisitScheduleData, AdmissionDoneData
from .models import *
from .resources import *
from .forms import AdmissionPageContentAdminForm,SchoolProfileAdminForm,BoardingSchoolExtendFrom
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

admin.site.register(AgeCriteria)
admin.site.register(DistancePoint)
admin.site.register(SchoolAdmissionAlert)
admin.site.register(AdmissionSession)
admin.site.register(SchoolClassNotification)
admin.site.register(SchoolPoint)

@admin.register(VideoTourLinks)
class VideoTourLinksAdmin(admin.ModelAdmin):
    list_display = ["id","school_id","school","district_region", "district", "city","link"]
    raw_id_fields = ["school"]
    search_fields = ("school__name","link","school__id")
    resource_class = VideoTourLinksResource

    def city(self,obj):
        return obj.school.school_city.name
    def district(self,obj):
        return obj.school.district.name
    def district_region(self,obj):
        return obj.school.district_region.name
    def school_id(self,obj):
        return str(obj.school.id)

def school_enquiries_tuple(sn):
    return (sn.pk, f'{sn.name} {sn.enquiries.count()}')


class SchoolFilter(admin.SimpleListFilter):
    title = 'School'
    parameter_name = 'school__id'

    def lookups(self, request, model_admin):
        return [school_enquiries_tuple(sn) for sn in
                SchoolProfile.objects.prefetch_related('enquiries').annotate(
            num_enquiries=Count('enquiries')).filter(
                num_enquiries__gt=0).order_by('-num_enquiries')[:100]]

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(
                school__id=self.value()
            )
            return queryset


@admin.register(SchoolContactClickData)
class SchoolContactClickDataAdmin(admin.ModelAdmin):
    list_display = ("id", "school", "user", "count_school", "timestamp",)
    ordering = ("school",)
    list_filter = ("school",)
    search_fields = ("school__name",)
    raw_id_fields = ['school', "user",]


@admin.register(SchoolClasses)
class SchoolClassesAdmin(admin.ModelAdmin):
    list_display = ("id", "rank", "name", "active")
    ordering = ("rank",)
    prepopulated_fields = {"slug": ["name"]}
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(SchoolMultiClassRelation)
class SchoolMultiClassRelationAdmin(admin.ModelAdmin):
    list_display = ["id", "unique_class_relation",]
    filter_horizontal = ['multi_class_relation',]
    raw_id_fields = ['unique_class_relation',]
    list_filter = ["unique_class_relation",]
    search_fields = ["unique_class_relation", "multi_class_relation",]


@admin.register(SchoolType)
class SchoolTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ["name"]}


@admin.register(SchoolBoard)
class SchoolBoardAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ("name",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "rank", "active", "is_featured")
    prepopulated_fields = {"slug": ["name"]}
    ordering = ("rank",)
    list_filter = ("active", "is_featured", "state")
    search_fields = ("name",)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "rank", "name", "active")
    ordering = ("rank",)
    prepopulated_fields = {"slug": ["name"]}
    list_filter = ("active",)
    search_fields = ("name",)


class AgeCriteriaInline(nested_admin.NestedTabularInline):
    model = AgeCriteria
    raw_id_fields = ["class_relation"]
    extra = 1


class ActivityAdmin(nested_admin.NestedTabularInline):
    model = Activity
    classes = ["collapse"]
    extra = 1
    list_display = (
        "id",
        "activity_type",
        "image",
        "name",
        "order",
    )
    ordering = ("order",)
    list_filter = ("activity_type",)
    search_fields = ("name",)


class ActivityTypeAdmin(nested_admin.NestedTabularInline):
    model = ActivityType
    list_display = ("id", "name", "order",)
    ordering = ("order",)
    search_fields = ("name",)
    inlines = [
        ActivityAdmin,
    ]
    classes = ["collapse"]
    extra = 1


class GalleryAdmin(nested_admin.NestedTabularInline):
    model = Gallery
    classes = ["collapse"]
    extra = 1
    list_display = ("id", "school", "image", "is_active")
    list_filter = ("school", "is_active")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school")

class SchoolAdmissionResultImageAdmin(nested_admin.NestedTabularInline):
   model = SchoolAdmissionResultImage
   classes = ["collapse"]
   extra = 1
   list_display = ("id", "school", "image")
   list_filter = ("school")

   def get_queryset(self, request):
       qs = super().get_queryset(request)
       return qs.select_related("school")
# class DistancePointAdmin(nested_admin.NestedTabularInline):
#     model = DistancePoint
#     classes = ["collapse"]
#     extra = 1
#     list_display = ("id", "school", "start", "end", "point")
#     list_filter = ("school",)
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related("school")


class SchoolPointAdmin(nested_admin.NestedTabularInline):
    model = SchoolPoint
    classes = ["collapse"]
    extra = 1
    list_display = ("id", "school",)
    list_filter = ("school",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school")


class AdmmissionOpenClassesAdmin(nested_admin.NestedTabularInline):
    model = AdmmissionOpenClasses
    classes = ["collapse"]
    extra = 1
    readonly_fields = ("id",
    "class_relation",
    "school",
    "admission_open",
    "form_limit",
    "draft",
    "available_seats",)
    list_display = (
        "id",
        "class_relation",
        "school",
        "admission_open",
        "form_limit",
        "draft",
        "available_seats",
    )
    list_filter = ("class_relation", "school", "admission_open", "draft")
    search_fields = ("school__name",)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school")

@admin.register(AdmmissionOpenClasses)
class SchoolCLassAdmissionOpenAdmin(admin.ModelAdmin):
     search_fields = ("school__name",)
     list_filter = ("admission_open","session", "school__slug")
     raw_id_fields=['school']

class SchoolAdmissionFormFeeAdmin(nested_admin.NestedTabularInline):
    model = SchoolAdmissionFormFee
    classes = ["collapse"]
    extra = 1
    readonly_fields =("id",
    "class_relation",
    "school_relation",
    "form_price",
    "created_at",)
    list_display = (
        "id",
        "class_relation",
        "school_relation",
        "form_price",
        "created_at",
    )
    list_filter = ("class_relation","school_relation")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school_relation")

# class FeeStructureAdmin(nested_admin.NestedTabularInline):
#     model = FeeStructure
#     classes = ["collapse"]
#     extra = 1
#     list_display = (
#         "id",
#         "class_relation",
#         "school",
#         "active",
#         "draft",
#         "fee_price",
#         "session",
#     )
#     list_filter = ("class_relation", "school", "active", "draft", "session")
#     filter_horizontal = ('fees_parameters',)
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related("school")


@admin.register(SchoolProfile)
class SchoolProfileAdmin(ExportMixin, nested_admin.NestedModelAdmin):
    form = SchoolProfileAdminForm
    resource_class = SchoolProfileResource
    list_display = (
        "id",
        "name",
        "user",
        "email",
        "phone_no",
        "is_active",
        "is_verified",
        "is_featured",
        "collab",
        "avg_fee",
        "calculated_avg_fee",
    )
    list_filter = (
        "ad_source",
        "school_type",
        "school_board",
        "region",
        "state",
        "school_city",
        "school_state",
        "school_country",
        "district",
      #  "district_region",
        "collab",
        "is_active",
        "is_verified",
        "is_featured",
        "point_system",
        "ownership",
        'online_school',
    )
    filter_horizontal = ["class_relation","school_boardss",'languages']
    raw_id_fields = (
        "user",
        "school_city",
        "school_state",
        "school_country",
        "district",
        "district_region",
        "pincode",
    )
    search_fields = ("name", "slug", "id")
    prepopulated_fields = {"slug": ["name"]}
    inlines = [
        ActivityTypeAdmin,
        GalleryAdmin,
        # DistancePointAdmin,
        AdmmissionOpenClassesAdmin,
        AgeCriteriaInline,
#        FeeStructureAdmin,
        SchoolPointAdmin,
        SchoolAdmissionFormFeeAdmin,
        SchoolAdmissionResultImageAdmin,
    ]

    actions = ["mark_featured", "mark_not_featured"]
    readonly_fields = ("ad_source",)
    def mark_featured(self, request, queryset):
        rows_updated = queryset.update(is_featured=True)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as featured.",
                          level=messages.SUCCESS)
    mark_featured.short_description = 'Mark selected items as featured'
    mark_featured.allowed_permissions = ('change',)

    def mark_not_featured(self, request, queryset):
        rows_updated = queryset.update(is_featured=False)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as not featured.",
                          level=messages.SUCCESS)
    mark_not_featured.short_description = 'Mark selected items as not featured'
    mark_not_featured.allowed_permissions = ('change',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "school", "name", "phone")
    list_filter = ("school",)
    search_fields = ("name","school__name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school")


@admin.register(SchoolView)
class SchoolViewAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SchoolViewResource
    list_display = (
        "get_parent",
        "school",
        "count",
        "timestamp",
        "updated_at",
    )
    raw_id_fields = ("user", "school")
    list_filter = ("school", "timestamp", "updated_at")
    date_hierarchy = "updated_at"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("school", "user")

    def get_parent(self, obj):
        return obj.user.name

    get_parent.short_description = "Parent"


# @admin.register(FeeStructure)
# class FeeStructureAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "class_relation",
#         "stream_relation",
#         "school",
#         "session",
#         "active",
#         "draft",
#         "fee_price",
#     )
#     list_filter = ("class_relation", "active", "draft", "session", "school")
#     filter_horizontal = ["fees_parameters",]
#     search_fields = ("school__name",)
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.select_related("school")
#
#     def formfield_for_manytomany(self, db_field, request, **kwargs):
#         if db_field.name == "fees_parameters":
#             if 'object_id' in request.resolver_match:
#                 object=FeeStructure.objects.get(id=request.resolver_match.kwargs['object_id'])
#                 kwargs["queryset"] = SchoolFeesParameters.objects.all().filter(school=object.school)
#             else:
#                 #school_id=request.GET.get('school_id',None)
#                 #if school_id:
#                 #    kwargs["queryset"] = SchoolFeesParameters.objects.all().filter(school=school_id)
#                 #else:
#                 pass
#         return super().formfield_for_manytomany(db_field, request, **kwargs)
#     #def formfield_for_manytomany(self, db_field, request, **kwargs):
#     #   if db_field.name == "fees_parameters":
#     #       object=FeeStructure.objects.get(id=request.resolver_match.kwargs['object_id'])
#     #       kwargs["queryset"] = object.fees_parameters.all()
#     #   return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(SchoolEnquiry)
class SchoolEnquiryAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SchoolEnquiryResource
    list_display = (
        'get_parents_name',
        "school",
        'class_relation',
        'get_school_collab',
        'source',
        'get_phone',
        'get_monthly_budget',
        'get_email_id',
        'get_school_city',
        'get_school_district_region',
        'timestamp')

    list_filter = [('timestamp', DateTimeRangeFilter),'source','ad_source','school__collab','interested_for_visit','class_relation','school__school_city__name',SchoolFilter]
    readonly_fields = ("ad_source",)
    raw_id_fields = ["user", "school"]
    date_hierarchy = "timestamp"
    search_fields = ["school__name"]

    def get_parents_name(self, obj):
        if obj.user:
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            return parent.name
        else:
            return obj.parent_name
    get_parents_name.short_description = "Parent's Name"

    def get_school_collab(self, obj):
        if obj.school.collab:
            return 'Yes'
        else:
            return 'No'
    get_school_collab.short_description = "Collab School"

    def get_phone(self, obj):
        if obj.user:
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            if parent.phone:
                return parent.phone
        return obj.phone_no
    get_phone.short_description = "Phone No."

    def get_email_id(self, obj):
        if obj.user:
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            return parent.email
        else:
            return obj.email
    get_email_id.short_description = "Email"

    def get_school_city(self,obj):
        if obj.school and obj.school.school_city:
            region = obj.school.school_city
            return region.name
        else:
            return "NA"
    get_school_city.short_description= "School City"

    def get_school_district_region(self,obj):
        if obj.school and obj.school.district_region:
            region = obj.school.district_region
            return region.name
        else:
            return "NA"

    get_school_district_region.short_description= "District region"



    def get_monthly_budget(self, obj):
        if obj.user:
            parent = ParentAddress.objects.get(parent=obj.user.current_parent)
            return parent.monthly_budget
        else:
            return "NA"
    get_monthly_budget.short_description = "Monthly Budget"

@admin.register(SchoolFormat)
class SchoolFormatAdmin(admin.ModelAdmin):
    list_display = ["title", "slug"]
    prepopulated_fields = {"slug": ["title"]}

@admin.register(RequiredOptionalSchoolFields)
class RequiredOptionalSchoolFieldsAdmin(admin.ModelAdmin):
    list_display = ["id", "school", "timestamp"]
    raw_id_fields = ["school"]
    search_fields = ["school__name","school__slug"]
    list_filter = [('timestamp', DateTimeRangeFilter),"school"]


@admin.register(SchoolVerificationCode)
class SchoolCodeAdmin(ImportExportModelAdmin):
    list_display = ["name", "address", "code", "active"]


class ActivityAutocompleteInline(admin.TabularInline):
    model = ActivityAutocomplete
    extra = 1


@admin.register(ActivityTypeAutocomplete)
class ActivityTypeAutocompleteAdmin(admin.ModelAdmin):
    list_filter = ["created_at"]
    list_display = ["name", "activities_count", "created_at"]
    search_fields = ["name"]
    inlines = [ActivityAutocompleteInline]

    def activities_count(self, obj):
        return obj.activities.count()


@admin.register(ActivityAutocomplete)
class ActivityAutocompleteAdmin(admin.ModelAdmin):
    raw_id_fields = ["activity_type"]
    list_filter = ["activity_type", "created_at"]
    list_display = ["name", "activity_type"]
    search_fields = ["name"]

# @admin.register(SchoolAdmissionFormFee)
# class SchoolAdmissionFormFeeAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "class_relation",
#         "school_relation",
#         "form_price",
#         "created_at",
#     )
#     list_filter = ("class_relation",)

@admin.register(SchoolStream)
class SchoolStreamAdmin(admin.ModelAdmin):
     list_display = (
        "id",
        "stream",)

@admin.register(SchoolFeesType)
class SchoolFeesTypeAdmin(admin.ModelAdmin):
     list_display = (
        "id",
        "head",)

# @admin.register(SchoolFeesParameters)
# class SchoolFeesPareameterAdmin(admin.ModelAdmin):
#      search_fields = ["school__name"]
#      list_display = (
#         "id",
#         "head",
#        # "school__name",
#         "tenure",
#         "price",
#         "refundable",
#         "upper_price"
#         )
#
#      raw_id_fields = ["school",]

@admin.register(AppliedSchoolSelectedCsv)
class SchoolAdmissionUploadedCsvAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "school_relation",
        "csv_file",
    )

@admin.register(SelectedStudentFromCsv)
class SchoolSelectedChildsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "school_relation",
        "receipt_id",
    )


@admin.register(Pincode)
class SchoolPincodeAdmin(admin.ModelAdmin):
    list_display = ("id","pincode","type")
    search_fields = ["pincode"]

@admin.register(Country)
class SchoolCountryAdmin(admin.ModelAdmin):
    list_display = ("id","name","slug")
    search_fields = ["name"]


@admin.register(States)
class SchoolStateAdmin(admin.ModelAdmin):
    list_display = ("id","name","slug","country")
    search_fields = ["name"]

@admin.register(City)
class SchoolCityAdmin(admin.ModelAdmin):
    list_display = ("id","name","slug","states","country")
    search_fields = ["name"]

@admin.register(District)
class SchoolDistrictAdmin(admin.ModelAdmin):
    list_display = ("id","name","slug","city","state","country")
    search_fields = ["name"]

@admin.register(DistrictRegion)
class SchoolDistrictRegionAdmin(ExportMixin,admin.ModelAdmin):
    resource_class = SchoolDistrictRegionResource
    list_display = ("id","name","slug","latitude","longitude","city","district","state","country")
    search_fields = ["name"]
    list_filter = ("city",'district')
    filter_horizontal = ["pincode"]
    raw_id_fields = ("district","city","country","state",)


@admin.register(Area)
class SchoolAreaAdmin(admin.ModelAdmin):
    list_display = ("id","name","slug","city","district","district_region","state","country")
    search_fields = ["name"]


@admin.register(FeatureName)
class Features(admin.ModelAdmin):
    list_display = (
            "id",
            "name",
        )

@admin.register(Subfeature)
class SubFeatures(admin.ModelAdmin):
    list_display = (
            "id",
            "name",
            "parent"
        )



@admin.register(Feature)
class SchoolFeature(admin.ModelAdmin):
    list_display = ("id","school","exist","features","parent")
    search_fields = ["school__name"]
    def parent(self,obj):
        try:
            if obj.features:
                return obj.features.parent.name
            return 'N/A'
        except:
            return 'N/A'

@admin.register(Subjects)
class SchoolSubjects(admin.ModelAdmin):
    list_display = ("id","name")

@admin.register(AdmissionPageContent)
class AdmissionPageContentAdmin(ImportExportModelAdmin):
    form=AdmissionPageContentAdminForm
    list_display = ["id", "city",'district',"district_region","is_popular"]
    list_filter = ["city","district","is_popular"]
    search_fields = ['city__slug',"district__slug","district_region__slug"]
    raw_id_fields = ["city", "district", "district_region"]

@admin.register(GroupedSchools)
class GroupedSchoolsAdmin(admin.ModelAdmin):
   filter_horizontal=["schools"]
   readonly_fields = ("api_key",)

class LanguageAdmin(admin.ModelAdmin):
    list_display = ["rank", "name",'slug']
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Language, LanguageAdmin)

@admin.register(SchoolAlumni)
class SchoolAlumniAdmin(admin.ModelAdmin):
    list_display=['id','school','name','passing_year']
    list_filter=['school',]
    raw_id_fields = ['school',]
    search_fields = ["school__name"]

@admin.register(FoodCategories)
class FoodCategoriesAdmin(admin.ModelAdmin):
    list_display=['id','name','type',]
    list_filter=['name',]
    search_fields = ["name"]

@admin.register(BoardingSchoolExtend)
class BoardingSchoolExtendAdmin(admin.ModelAdmin):
    form = BoardingSchoolExtendFrom
    list_display=['id','extended_school','withdrawl_policy_available','food_details_available','pre_post_admission_process_available']
    raw_id_fields = ['extended_school']
    list_filter=['extended_school',]
    search_fields = ["extended_school__name"]
    filter_horizontal=["food_option","weekday_schedule","weekend_schedule","infrastruture"]

    def withdrawl_policy_available(self,obj):
        if obj.withdrawl_policy:
            return 'Yes'
        else:
            return 'No'

    def food_details_available(self,obj):
        if obj.food_details:
            return 'Yes'
        else:
            return 'No'

    def pre_post_admission_process_available(self,obj):
        if obj.pre_post_admission_process:
            return 'Yes'
        else:
            return 'No'

@admin.register(DaywiseSchedule)
class DaywiseScheduleAdmin(admin.ModelAdmin):
    list_display=['id','school','type','starting_class','ending_class']
    raw_id_fields = ['school']
    list_filter=['school',"session"]
    search_fields = ["school__name"]
    filter_horizontal=["values",]

@admin.register(ScheduleTimings)
class ScheduleTimingsAdmin(admin.ModelAdmin):
    list_display=['id','name','start_time','end_time','duration']

@admin.register(BoardingSchoolInfrastructureHead)
class BoardingSchoolInfrastructureHeadAdmin(admin.ModelAdmin):
    list_display=['id','name','slug','active']

@admin.register(BoardingSchoolInfrastrutureImages)
class BoardingSchoolInfrastrutureImagesAdmin(admin.ModelAdmin):
    list_display=['id','image','visible','school']

    def school(self,obj):
        all_item = BoardingSchoolInfrastructure.objects.filter(related_images=obj)
        result = ''
        for item in all_item:
            if item == "":
                result = item.school.name
            else:
                result = f"{result}, {item.school.name}"
        return result

@admin.register(BoardingSchoolInfrastructure)
class BoardingSchoolInfrastructureAdmin(admin.ModelAdmin):
    list_display=['id','type','school','description_available']
    raw_id_fields = ['school','type']
    list_filter=['type',"school"]
    search_fields = ["school__name","type__name"]
    filter_horizontal=["related_images",]

    def description_available(self,obj):
        if obj.description:
            return "Yes"
        else:
            return "No"

@admin.register(SchoolClaimRequests)
class SchoolClaimRequestsAdmin(admin.ModelAdmin):
    list_display=['id','school','name','phone_number','email','designation','timestamp']
    raw_id_fields = ['school',]
    list_filter=["school",]
    search_fields = ["school__name","name"]


@admin.register(SchoolEqnuirySource)
class SchoolEqnuirySourceAdmin(ImportExportModelAdmin):
    resource_class = SchoolEnquirySourceResource
    list_display = ["id", 'source_name', "total_clicks", "user", "enquiries", "cart", "applications", "lead_generated",
                    "visit_scheduled", "admission_done", "school_signup"]
    list_filter = ["source_name", "campaign_name"]
    search_fields = ["source_name", "related_id"]
    change_list_template = "schools/admin_changelist.html"
    readonly_fields = ("source_name", "related_id", "campaign_name", "total_clicks")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        extra_context['show_save_and_add_another'] = False
        return super(SchoolEqnuirySourceAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def enquiries(self, obj):
        all_city = City.objects.all()
        data = []
        for city in all_city:
            if SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=True).count() > 0 or SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=False).count() > 0:
                data.append({'City': city.name,
                            "Collab": SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=True).count(),
                            "Non-Collab": SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=False).count(),
                })
        if len(data)>0:
            return data
        return "-"

    def user(self, obj):
        return User.objects.filter(ad_source=obj.source_name.title()).count()

    def cart(self, obj):
        return ChildSchoolCart.objects.filter(ad_source=obj.source_name.title()).count()

    def applications(self, obj):
        all_city = City.objects.all()
        data = []
        for city in all_city:
            if SchoolApplication.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug).count()>0:
                data.append({'City': city.name,
                            "Total": SchoolApplication.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug).count(),
                })

        if len(data) > 0:
            return data
        return "-"

    def lead_generated(self, obj):
        ad_src = obj.source_name.title()
        adm_objs, adm_cnt = [], 0
        visits_objs, visits_cnt = [], 0
        leads_objs, leads_cnt = [], 0
        if AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
            Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            adm_objs = [obj for obj in AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if VisitScheduleData.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            visits_objs = [obj for obj in VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if LeadGenerated.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            leads_objs = [obj for obj in
                          LeadGenerated.objects.filter(
                              Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                              Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]
            leads_cnt = LeadGenerated.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).count()

        remove_visit_cnt = 0
        remove_lead_cnt = 0
        for adm_usr in adm_objs:
            for visit_usr in visits_objs:
                if adm_usr.user and visit_usr.user and adm_usr.user.id == visit_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and visit_usr.enquiry and adm_usr.enquiry.id == visit_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
            for lead_usr in leads_objs:
                if adm_usr.user and lead_usr.user and adm_usr.user.id == lead_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and lead_usr.enquiry and adm_usr.enquiry.id == lead_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
        for lead_usr in leads_objs:
            for visit_usr in visits_objs:
                if lead_usr.user and visit_usr.user and lead_usr.user.id == visit_usr.user.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1
                if lead_usr.enquiry and visit_usr.enquiry and lead_usr.enquiry.id == visit_usr.enquiry.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1

        leads_cnt = leads_cnt - remove_lead_cnt
        return leads_cnt

    def visit_scheduled(self, obj):
        ad_src = obj.source_name.title()
        adm_objs, adm_cnt = [], 0
        visits_objs, visits_cnt = [], 0
        leads_objs, leads_cnt = [], 0
        if AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
            Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            adm_objs = [obj for obj in AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if VisitScheduleData.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            visits_objs = [obj for obj in VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]
            visits_cnt = VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).count()

        if LeadGenerated.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            leads_objs = [obj for obj in
                          LeadGenerated.objects.filter(
                              Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                              Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        remove_visit_cnt = 0
        remove_lead_cnt = 0
        for adm_usr in adm_objs:
            for visit_usr in visits_objs:
                if adm_usr.user and visit_usr.user and adm_usr.user.id == visit_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and visit_usr.enquiry and adm_usr.enquiry.id == visit_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
            for lead_usr in leads_objs:
                if adm_usr.user and lead_usr.user and adm_usr.user.id == lead_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and lead_usr.enquiry and adm_usr.enquiry.id == lead_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
        for lead_usr in leads_objs:
            for visit_usr in visits_objs:
                if lead_usr.user and visit_usr.user and lead_usr.user.id == visit_usr.user.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1
                if lead_usr.enquiry and visit_usr.enquiry and lead_usr.enquiry.id == visit_usr.enquiry.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1

        visits_cnt = visits_cnt - remove_visit_cnt
        return visits_cnt

    def admission_done(self,obj):
        return AdmissionDoneData.objects.filter(user__ad_source=obj.source_name.title(),counseling_user__isnull=False,enquiry__isnull=True).count() + AdmissionDoneData.objects.filter(enquiry__ad_source=obj.source_name.title(),counseling_user__isnull=False,user__isnull=True).count()

    def school_signup(self, obj):
        return SchoolProfile.objects.filter(ad_source=obj.source_name.title()).count()

# admin.site.register(Coupons)
@admin.register(Coupons)
class CouponsAdmin(admin.ModelAdmin):
    list_display=['id','school','school_code','school_amount','ezyschool_code','ezyschool_amount']
    raw_id_fields = ['school',]
    list_filter=["school",]
    search_fields = ["school__name"]
