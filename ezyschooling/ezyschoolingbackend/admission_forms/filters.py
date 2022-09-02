from django_filters import rest_framework as filters

from admission_forms.models import (ChildSchoolCart,
                                    CommonRegistrationForm, SchoolApplication)
from core.filters import CharInFilter


class CommonRegistrationFormFilter(filters.FilterSet):

    child = CharInFilter(field_name="child__id", lookup_expr="in")

    created_by = CharInFilter(field_name="created_by__slug", lookup_expr="in")

    timestamp_gte = filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    timestamp_lt = filters.DateTimeFilter(field_name="timestamp", lookup_expr="lt")

    year_created = filters.NumberFilter(field_name="timestamp", lookup_expr="year")
    year_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="year__gte"
    )
    year_created_lt = filters.NumberFilter(
        field_name="timestamp", lookup_expr="year__lt"
    )

    day_created = filters.NumberFilter(field_name="timestamp", lookup_expr="day")
    day_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="day__gte"
    )
    day_created_lt = filters.NumberFilter(field_name="timestamp", lookup_expr="day__lt")

    month_created = filters.NumberFilter(field_name="timestamp", lookup_expr="month")
    month_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="month__gte"
    )
    month_created_lt = filters.NumberFilter(
        field_name="timestamp", lookup_expr="month__lt"
    )
    session = CharInFilter(field_name="session",lookup_expr="in")
    class Meta:
        model = CommonRegistrationForm
        fields = [
            "child",
            "created_by",
            "timestamp_gte",
            "timestamp_lt",
            "year_created",
            "year_created_gte",
            "year_created_lt",
            "day_created",
            "day_created_gte",
            "day_created_lt",
            "month_created",
            "month_created_gte",
            "month_created_lt",
            "session",
        ]


class ChildSchoolCartFilter(filters.FilterSet):

    include_complete_data = filters.CharFilter(
        method="includes_complete_data", label="Include Complete Data?"
    )

    def includes_complete_data(self, queryset, name, value):
        if value == "yes":
            queryset = queryset.select_related("school")
        return queryset

    class Meta:
        model = ChildSchoolCart
        fields = [
            "child",
        ]

class ChildSchoolApplicationFilter(filters.FilterSet):
    class Meta:
        model = SchoolApplication
        fields = [
            "child",
        ]

class CustomSchoolApplicationOrdering(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "total_points" for v in value):
                qs = qs.order_by("total_points")
            elif any(v == "-total_points" for v in value):
                qs = qs.order_by("-total_points")
            if any(v == "timestamp" for v in value):
                qs = qs.order_by("timestamp")
            elif any(v == "-timestamp" for v in value):
                qs = qs.order_by("-timestamp")
        return super().filter(qs, value)


class SchoolApplicationFilter(filters.FilterSet):
    ordering = CustomSchoolApplicationOrdering(
        fields=(
            ("total_points", "total_points"),
            ("timestamp", "timestamp")
        ),

        field_labels={
            "total_points": "Total Points",
            "timestamp": "Timestamp"
        }
    )
    start_date = filters.DateFilter(field_name='timestamp', lookup_expr='date__gte')
    end_date = filters.DateFilter(field_name='timestamp', lookup_expr='date__lte')
    child_name = filters.CharFilter(field_name = 'child__name',lookup_expr='icontains')
    session = CharInFilter(field_name = 'registration_data__session',lookup_expr='in')

    class Meta:
        model = SchoolApplication
        fields = [
            "apply_for",
            "child__name",
        ]

class SchoolChildCartItemFilter(filters.FilterSet):
    session = CharInFilter(field_name="session",lookup_expr="in")
    class Meta:
        model = ChildSchoolCart
        fields= [
            "session",
        ]
