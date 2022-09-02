from rest_framework import serializers
from courses.models import *


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "parent_name",
            "child_name",
            "course_name",
            "class_name",
            "phone",
            "email",
            "address"
        ]

    def create(self, validated_data):
        instance, _ = CourseEnrollment.objects.get_or_create(**validated_data)
        return instance

    def validate_parent_name(self, value):
        return value.title()

    def validate_course_name(self, value):
        return value.title()

    def validate_child_name(self, value):
        return value.title()


class CourseEnquirySerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseEnquiry
        fields = [
            "parent_name",
            "child_name",
            "class_name",
            "phone",
            "query"
        ]

    def validate_parent_name(self, value):
        return value.title()

    def validate_child_name(self, value):
        return value.title()


class CourseOrderCreateSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    amount = serializers.IntegerField()


class CourseTransactionSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    razorpay_payment_id = serializers.CharField()
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class CourseDemoClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDemoClassRegistration
        fields = [
            "parent_name",
            "child_name",
            "class_name",
            "phone",
            "email"
        ]

    def validate_parent_name(self, value):
        return value.title()

    def validate_child_name(self, value):
        return value.title()
