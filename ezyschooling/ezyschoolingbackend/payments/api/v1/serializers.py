from rest_framework import serializers
from payments.models import AdmissionGuidanceProgrammeFormOrder


class CaptureTransactionSerializer(serializers.Serializer):

    child_id = serializers.IntegerField()
    form_id = serializers.IntegerField()
    razorpay_payment_id = serializers.CharField()
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

class CaptureAdmissionGuidanceProgrammeTransactionSerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField()
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

class CaptureAdmissionGuidanceTransactionSerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField()
    razorpay_order_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

class AdmissionGuidanceProgrammeOrderSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = AdmissionGuidanceProgrammeFormOrder
        fields = [
            "name",
            "email",
            "package_name",
        ]
