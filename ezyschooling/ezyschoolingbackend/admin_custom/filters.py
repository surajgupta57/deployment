from django_filters import rest_framework as filters
from schools.models import SchoolProfile

class SchoolProfileFilter(filters.FilterSet):
    class Meta:
        model = SchoolProfile
        fields = ('collab', 'district_region','district','school_city','school_state')
