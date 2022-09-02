from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.contrib import admin, messages
from import_export.admin import ExportMixin

from .models import *


class ContactUsUserFilter(admin.SimpleListFilter):
    title = 'Registered User'
    parameter_name = 'registered'

    def lookups(self, request, model_admin):
        return (
            ("1", 'Yes'),
            ("0", 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            queryset = queryset.filter(user__isnull=False)
        if self.value() == "0":
            queryset = queryset.filter(user__isnull=True)
        return queryset


@admin.register(ContactUs)
class ContactUsAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "created_at")
    list_filter = (ContactUsUserFilter, "created_at")
    search_fields = ("name", "email", "phone_number")
    raw_id_fields = ["user"]


@admin.register(CarouselCategory)
class CarouselCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = (
        "button_text",
        "link",
        "category",
        "active",
        "order",
    )
    list_filter = ("category", "active")

    actions = ["mark_active", "mark_inactive"]

    def mark_active(self, request, queryset):
        rows_updated = queryset.update(active=True)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as active.",
                          level=messages.SUCCESS)
    mark_active.short_description = 'Mark selected items as active'
    mark_active.allowed_permissions = ('change',)

    def mark_inactive(self, request, queryset):
        rows_updated = queryset.update(active=False)
        if rows_updated == 1:
            message_bit = '1 items was'
        else:
            message_bit = f"{rows_updated} items were"
        self.message_user(request, f"{message_bit} marked as inactive.",
                          level=messages.SUCCESS)
    mark_inactive.short_description = 'Mark selected items as inactive'
    mark_inactive.allowed_permissions = ('change',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "videos", "image", "link", "button_text", "order")


@admin.register(EzySchoolingNewsArticle)
class EzySchoolingNewsArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "link", "order")


@admin.register(OnlineEvent)
class OnlineEventAdmin(admin.ModelAdmin):
    list_display = ["title", "speaker_name", "url", "event_date", "active"]
    list_filter = ["active", "event_date"]
    search_fields = ["title"]
    ordering = ["-event_date"]


@admin.register(CompetitionCarousel)
class CompetitionCarouselAdmin(admin.ModelAdmin):
    list_display = ["child_name", "parent_name", "category", "order"]
    list_filter = ["category"]


@admin.register(CompetitionCarouselCategory)
class CompetitionCarouselCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]


@admin.register(Achiever)
class AchieverAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("child_name", "parent_name",
                    "phone", "created_at")
    list_filter = ("created_at", )
    search_fields = ("child_name", "parent_name", "phone")


@admin.register(TalentHuntSubmission)
class TalentHuntSubmissionsAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("title", "child_name", "parent_name", "phone",
                    "email", "created_at", "is_winner")
    list_filter = ("created_at", "is_winner", )
    search_fields = ("title", "child_name", "parent_name", "phone", "email")
    prepopulated_fields = {"slug": ["title"]}
    raw_id_fields = ["likes", "referrer"]


class FaqAnswerInline(admin.TabularInline):
    model = FaqAnswer

    formfield_overrides = {
        models.TextField: {'widget': CKEditorUploadingWidget},
    }

    extra = 0


@admin.register(FaqQuestion)
class FaqQuestionAdmin(admin.ModelAdmin):
    list_display = ["title","status","category"]
    list_filter = ["category", "region"]
    search_fields = ["title"]

    inlines = [
        FaqAnswerInline,
    ]
    raw_id_fields = (
        #"school_city",
        # "school_state",
        # "school_country",
        "district",
        "district_region",
    )

@admin.register(FaqCategory)
class FaqCategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "slug"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(AdmissionGuidance)
class AdmissionGuidanceAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ["parent_name", "email", "phone", "target_region", "created_at","paid"]
    list_filter = ["created_at","target_region", "slot"]
    raw_id_fields = ["slot"]

    def paid(self,obj):
        try:
            for i in obj.transaction_order.all():
                if i.payment_id:
                    return True
            return False
        except:
            return False

@admin.register(AdmissionGuidanceSlot)
class AdmissionGuidanceSlotAdmin(admin.ModelAdmin):
    list_display = ["get_day", "time_slot", "event_date"]

    def get_day(self, obj):
        return obj.get_day_display()
    get_day.short_description = "Day"


@admin.register(AdmissionAlert)
class AdmissionAlertAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ["name", "email", "phone_no", "region", "created_at"]
    list_filter = ["region", "created_at"]
    date_hierarchy = "created_at"

@admin.register(AdmissionGuidanceProgramme)
class AdmissionGuidanceProgrammeAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ["name", "email", "phone_no", "region", "created_at"]
    list_filter = ["region", "created_at"]
    date_hierarchy = "created_at"

@admin.register(AdmissionGuidanceProgrammePackage)
class AdmissionGuidanceProgrammePackageAdmin(admin.ModelAdmin):
    list_display = ["id","name","amount"]

@admin.register(SurveyQuestions)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ["label","created_at"]
    list_filter = ["label", "created_at"]
    date_hierarchy = "created_at"

@admin.register(SurveyChoices)
class SurveyChoiceAdmin(admin.ModelAdmin):
    list_display = ["id","question","name"]

@admin.register(SurveyResponses)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ["question","taker","answer"]

class ResponseInline(admin.TabularInline):
    model=SurveyResponses
    raw_id_fields=["question","answer"]
    extra=0

@admin.register(SurveyTaker)
class SurveyTakerAdmin(admin.ModelAdmin):
    list_display = ["user","timestamp"]
    inlines=[ResponseInline]




@admin.register(WebinarRegistrations)
class WebinarRegistrationsAdmin(admin.ModelAdmin):
     list_display = ["id","name", "email", "phone"]

@admin.register(SponsorsRegistrations)
class SponsorsRegistrationsAdmin(admin.ModelAdmin):
    list_display = ["id","name", "email", "phone"]

@admin.register(PastAndCurrentImpactinars)
class PastAndCurrentImpactinarsAdmin(admin.ModelAdmin):
    list_display = ["id","title","descriptions","video_link","held_on"]
    list_filter = ("is_featured", "is_current","status")

@admin.register(InvitedPrincipals)
class InvitedPrincipalsAdmin(admin.ModelAdmin):
    list_display = ["id","name", "designation","school_name","photo"]



@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ["id","name","designation","is_school","photo"]


@admin.register(OurSponsers)
class OurSponsersAdmin(admin.ModelAdmin):
    list_display =  ["id","name","photo","website_link"]

@admin.register(EzyschoolingEmployees)
class EzyemployeeAdmin(admin.ModelAdmin):
    list_display = ["id","name"]

admin.site.register(UnsubscribeEmail)
