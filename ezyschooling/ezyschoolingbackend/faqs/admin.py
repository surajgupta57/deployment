from django.contrib import admin
from .forms import *
from import_export.admin import ExportMixin, ImportExportModelAdmin
from .models import *
# Register your models here.
@admin.register(CityDistrictFaq)
class CityDistrictFaqAdmin(ImportExportModelAdmin):
    form=CityDistrictFaqForm

@admin.register(CityDistrictBoardFaq)
class CityDistrictBoardFaqAdmin(ImportExportModelAdmin):
    form=CityDistrictBoardFaqForm

@admin.register(CityDistrictSchoolTypeFaq)
class CityDistrictSchoolTypeFaqAdmin(ImportExportModelAdmin):
    form=CityDistrictSchoolTypeFaqForm

@admin.register(CityDistrictCoedFaq)
class CityDistrictCoedFaqAdmin(ImportExportModelAdmin):
    form=CityDistrictCoedFaqForm

@admin.register(CityDistrictGradeFaq)
class CityDistrictGradeFaqAdmin(ImportExportModelAdmin):
    form=CityDistrictGradeFaqForm
