from rest_framework import serializers

from experts.models import ExpertUserProfile


class ExperUserBasicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertUserProfile
        fields = [
            "id",
            "name",
            "profile_picture",
        ]


class ExpertUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertUserProfile
        lookup_field = "slug"
        fields = (
            "id",
            "name",
            "designation",
            "quote",
            "profile_picture",
            "slug",
            "bio",
        )
        extra_kwargs = {"url": {"lookup_field": "slug"}}
