from django_filters import rest_framework as filters
from django.db.models import Count, F

from core.filters import CharInFilter
from news.models import News


class CustomNewsOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "views_count" for v in value):
                qs = qs.annotate(views_count=F("views")+Count("visits"))
                qs = qs.order_by("views_count")
            elif any(v == "-views_count" for v in value):
                qs = qs.annotate(views_count=F("views")+Count("visits"))
                qs = qs.order_by("-views_count")
        return super().filter(qs, value)


class NewsFilter(filters.FilterSet):

    board = CharInFilter(field_name="board__slug", lookup_expr="in")

    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

    timestamp_gte = filters.DateTimeFilter(
        field_name="timestamp", lookup_expr='gte')
    timestamp_lt = filters.DateTimeFilter(
        field_name="timestamp", lookup_expr='lt')

    year_created = filters.NumberFilter(
        field_name="timestamp", lookup_expr="year")
    year_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="year__gte")
    year_created_lt = filters.NumberFilter(
        field_name="timestamp", lookup_expr="year__lt")

    day_created = filters.NumberFilter(
        field_name="timestamp", lookup_expr="day")
    day_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="day__gte")
    day_created_lt = filters.NumberFilter(
        field_name="timestamp", lookup_expr="day__lt")

    month_created = filters.NumberFilter(
        field_name="timestamp", lookup_expr="month")
    month_created_gte = filters.NumberFilter(
        field_name="timestamp", lookup_expr="month__gte")
    month_created_lt = filters.NumberFilter(
        field_name="timestamp", lookup_expr="month__lt")

    ordering = CustomNewsOrderingFilter(
        fields=(
            ("timestamp", "timestamp"),
            ("views", "views"),
            ("views_count", "views_count")
        ),

        field_labels={
            "timestamp": "TimeStamp",
            "views": "Views",
            "views_count": "View Count"
        }
    )

    class Meta:
        model = News
        fields = [
            "board",
            "tags",
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
        ]
