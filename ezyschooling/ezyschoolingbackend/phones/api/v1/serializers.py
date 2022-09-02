from rest_framework import serializers

from phones.models import PhoneNumber


class PhoneNumberSerializer(serializers.ModelSerializer):
    number = serializers.CharField(min_length=10, max_length=10)

    class Meta:
        model = PhoneNumber
        fields = [
            "number",
        ]

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Invalid Phone Number provided")
        return value


class PhoneNumberOTPSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    number = serializers.CharField(max_length=10, min_length=10)

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Invalid Phone Number provided")
        return value
