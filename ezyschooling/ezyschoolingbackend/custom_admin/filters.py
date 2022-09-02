import django_filters
from dal import autocomplete
from django.db.models import Count

from admission_forms.models import ChildSchoolCart
from parents.models import ParentProfile
from schools.models import Region, SchoolEnquiry, SchoolProfile, SchoolView

from .widgets import DateRangeInput


class ParentFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(
        field_name="user__date_joined", label="Date:", widget=DateRangeInput,)
    child_count = django_filters.NumberFilter(
        label="Child Count:", method="filter_child_count")

    def filter_child_count(self, queryset, name, value):
        return queryset.annotate(child_count=Count(
            "user__user_childs")).filter(child_count=value)

    class Meta:
        model = ParentProfile
        fields = ["date", "child_count"]


class SchoolViewFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(
        field_name="updated_at", label="Date:", widget=DateRangeInput,)
    school = django_filters.ModelChoiceFilter(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
        queryset=SchoolProfile.objects.all())
    region = django_filters.ModelChoiceFilter(
        field_name="school__region",
        widget=autocomplete.ModelSelect2(
            url='custom_admin:region-autocomplete'),
        queryset=Region.objects.all())

    class Meta:
        model = SchoolView
        fields = ["date", "school", "region"]


class ChildSchoolCartFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(
        field_name="timestamp", label="Date:", widget=DateRangeInput,)
    school = django_filters.ModelChoiceFilter(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
        queryset=SchoolProfile.objects.all())
    region = django_filters.ModelChoiceFilter(
        field_name="school__region",
        widget=autocomplete.ModelSelect2(
            url='custom_admin:region-autocomplete'),
        queryset=Region.objects.all())

    class Meta:
        model = ChildSchoolCart
        fields = ["date", "school", "region"]


class SchoolApplicationFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(
        field_name="timestamp", label="Date:", widget=DateRangeInput,)
    school = django_filters.ModelChoiceFilter(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
        queryset=SchoolProfile.objects.all())
    region = django_filters.ModelChoiceFilter(
        field_name="school__region",
        widget=autocomplete.ModelSelect2(
            url='custom_admin:region-autocomplete'),
        queryset=Region.objects.all())

    class Meta:
        model = SchoolView
        fields = ["date", "school", "region"]


class SchoolEnquiryFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(
        field_name="timestamp", label="Date:", widget=DateRangeInput,)
    school = django_filters.ModelChoiceFilter(
        widget=autocomplete.ModelSelect2(
            url='custom_admin:school-autocomplete'),
        queryset=SchoolProfile.objects.all())

    class Meta:
        model = SchoolEnquiry
        fields = ["date", "school"]
