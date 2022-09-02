from rest_auth.registration.serializers import SocialLoginSerializer
from rest_framework import serializers

from accounts.models import Token, User
from parents.api.v1.serializers import *


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model.
    """

    class Meta:
        model = Token
        fields = ("key",)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "is_parent",
            "is_expert",
            "is_brand",
            "current_child",
            "name",
            "current_parent",
            'is_active'
        ]
        read_only_fields = ["id", "email"]


class CustomSocialLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    is_uniform_app = serializers.BooleanField(default=False)
    is_facebook_user = serializers.BooleanField(default=False)
    email = serializers.EmailField()
