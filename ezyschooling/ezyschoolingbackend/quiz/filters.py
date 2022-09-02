from django_filters import rest_framework as filters

from core.filters import CharInFilter
from quiz.models import *


class QuizFilter(filters.FilterSet):

    category = CharInFilter(field_name="category__slug", lookup_expr="in")

    slug = CharInFilter(
        field_name="slug", lookup_expr="in")

    created_gte = filters.DateTimeFilter(
        field_name="created", lookup_expr='gte')
    created_lt = filters.DateTimeFilter(field_name="created", lookup_expr='lt')

    year_created = filters.NumberFilter(
        field_name="created", lookup_expr="year")
    year_created_gte = filters.NumberFilter(
        field_name="created", lookup_expr="year__gte")
    year_created_lt = filters.NumberFilter(
        field_name="created", lookup_expr="year__lt")

    day_created = filters.NumberFilter(field_name="created", lookup_expr="day")
    day_created_gte = filters.NumberFilter(
        field_name="created", lookup_expr="day__gte")
    day_created_lt = filters.NumberFilter(
        field_name="created", lookup_expr="day__lt")

    month_created = filters.NumberFilter(
        field_name="created", lookup_expr="month")
    month_created_gte = filters.NumberFilter(
        field_name="created", lookup_expr="month__gte")
    month_created_lt = filters.NumberFilter(
        field_name="created", lookup_expr="month__lt")

    ordering = filters.OrderingFilter(
        fields=(("created", "created"),), field_labels={"created": "Timestamp", }
    )

    include_question = filters.CharFilter(
        method="include_questions", label="Include Questions?")

    def include_questions(self, queryset, name, value):
        if value == "yes":
            queryset = queryset.get_include_question()
        return queryset

    class Meta:
        model = Quiz
        fields = [
            "category",
            "slug",

            "created_gte",
            "created_lt",
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


class QuizTakerFilter(filters.FilterSet):

    quiz = CharInFilter(field_name="quiz__slug", lookup_expr="in")

    class Meta:
        model = QuizTakers
        fields = [
            "quiz",
        ]


class QuizCategoryFilter(filters.FilterSet):

    places = CharInFilter(
        field_name="places__slug", lookup_expr="in")

    slug = CharInFilter(
        field_name="slug", lookup_expr="in")

    class Meta:
        model = QuizCategory
        fields = [
            "places",
            "slug",
            "is_featured"
        ]
