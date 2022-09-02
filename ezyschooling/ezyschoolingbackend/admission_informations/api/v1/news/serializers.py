from rest_framework import serializers

from categories.api.v1.serializers import BoardSerializer
from admission_informations.models import AdmissionInformationNews, AdmissionInformationNewsHeadline
from tags.api.v1.serializers import TagListSerializerField


class AdmissionInformationNewsHeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInformationNewsHeadline
        fields = ["id", "title"]


class AdmissionInformationNewsSerializer(serializers.ModelSerializer):

    board = BoardSerializer()
    tags = TagListSerializerField()

    class Meta:
        model = AdmissionInformationNews
        fields = [
            "id",
            "title",
            "mini_title",
            "slug",
            "image",
            "views",
            "timestamp",
            "tags",
            "board",
        ]


class AdmissionInformationNewsDetailSerializer(AdmissionInformationNewsSerializer):

    headlines = AdmissionInformationNewsHeadlineSerializer(many=True)

    class Meta:
        model = AdmissionInformationNews
        fields = [
            "id",
            "title",
            "mini_title",
            "slug",
            "image",
            "content",
            "views",
            "timestamp",
            "tags",
            "board",
            "headlines",
        ]
