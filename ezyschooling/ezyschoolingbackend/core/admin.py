from django.contrib import admin
from notifications.admin import NotificationAdmin
from notifications.models import Notification


class CustomNotificationAdmin(NotificationAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("target")


admin.site.unregister(Notification)

admin.site.register(Notification, CustomNotificationAdmin)
