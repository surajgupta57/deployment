import random

import requests
from bs4 import BeautifulSoup as bs  # importing BeautifulSoup
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from datetime import date
from analatics.models import PageVisited
from categories.api.v1.serializers import (BoardSerializer,
                                           SubCategorySerializer)
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from parents.api.v1.serializers import ParentArticleProfileSerializer
from tags.api.v1.serializers import TaggitSerializer, TagListSerializerField
from videos.models import ExpertUserVideo, ExpertVideoComment
from videos.utils import fetch_youtube_views

class ExpertUserVideoListSerializer(TaggitSerializer, serializers.ModelSerializer):

    board = BoardSerializer()
    sub_category = SubCategorySerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = ExpertUserVideo
        fields = [
            "id",
            "title",
            "url",
            "slug",
            "board",
            "sub_category",
            "expert",
            "timestamp",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "likes_count"):
            response["likes_count"] = instance.likes_count
        if hasattr(instance, "comment_count"):
            response["comment_count"] = instance.comment_count
        return response


class ExpertUserVideoSerializer(ExpertUserVideoListSerializer):

    tags = TagListSerializerField()
    views = serializers.SerializerMethodField()

    class Meta:
        model = ExpertUserVideo
        fields = [
            "id",
            "title",
            "url",
            "slug",
            "board",
            "description",
            "sub_category",
            "expert",
            "views",
            "timestamp",
            "tags",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if (
            "request" in self.context
            and self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            response["like_status"] = instance.like_status
            if self.context["request"].user.is_parent:
                response["bookmark_status"] = instance.bookmark_status
        return response

    def get_views(self, instance):
        today = date.today()
        if not instance.last_views_update:
            view_count = fetch_youtube_views(instance.url)
            instance.youtube_views = view_count
            instance.last_views_update = today
            instance.save()
        else:
            last_update_date = instance.last_views_update
            days_diff = today - last_update_date
            if days_diff.days >=7:
                view_count = fetch_youtube_views(instance.url)
                instance.youtube_views = view_count
                instance.last_views_update = today
                instance.save()
        return instance.views + instance.youtube_views


class ExpertVideoCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertVideoComment
        fields = [
            "id",
            "video",
            "comment",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = ["id", "video", "timestamp", "parent", "expert"]

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


class ExpertVideoCommentSerializer(serializers.ModelSerializer):

    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = ExpertVideoComment
        fields = [
            "id",
            "video",
            "comment",
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


class ExpertVideoThreadCommentCreateSerializer(ExpertVideoCommentCreateSerializer):
    class Meta:
        model = ExpertVideoComment
        fields = [
            "id",
            "video",
            "comment",
            "parent_comment",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = [
            "id",
            "video",
            "timestamp",
            "parent",
            "expert",
            "parent_comment",
        ]


class ExpertUserVideoNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertUserVideo
        fields = [
            "id",
            "title",
            "url",
            "slug",
        ]


class ExpertUserVideoCommentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertVideoComment
        fields = [
            "id",
            "comment",
            "video",
            "timestamp",
        ]
