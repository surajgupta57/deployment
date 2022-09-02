from django.db.models import Count
from django_filters import rest_framework as filters

from core.filters import CharInFilter
from miscs.models import Carousel, FaqQuestion, OnlineEvent


class CarouselFilter(filters.FilterSet):

    category = CharInFilter(
        field_name="category__slug", lookup_expr="in")

    class Meta:
        model = Carousel
        fields = [
            "category"
        ]


class OnlineEventFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            "event_date", "event_date"
        ),

        field_labels={
            "event_date": "Event Date"
        }
    )

    class Meta:
        model = OnlineEvent
        fields = ["ordering"]


class FaqQuestionFilter(filters.FilterSet):
    category = CharInFilter(field_name="category__slug", lookup_expr="in")
    region = filters.CharFilter(field_name="region__slug", lookup_expr="exact")
    city = filters.CharFilter(field_name="city__slug", lookup_expr="exact")
    district = CharInFilter(field_name="district__slug", lookup_expr="in")
    district_region = CharInFilter(field_name="district_region__slug", lookup_expr="in") 
    board = CharInFilter(field_name="board__slug", lookup_expr="in")
    school_type = CharInFilter(field_name="school_type__slug",lookup_expr="in")
    school_category = CharInFilter(field_name="school_category", lookup_expr="in")
    class_relation = CharInFilter(field_name="class_relation__slug", lookup_expr="in")
    is_popular = CharInFilter(field_name="popular", lookup_expr="in")
    class Meta:
        model = FaqQuestion
        fields = ["category","region","city","district","district_region","board","school_type","school_category","class_relation", "popular"]
