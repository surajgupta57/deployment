from rest_framework import serializers

from categories.api.v1.serializers import (BoardSerializer,
                                           SubCategorySerializer)
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from parents.api.v1.serializers import ParentArticleProfileSerializer
from tags.api.v1.serializers import TaggitSerializer, TagListSerializerField
from admission_informations.models import AdmissionInformationUserVideo, AdmissionInformationVideoComment


class AdmissionInformationUserVideoListSerializer(TaggitSerializer, serializers.ModelSerializer):

    board = BoardSerializer()
    sub_category = SubCategorySerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = AdmissionInformationUserVideo
        fields = [
            "id",
            "title",
            "url",
            "slug",
            "board",
            "sub_category",
            "expert",
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


class AdmissionInformationUserVideoSerializer(AdmissionInformationUserVideoListSerializer):

    tags = TagListSerializerField()

    class Meta:
        model = AdmissionInformationUserVideo
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


class AdmissionInformationVideoCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationVideoComment
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


class AdmissionInformationVideoCommentSerializer(serializers.ModelSerializer):

    parent = ParentArticleProfileSerializer()
    expert = ExperUserBasicProfileSerializer()

    class Meta:
        model = AdmissionInformationVideoComment
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


class AdmissionInformationVideoThreadCommentCreateSerializer(AdmissionInformationVideoCommentCreateSerializer):
    class Meta:
        model = AdmissionInformationVideoComment
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


class AdmissionInformationUserVideoNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationUserVideo
        fields = [
            "id",
            "title",
            "url",
            "slug",
        ]


class AdmissionInformationUserVideoCommentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationVideoComment
        fields = [
            "id",
            "comment",
            "video",
            "timestamp",
        ]
