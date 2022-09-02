from rest_framework import serializers
from newsletters.models import *


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        exclude = ["user", "id"]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "uuid",
            "email",
            "frequency",
            "group",
        ]

        extra_kwargs = {
            'uuid': {
                'read_only': True
            },
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.frequency:
            response["frequency"] = instance.get_frequency_display()
        response["group"] = instance.get_group_display()
        return response


class SubscriptionUpdateSerializer(SubscriptionSerializer):
    class Meta:
        model = Subscription
        fields = [
            "uuid",
            "email",
            "frequency",
            "group",
            "active"
        ]

        extra_kwargs = {
            'url': {'lookup_field': 'uuid'},
            'uuid': {
                'read_only': True
            },
            'frequency': {
                'read_only': True
            },
            'group': {
                'read_only': True
            },
            'email': {
                'read_only': True
            }
        }
