from django.contrib import admin

from .models import *

# admin.site.register(Subscription)
class SubscriptionInlineAdmin(admin.TabularInline):
    model = Subscription
    extra = 0
    exclude = ["email"]


class SubscriptionUserFilter(admin.SimpleListFilter):
    title = 'Registered User'
    parameter_name = 'registered'

    def lookups(self, request, model_admin):
        return (
            ("1", 'Yes'),
            ("0", 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            queryset = queryset.filter(preferences__isnull=False)
        if self.value() == "0":
            queryset = queryset.filter(preferences__isnull=True)
        return queryset


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    readonly_fields = ["uuid"]
    list_display = ["get_user", "group", "frequency", "active", "created_at"]
    list_filter = [SubscriptionUserFilter, "active",
                   "group", "frequency", "created_at", ]
    raw_id_fields = ["preferences"]
    search_fields = ["email", "preferences__user__email"]

    def get_user(self, obj):
        if obj.preferences:
            return obj.preferences.user
        else:
            return obj.email
    get_user.short_description = "User"


@admin.register(Preference)
class PreferencesAdmin(admin.ModelAdmin):
    list_display = ["user", "news", "admission",
                    "parenting", "quiz", "updated_at"]
    raw_id_fields = ["user", "region"]
    list_filter = ["news", "quiz", "admission", "parenting", "updated_at"]
    list_per_page = 50
    inlines = [SubscriptionInlineAdmin]
    search_fields = ["user__username", "user__name"]
