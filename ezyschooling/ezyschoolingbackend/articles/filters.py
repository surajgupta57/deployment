from django.db.models import Count, F
from django_filters import rest_framework as filters

from articles.models import ExpertArticle, ExpertArticleComment
from core.filters import CharInFilter


class CustomArticleOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "views_count" for v in value):
                qs = qs.annotate(views_count=F("views")+Count("visits"))
                qs = qs.order_by("views_count")
            elif any(v == "-views_count" for v in value):
                qs = qs.annotate(views_count=F("views")+Count("visits"))
                qs = qs.order_by("-views_count")
            if any(v == "likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("likes_count")
            elif any(v == "-likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("-likes_count")
            if any(v == "comment_count" for v in value):
                qs = qs.annotate(comment_count=Count("article_comments"))
                qs = qs.order_by("comment_count")
            elif any(v == "-comment_count" for v in value):
                qs = qs.annotate(comment_count=Count("article_comments"))
                qs = qs.order_by("-comment_count")
        return super().filter(qs, value)


class CustomArticleCommentOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("likes_count")
            elif any(v == "-likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("-likes_count")
            if any(v == "children_comment_count" for v in value):
                qs = qs.annotate(children_comment_count=Count(
                    "user_expert_article_comment_childrens"))
                qs = qs.order_by("children_comment_count")
            elif any(v == "-children_comment_count" for v in value):
                qs = qs.annotate(children_comment_count=Count(
                    "user_expert_article_comment_childrens"))
                qs = qs.order_by("-children_comment_count")
        return super().filter(qs, value)


class ExpertArticleFilter(filters.FilterSet):

    board = CharInFilter(field_name="board__slug", lookup_expr="in")

    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

    sub_category = CharInFilter(
        field_name="sub_category__slug", lookup_expr="in")

    created_by = CharInFilter(field_name="created_by__slug", lookup_expr="in")

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

    ordering = CustomArticleOrderingFilter(
        fields=(
            ("pinned", "Pinned"),
            ("timestamp", "timestamp"),
            ("likes_count", "likes_count"),
            ("comment_count", "comment_count"),
            ("views", "views"),
            ("views_count", "views_count")
        ),
        field_labels={
            "pinned": "Pinned",
            "timestamp": "TimeStamp",
            "views": "Article Views",
            "likes_count": "Article Liked Count",
            "comment_count": "Article Comment Count",
            "views_count": "Article View Count"
        }
    )

    class Meta:
        model = ExpertArticle
        fields = [
            "board",
            "sub_category",
            "popup_category",
            "created_by",
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


class ExpertArticleCommentFilter(filters.FilterSet):
    article_id = filters.NumberFilter(field_name="article_id")
    expert_id = filters.NumberFilter(field_name="expert_id")
    parent_id = filters.NumberFilter(field_name="parent_id")

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

    ordering = CustomArticleCommentOrderingFilter(
        fields=(
            ("id", "id"),
            ("likes_count", "likes_count"),
            ("children_comment_count", "children_comment_count"),
        ),
        field_labels={
            "id": "Comment Created",
            "likes_count": "Article Liked Count",
            "children_comment_count": "Article Comment Count",
        },
    )

    class Meta:
        model = ExpertArticleComment
        fields = [
            "article_id",
            "expert_id",
            "parent_id",
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
