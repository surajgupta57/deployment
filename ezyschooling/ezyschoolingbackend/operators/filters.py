import django_filters
from django import forms
from schools.models import Region,SchoolClasses
from admission_forms.models import ApplicationStatus

class SchoolOperatorFilter(django_filters.FilterSet):
    region__name = django_filters.ModelChoiceFilter(queryset=Region.objects.all(),label='Region')


class SchoolApplicationOperatorFilter(django_filters.FilterSet):
    apply_for__name = django_filters.ModelChoiceFilter(queryset=SchoolClasses.objects.all(),label='Class')
    # school__status__name = django_filters.ModelChoiceFilter(queryset=ApplicationStatus.objects.all(),label='Class')