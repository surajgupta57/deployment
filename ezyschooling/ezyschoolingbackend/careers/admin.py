from django.contrib import admin
from .models import *
from .forms import *
from import_export.admin import ExportMixin, ImportExportModelAdmin
# Register your models here.

admin.site.register(JobType)
admin.site.register(JobDomain)
admin.site.register(JobLocation)
admin.site.register(JobExperienceRange)
admin.site.register(JobSalary)
admin.site.register(JobJoiningType)
admin.site.register(AppliedJobs)

@admin.register(JobProfile)
class JobProfileAdmin(ImportExportModelAdmin):
    form=JobProfileAdminForm

# @admin.register(AppliedJobs)
# class AppliedJobsAdmin(ImportExportModelAdmin):
#     list_display = ["name", "address", "code", "active"]
