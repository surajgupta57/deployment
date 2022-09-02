from notifications.models import Notification
from rest_framework import serializers

from .fields import GenericNotificationRelatedField


class NotificationSerializer(serializers.ModelSerializer):
    actor = GenericNotificationRelatedField(read_only=True)
    unread = serializers.BooleanField(read_only=True)
    target = GenericNotificationRelatedField(read_only=True)
    action_object = GenericNotificationRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "action_object",
            "unread",
            "target",
            "verb",
            "timestamp",
        ]
