from rest_framework import serializers

from childs.models import Child
from core.utils import Base64ImageField


class ChildSerialzer(serializers.ModelSerializer):
    class_applying_for_slug = serializers.CharField(source='class_applying_for.slug', read_only=True)
    class Meta:
        model = Child
        fields = [
            "id",
            "user",
            "name",
            "slug",
            "photo",
            "date_of_birth",
            "gender",
            "blood_group",
            "aadhaar_number",
            "religion",
            "nationality",
            "birth_certificate",
            "medical_certificate",
            "aadhaar_card_proof",
            "address_proof",
            "address_proof2",
            "first_child_affidavit",
            "minority_proof",
            "vaccination_card",
            "armed_force_proof",
            "is_christian",
            "minority_points",
            "student_with_special_needs_points",
            "armed_force_points",
            "orphan",
            "no_school",
            "class_applying_for",
            "class_applying_for_slug",
            "intre_state_transfer",
            "illness",
        ]
        read_only_fields = ["id", "user", "slug", 'class_applying_for_slug']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if hasattr(instance, "current_child"):
            response["current_child"] = instance.current_child
        return response


class ChildAdmissionFormSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Child
        fields = [
            "id",
            "user",
            "name",
            "slug",
        ]
