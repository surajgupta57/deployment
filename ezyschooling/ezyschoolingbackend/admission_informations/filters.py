from django.db.models import Count
from django_filters import rest_framework as filters

from .models import (
            AdmissionInformationArticle,
            AdmissionInformationArticleComment,
            AdmissionInformationUserVideo,
            AdmissionInformationVideoComment,
            AdmissionInformationNews
        )
from core.filters import CharInFilter


class CustomArticleOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
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
                qs = qs.annotate(
                    children_comment_count=Count(
                        "user_admission_article_comment_childrens"
                    )
                )
                qs = qs.order_by("children_comment_count")
            elif any(v == "-children_comment_count" for v in value):
                qs = qs.annotate(
                    children_comment_count=Count(
                        "user_admission_article_comment_childrens"
                    )
                )
                qs = qs.order_by("-children_comment_count")
        return super().filter(qs, value)


class AdmissionInformationArticleFilter(filters.FilterSet):

    board = CharInFilter(field_name="board__slug", lookup_expr="in")

    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

    sub_category = CharInFilter(field_name="sub_category__slug", lookup_expr="in")

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

    ordering = CustomArticleOrderingFilter(
        fields=(
            ("timestamp", "timestamp"),
            ("likes_count", "likes_count"),
            ("comment_count", "comment_count"),
            ("views", "views"),
        ),
        field_labels={
            "timestamp": "TimeStamp",
            "views": "Article Views",
            "likes_count": "Article Liked Count",
            "comment_count": "Article Comment Count",
        },
    )

    class Meta:
        model = AdmissionInformationArticle
        fields = [
            "board",
            "sub_category",
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


class AdmissionInformationArticleCommentFilter(filters.FilterSet):
    article_id = filters.NumberFilter(field_name="article_id")
    expert_id = filters.NumberFilter(field_name="expert_id")
    parent_id = filters.NumberFilter(field_name="parent_id")

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
        model = AdmissionInformationArticleComment
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


class CustomVideoOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("likes_count")
            elif any(v == "-likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("-likes_count")
            if any(v == "comment_count" for v in value):
                qs = qs.annotate(comment_count=Count("video_comments"))
                qs = qs.order_by("comment_count")
            elif any(v == "-comment_count" for v in value):
                qs = qs.annotate(comment_count=Count("video_comments"))
                qs = qs.order_by("-comment_count")
        return super().filter(qs, value)


class AdmissionInformationUserVideoFilter(filters.FilterSet):

    board = CharInFilter(field_name="board__slug", lookup_expr="in")

    category = CharInFilter(field_name="category__slug", lookup_expr="in")

    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

    sub_category = CharInFilter(field_name="sub_category__slug", lookup_expr="in")

    expert = CharInFilter(field_name="expert__slug", lookup_expr="in")

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

    ordering = CustomVideoOrderingFilter(
        fields=(
            ("timestamp", "timestamp"),
            ("likes_count", "likes_count"),
            ("comment_count", "comment_count"),
            ("views", "views"),
        ),
        field_labels={
            "timestamp": "TimeStamp",
            "views": "Video Views",
            "likes_count": "Video Liked Count",
            "comment_count": "Video Comment Count",
        },
    )

    class Meta:
        model = AdmissionInformationUserVideo
        fields = [
            "board",
            "category",
            "sub_category",
            "expert",
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


class CustomVideoCommentOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if value is not None:
            if any(v == "likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("likes_count")
            elif any(v == "-likes_count" for v in value):
                qs = qs.annotate(likes_count=Count("likes"))
                qs = qs.order_by("-likes_count")
            if any(v == "children_comment_count" for v in value):
                qs = qs.annotate(
                    children_comment_count=Count("user_admission_video_comment_childrens")
                )
                qs = qs.order_by("children_comment_count")
            elif any(v == "-children_comment_count" for v in value):
                qs = qs.annotate(
                    children_comment_count=Count("user_admission_video_comment_childrens")
                )
                qs = qs.order_by("-children_comment_count")
        return super().filter(qs, value)


class AdmissionInformationVideoCommentFilter(filters.FilterSet):
    video_id = filters.NumberFilter(field_name="video_id")
    expert_id = filters.NumberFilter(field_name="expert_id")
    parent_id = filters.NumberFilter(field_name="parent_id")

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

    ordering = CustomVideoCommentOrderingFilter(
        fields=(
            ("id", "id"),
            ("likes_count", "likes_count"),
            ("children_comment_count", "children_comment_count"),
        ),
        field_labels={
            "id": "Comment Created",
            "likes_count": "Video Liked Count",
            "children_comment_count": "Video Comment Count",
        },
    )

    class Meta:
        model = AdmissionInformationVideoComment
        fields = [
            "video_id",
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


class AdmissionInformationNewsFilter(filters.FilterSet):

    board = CharInFilter(field_name="board__slug", lookup_expr="in")

    tags = CharInFilter(field_name="tags__slug", lookup_expr="in")

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

    ordering = filters.OrderingFilter(
        fields=(("timestamp", "timestamp"), ("views", "views"),),
        field_labels={"timestamp": "TimeStamp", "views": "Video Views",},
    )

    class Meta:
        model = AdmissionInformationNews
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
