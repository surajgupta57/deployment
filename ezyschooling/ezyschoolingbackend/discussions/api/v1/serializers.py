import random

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from analatics.models import PageVisited
from categories.api.v1.serializers import (BoardSerializer,
                                           SubCategorySerializer)
from categories.models import Board, SubCategory
from discussions.models import Discussion, DiscussionComment
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from parents.api.v1.serializers import ParentArticleProfileSerializer
from tags.api.v1.serializers import TaggitSerializer, TagListSerializerField


class DiscussionListSerializer(TaggitSerializer, serializers.ModelSerializer):

    board = BoardSerializer()
    sub_category = SubCategorySerializer()
    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()
    views = serializers.SerializerMethodField()

    class Meta:
        model = Discussion
        fields = [
            "id",
            "title",
            "slug",
            "board",
            "sub_category",
            "parent",
            "expert",
            "views",
            "anonymous_user",
            "timestamp",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "likes_count"):
            response["likes_count"] = instance.likes_count
        if hasattr(instance, "comment_count"):
            response["comment_count"] = instance.comment_count
        return response

    def get_views(self, instance):
        return instance.views


class DiscussionSerializer(DiscussionListSerializer):

    tags = TagListSerializerField()

    class Meta:
        model = Discussion
        fields = [
            "id",
            "title",
            "slug",
            "board",
            "description",
            "sub_category",
            "parent",
            "expert",
            "anonymous_user",
            "views",
            "timestamp",
            "tags",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if (
            self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            response["like_status"] = instance.like_status
            if self.context["request"].user.is_parent:
                response["bookmark_status"] = instance.bookmark_status
        return response


class DiscussionCreateSerializer(TaggitSerializer, serializers.ModelSerializer):

    tags = TagListSerializerField()
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.filter(active=True)
    )
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.filter(active=True)
    )

    class Meta:
        model = Discussion
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "board",
            "sub_category",
            "anonymous_user",
            "tags",
        ]
        read_only_fields = ["slug"]


class DiscussionCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscussionComment
        fields = [
            "id",
            "comment",
            "discussion",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = ["id", "discussion",
                            "timestamp", "parent", "expert"]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "parent"):
            if instance.parent:
                response["parent"] = ParentArticleProfileSerializer(
                    instance.parent
                ).data
        if hasattr(instance, "expert"):
            if instance.expert:
                response["expert"] = ExperUserBasicProfileSerializer(
                    instance.expert
                ).data
        return response


class DiscussionCommentSerializer(serializers.ModelSerializer):

    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = DiscussionComment
        fields = [
            "id",
            "comment",
            "discussion",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "likes_count"):
            response["likes_count"] = instance.likes_count
        if hasattr(instance, "children_comment_count"):
            response["children_comment_count"] = instance.children_comment_count
        if (
            "request" in self.context
            and self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            response["like_status"] = instance.like_status
        return response


class DiscussionThreadCommentCreateSerializer(DiscussionCommentCreateSerializer):
    class Meta:
        model = DiscussionComment
        fields = [
            "id",
            "comment",
            "discussion",
            "parent_comment",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = [
            "id",
            "discussion",
            "timestamp",
            "parent",
            "expert",
            "parent_comment",
        ]


class DiscussionNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discussion
        fields = [
            "id",
            "title",
            "slug",
        ]


class DiscussionCommentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscussionComment
        fields = [
            "id",
            "comment",
            "discussion",
            "timestamp",
        ]
