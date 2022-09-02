import random

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from analatics.models import PageVisited
from articles.models import ExpertArticle, ExpertArticleComment
from categories.api.v1.serializers import (BoardSerializer,
                                           SubCategorySerializer, PopUpCategorySerializer)
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from parents.api.v1.serializers import ParentArticleProfileSerializer
from tags.api.v1.serializers import (FeaturedTagSerializer, TaggitSerializer,
                                     TagListSerializerField)


class ExpertArticleListSerializer(serializers.ModelSerializer):

    board = BoardSerializer()
    sub_category = SubCategorySerializer()
    created_by = ExperUserBasicProfileSerializer()
    views = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    popup_category = PopUpCategorySerializer()
    class Meta:
        model = ExpertArticle
        fields = [
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "thumb_desc",
            "slug",
            "board",
            "sub_category",
            "created_by",
            "popup_category",
            "views",
            "timestamp",
            "comment_counts",
            "like_counts",
            "comment_count",
            "like_count",
        ]

    def get_views(self, instance):
        return instance.views

    def get_comment_count(self, instance):
        return instance.comment_counts

    def get_like_count(self, instance):
        return instance.like_counts


class FeaturedExpertArticleListSerializer(ExpertArticleListSerializer):

    class Meta:
        model = ExpertArticle
        fields = [
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "thumb_desc",
            "slug",
            "board",
            "sub_category",
            "created_by",
            "views",
            "popup_category",
            "timestamp",
            "comment_counts",
            "like_counts",
            "comment_count",
            "like_count",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["featured_tag"] = FeaturedTagSerializer(
            instance.tags.get(featured=True)).data
        return response


class ExpertArticleSerializer(TaggitSerializer, ExpertArticleListSerializer):

    tags = TagListSerializerField()

    class Meta:
        model = ExpertArticle
        fields = [
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "thumb_desc",
            "meta_desc",
            "slug",
            "board",
            "audio_file",
            "description",
            "sub_category",
            "created_by",
            "views",
            "popup_category",
            "timestamp",
            "tags",
            "comment_counts",
            "like_counts",
            "comment_count",
            "like_count",
        ]

    def to_internal_value(self, data):
        print(data.description, flush=True)
        print(dir(data), flush=True)
        return super().to_internal_value(data)

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


class ExpertArticleCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertArticleComment
        fields = [
            "id",
            "comment",
            "article",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = ["id", "article", "timestamp", "parent", "expert"]

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


class ExpertArticleCommentSerializer(serializers.ModelSerializer):

    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = ExpertArticleComment
        fields = [
            "id",
            "comment",
            "article",
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


class ExpertArticleThreadCommentCreateSerializer(
        ExpertArticleCommentCreateSerializer):
    class Meta:
        model = ExpertArticleComment
        fields = [
            "id",
            "comment",
            "article",
            "parent_comment",
            "timestamp",
            "parent",
            "expert",
            "anonymous_user",
        ]
        read_only_fields = [
            "id",
            "article",
            "timestamp",
            "parent",
            "expert",
            "parent_comment",
        ]


class ExpertArticleNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertArticle
        fields = [
            "id",
            "mini_title",
            "title",
            "thumbnail",
            "slug",
        ]


class ExpertArticleCommentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertArticleComment
        fields = [
            "id",
            "comment",
            "article",
            "timestamp",
        ]
