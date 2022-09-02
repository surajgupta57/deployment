from rest_framework import serializers

from admission_informations.models import AdmissionInformationArticle, AdmissionInformationArticleComment
from categories.api.v1.serializers import (BoardSerializer,
                                           SubCategorySerializer)
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from parents.api.v1.serializers import ParentArticleProfileSerializer
from tags.api.v1.serializers import TaggitSerializer, TagListSerializerField


class AdmissionInformationArticleListSerializer(serializers.ModelSerializer):

    board = BoardSerializer()
    sub_category = SubCategorySerializer()
    created_by = ExperUserBasicProfileSerializer()

    class Meta:
        model = AdmissionInformationArticle
        fields = [
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "slug",
            "board",
            "sub_category",
            "created_by",
            "views",
            "timestamp",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "likes_count"):
            response["likes_count"] = instance.likes_count
        if hasattr(instance, "comment_count"):
            response["comment_count"] = instance.comment_count
        return response


class AdmissionInformationArticleSerializer(TaggitSerializer, AdmissionInformationArticleListSerializer):

    tags = TagListSerializerField()

    class Meta:
        model = AdmissionInformationArticle
        fields = [
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "slug",
            "board",
            "description",
            "sub_category",
            "created_by",
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


class AdmissionInformationArticleCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationArticleComment
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


class AdmissionInformationArticleCommentSerializer(serializers.ModelSerializer):

    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = AdmissionInformationArticleComment
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


class AdmissionInformationArticleThreadCommentCreateSerializer(AdmissionInformationArticleCommentCreateSerializer):
    class Meta:
        model = AdmissionInformationArticleComment
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


class AdmissionInformationArticleNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationArticle
        fields = [
            "id",
            "mini_title",
            "title",
            "thumbnail",
            "slug",
        ]


class AdmissionInformationArticleCommentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationArticleComment
        fields = [
            "id",
            "comment",
            "article",
            "timestamp",
        ]
