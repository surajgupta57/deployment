import random

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from analatics.models import PageVisited
from categories.api.v1.serializers import BoardSerializer
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from news.models import News, NewsHeadline
from tags.api.v1.serializers import TaggitSerializer, TagListSerializerField


class NewsHeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsHeadline
        fields = ["id", "title"]


class NewsSerializer(serializers.ModelSerializer):

    board = BoardSerializer()
    tags = TagListSerializerField()
    views = serializers.SerializerMethodField()
    author = ExperUserBasicProfileSerializer()

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "mini_title",
            "author",
            "slug",
            "image",
            "thumb_desc",
            "views",
            "timestamp",
            "tags",
            "board",
        ]

    def get_views(self, instance):
        return instance.views


class NewsDetailSerializer(NewsSerializer):

    headlines = NewsHeadlineSerializer(many=True)

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "mini_title",
            "author",
            "slug",
            "image",
            "thumb_desc",
            "content",
            "views",
            "timestamp",
            "tags",
            "board",
            "headlines",
        ]
