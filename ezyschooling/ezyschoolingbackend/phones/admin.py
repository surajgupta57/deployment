from django.contrib import admin
from .models import *

@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ["number", "user", "verified"]
    list_filter = ["verified", "created_at"]
    search_fields = ["number"]
    raw_id_fields = ["user"]
