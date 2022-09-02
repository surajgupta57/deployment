from django.contrib import admin
from .models import *
from rangefilter.filter import DateTimeRangeFilter
from import_export.admin import ExportMixin
@admin.register(FormTransaction)
class FormTransactionAdmin(ExportMixin,admin.ModelAdmin):
    list_display = ["payment_id", "status", "amount", "timestamp"]
    list_filter = ["method", ('timestamp', DateTimeRangeFilter)]


@admin.register(FormOrder)
class FormOrderAdmin(admin.ModelAdmin):
    list_display = ["child", "amount", "timestamp","payment_id"]
    list_filter = ["timestamp"]
    raw_id_fields = ["child", "payment_id"]
    search_fields = ["child__name","amount"]

@admin.register(AdmissionGuidanceProgrammeFormTransaction)
class AdmissionGuidanceProgrammeFormTransactionAdmin(admin.ModelAdmin):
    list_display = ["payment_id", "status", "amount", "timestamp"]
    list_filter = ["method", "timestamp"]


@admin.register(AdmissionGuidanceProgrammeFormOrder)
class AdmissionGuidanceProgrammeFormOrderAdmin(admin.ModelAdmin):
    list_display = ["name","email","amount", "timestamp"]
    list_filter = ["amount","timestamp"]
    raw_id_fields = ["payment_id"]

@admin.register(AdmissionGuidanceFormTransaction)
class AdmissionGuidanceFormTransactionAdmin(admin.ModelAdmin):
    list_display = ["payment_id", "status", "amount", "timestamp"]
    list_filter = ["method", "timestamp"]


@admin.register(AdmissionGuidanceFormOrder)
class AdmissionGuidanceFormOrderAdmin(admin.ModelAdmin):
    list_display = ["person","amount", "timestamp"]
    list_filter = ["amount","timestamp"]
    raw_id_fields = ["payment_id"]


@admin.register(SchoolSettlementAccounts)
class SchoolSettlementAccountsAdmin(admin.ModelAdmin):
    list_display = ["school","razorpay_account_id"]
    list_filter = ["school","razorpay_account_id"]
    raw_id_fields = ["school"]

@admin.register(SchoolTransferDetail)
class SchoolTransferDetailAdmin(admin.ModelAdmin):
    list_display = ["school","transfer_id","recipient","amount","payment_done_at"]
    list_filter = ["school","transfer_id","payment_done_at"]
    raw_id_fields = ["school"]