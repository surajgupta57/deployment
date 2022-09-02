from django_filters import rest_framework as filters
from core.filters import CharInFilter
from .models import JobProfile

class JobProfileFilter(filters.FilterSet):
    experience = CharInFilter(field_name="experience__range", lookup_expr="in")
    location = CharInFilter(field_name="location__name", lookup_expr="in")
    joining_type = CharInFilter(field_name="joining_type__type", lookup_expr="in")
    job_domain = CharInFilter(field_name="job_domain__name", lookup_expr="in")
    class Meta:
        model = JobProfile
        fields = [
            "experience",
            "location",
            "joining_type",
            "job_domain"
        ]
