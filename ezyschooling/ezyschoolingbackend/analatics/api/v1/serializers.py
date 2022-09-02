from rest_framework import serializers
from analatics.models import ClickLogEntry


class PageVisitedSerializer(serializers.Serializer):
    path = serializers.CharField(required=False)
    object_slug = serializers.CharField(required=False)
    object_type = serializers.CharField(required=False)


class ClickLogEntrySerializer(serializers.ModelSerializer):
    object_slug = serializers.CharField(required=False)
    object_type = serializers.CharField(required=False)
    
    class Meta:
        model = ClickLogEntry
        fields = [
            "action_flag",
            "path",
            "action_message",
            "object_id",
            "object_slug",
            "object_type",
        ]