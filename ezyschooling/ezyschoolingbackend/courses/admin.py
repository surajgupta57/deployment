from django.contrib import admin

from .models import *


class CourseOrderInline(admin.TabularInline):
    model = CourseOrder
    extra = 0
    raw_id_fields = ["payment"]


@admin.register(CourseEnquiry)
class CourseEnquiryAdmin(admin.ModelAdmin):
    list_display = ("child_name", "parent_name",
                    "phone", "class_name", "created_at")
    list_filter = ("created_at", )
    search_fields = ("child_name", "parent_name", "phone")


@admin.register(CourseDemoClassRegistration)
class CourseDemoClassAdmin(admin.ModelAdmin):
    list_display = ("child_name", "parent_name",
                    "phone", "class_name", "created_at")
    list_filter = ("created_at", )
    search_fields = ("child_name", "parent_name", "phone")


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    search_fields = ["child_name"]
    list_display = ["child_name", "course_name",
                    "parent_name", "paid", "created_at"]
    list_filter = ["paid", "created_at"]
    inlines = [CourseOrderInline, ]


@admin.register(CourseOrder)
class CourseOrderAdmin(admin.ModelAdmin):
    search_fields = ["order_id"]
    list_display = ["order_id", "enrollment", "amount", "timestamp"]
    raw_id_fields = ["enrollment", "payment"]
    list_filter = ["timestamp"]


@admin.register(CourseTransaction)
class CourseTransactionAdmin(admin.ModelAdmin):
    list_display = ["order_id", "payment_id", "method", "timestamp"]
    list_filter = ["timestamp"]
    search_fields = ["order_id", "payment_id"]
