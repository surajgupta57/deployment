from rest_framework import serializers
from webpush.models import *
from notification.models import DeviceRegistrationToken ,PushNotificationData

class SubscriptionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInfo
        exclude = ["id"]


class WebPushSerializer(serializers.ModelSerializer):
    group = serializers.CharField(max_length=255, required=False)
    subscription = SubscriptionInfoSerializer()

    class Meta:
        model = PushInformation
        fields = ["group", "subscription"]

    def create(self, validated_data):
        group_name = validated_data.pop("group", None)
        subs = validated_data.pop("subscription", None)

        subscription, created = SubscriptionInfo.objects.get_or_create(**subs)

        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)

        if group:
            push_info, created = PushInformation.objects.get_or_create(
                subscription=subscription, group=group)
        else:
            push_info, created = PushInformation.objects.get_or_create(
                subscription=subscription, user=self.context['request'].user
            )

        if self.context['request'].user.is_authenticated and push_info.user is None:
            push_info.user = self.context['request'].user
            push_info.save()

        return push_info

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["group"] = instance.group.name
        return response

class DeviceRegistrationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceRegistrationToken
        fields= '__all__'

class PushNotificationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationData
        fields= '__all__'
