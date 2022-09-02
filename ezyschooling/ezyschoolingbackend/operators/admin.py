from django.contrib import admin

from .models import *


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    raw_id_fields=['user']
    filter_horizontal=['school']

