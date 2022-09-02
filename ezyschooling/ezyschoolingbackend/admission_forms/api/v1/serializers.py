from rest_framework import serializers

from admission_forms.models import *
from childs.api.v1.serializers import (ChildAdmissionFormSerialzer,
                                       ChildSerialzer)
from childs.models import Child
from schools.models import SchoolMultiClassRelation
from parents.api.v1.serializers import ParentProfileDetailSerializer
from parents.models import ParentProfile
from schools.api.v1.serializers import (SchoolClassesSerializer,
                                        SchoolFormApplicationProfileSerializer,
                                        SchoolPDFProfileSerializer,
                                        SchoolProfileCartSerializer,
                                        SchoolProfileSerializer)
from schools.utils import (default_required_admission_form_fields,
                           default_required_child_fields,
                           default_required_father_fields,
                           default_required_guardian_fields,
                           default_required_mother_fields)
import copy

class ChildSchoolCartIDSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChildSchoolCart
        fields = [
            "school_id",
        ]


class ChildSchoolCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChildSchoolCart
        fields = [
            "id",
            "child",
            "school",
            "session",
            "timestamp",
            "form_price",
            "coupon_code",
            # 'discount',
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["school"] = SchoolProfileCartSerializer(
            instance.school
        ).data
        response["after_applied_coupon"] = instance.discount
        return response


class CommonRegistrationFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonRegistrationForm
        fields = [
            "id",
            "father",
            "mother",
            "guardian",
            "child",
            "short_address",
            "street_address",
            "city",
            "state",
            "pincode",
            "country",
            "latitude",
            "longitude",
            "latitude_secondary",
            "longitude_secondary",
            "category",
            "email",
            "phone_no",
            "single_child",
            "first_child",
            "single_parent",
            "first_girl_child",
            "staff_ward",
            "sibling1_alumni_name",
            "sibling1_alumni_school_name",
            "sibling2_alumni_name",
            "sibling2_alumni_school_name",
            "sibling1_alumni_proof",
            "sibling2_alumni_proof",
            "last_school_name",
            "last_school_board",
            "last_school_address",
            "last_school_class",
            "reason_of_leaving",
            "extra_questions",
            "report_card",
            "last_school_result_percentage",
            "transport_facility_required",
            "transfer_certificate",
            "family_photo",
            "distance_affidavit",
            "baptism_certificate",
            "parent_signature_upload",
            "mother_tongue",
            "single_parent_proof",
            "differently_abled_proof",
            "caste_category_certificate",
            "is_twins",
            "second_born_child",
            "third_born_child",
            "transfer_number",
            "transfer_date",
            "lockstatus",
            "timestamp",
            "session",
            'father_staff_ward_school_name',
            'father_staff_ward_department',
            'father_type_of_staff_ward',
            'father_staff_ward_tenure',
            'mother_staff_ward_school_name',
            'mother_staff_ward_department',
            'mother_type_of_staff_ward',
            'mother_staff_ward_tenure',
            'guardian_staff_ward_school_name',
            'guardian_staff_ward_department',
            'guardian_type_of_staff_ward',
            'guardian_staff_ward_tenure',
        ]


class ChildSchoolApplySerializer(serializers.ModelSerializer):

    apply_for = serializers.IntegerField()

    class Meta:
        model = ChildSchoolCart
        fields = [
            "apply_for",
            "child",
            "school",
        ]


class ChildSchoolApplicationIDSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolApplication
        fields = [
            "school_id"
        ]


class SchoolReceiptSerializer(serializers.ModelSerializer):

    class Meta:
        model = FormReceipt
        fields = [
            "id",
            "receipt_id",
            "school_applied",
            "form_fee",
            "timestamp",
        ]

class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatus
        fields = [
            'id',
            'type',
            'rank',
            'name',
            'description',
        ]
        read_only_fields = (
            "id",
        )

class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    status = ApplicationStatusSerializer()
    class Meta:
        model = ApplicationStatusLog
        fields = [
            'status',
        ]
    def to_representation(self,instance):
        response = super().to_representation(instance)
        return response['status']

class ApplicationStatusLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusLog
        fields = [
            'status',
            'application',
        ]

class ParentReceiptListSerializer(serializers.ModelSerializer):
    receipt = SchoolReceiptSerializer()
    school = SchoolFormApplicationProfileSerializer()
    child = ChildAdmissionFormSerialzer(read_only=True)
    status = ApplicationStatusLogSerializer(many=True)

    class Meta:
        model = SchoolApplication
        fields = [
            "id",
            "receipt",
            "school",
            "apply_for",
            "child",
            "status",
            "total_points",
            "non_collab_receipt",
        ]
        read_only_fields = (
            "status",
        )

    def to_representation(self, instance):
        response = super().to_representation(instance)
        for cls in instance.school.class_relation.filter():
            multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(multi_class_relation__id=instance.child.class_applying_for.id).first()
            if multi_obj:
                if cls.id == instance.child.class_applying_for.id:
                    response["apply_for"] = instance.child.class_applying_for.name
                else:
                    response["apply_for"] = instance.child.class_applying_for.name + "/" + cls.name
            else:
                response["apply_for"] = instance.child.class_applying_for.name

        return response

class ParentApplicationStatusLogSerializer(serializers.ModelSerializer):
    status = ApplicationStatusLogSerializer(many=True)

    class Meta:
        model = SchoolApplication
        fields = [
            "status",
            "school",
        ]

    def to_representation(self,instance):
        response = super().to_representation(instance)
        response["school"] = instance.school.name
        return response

class ParentSchoolApplicationListSerializer(serializers.ModelSerializer):
    school = SchoolFormApplicationProfileSerializer()
    child = ChildAdmissionFormSerialzer(read_only=True)

    class Meta:
        model = SchoolApplication
        fields = ("id", "form", "school", "child")


class ChildFormSerializer(ChildSerialzer):
    class Meta:
        model = Child
        fields = [
            "name",
            "photo",
            "date_of_birth",
            "gender",
            "blood_group",
            "aadhaar_number",
            "religion",
            "nationality",
            "birth_certificate",
            "address_proof",
            "address_proof2",
            "first_child_affidavit",
            "minority_proof",
            "vaccination_card",
            "armed_force_proof",
            "aadhaar_card_proof",
            "is_christian",
            "minority_points",
            "student_with_special_needs_points",
            "armed_force_points",
            "orphan",
            "intre_state_transfer",
            "illness",
        ]


class ParentFormSerializer(ParentProfileDetailSerializer):
    class Meta:
        model = ParentProfile
        fields = [
            "name",
            "email",
            "date_of_birth",
            "photo",
            "income",
            "aadhaar_number",
            "companyname",
            "transferable_job",
            "special_ground",
            "designation",
            "profession",
            "special_ground_proof",
            "parent_aadhar_card",
            "pan_card_proof",
            "phone",
            "education",
            "occupation",
            "office_address",
            "office_number",
            "alumni_school_name",
            "alumni_year_of_passing",
            "passing_class",
            "alumni_proof",
            "covid_vaccination_certificate",
            "frontline_helper",
            'college_name',
            'course_name',
        ]


class CommonRegistrationFormDetailSerializer(serializers.ModelSerializer):
    child = ChildFormSerializer()
    father = ParentFormSerializer()
    mother = ParentFormSerializer()
    guardian = ParentFormSerializer()

    class Meta:
        model = CommonRegistrationForm
        exclude = ["timestamp", "user"]

class SchoolApplicationListSerializer(serializers.ModelSerializer):
    birth_certificate = serializers.SerializerMethodField()
    address_proof = serializers.SerializerMethodField()
    address_proof2= serializers.SerializerMethodField()
    status = ApplicationStatusLogSerializer(many=True)

    class Meta:
        model = SchoolApplication
        exclude = ["user", "school"]
        read_only_fields = (
            "status",
        )

    def get_birth_certificate(self, obj):
        if obj.child.birth_certificate:
            return obj.child.birth_certificate.url
        else:
            return None

    def get_address_proof(self, obj):
        if obj.child.address_proof:
            return obj.child.address_proof.url
        else:
            return None

    def get_address_proof2(self, obj):
        if obj.child.address_proof2:
            return obj.child.address_proof2.url
        else:
            return None

    def to_representation(self, instance):
        response = super().to_representation(instance)
        for cls in instance.school.class_relation.filter():
            multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cls.id).filter(multi_class_relation__id=instance.child.class_applying_for.id).first()
            if multi_obj:
                if cls.id == instance.child.class_applying_for.id:
                    response["apply_for"] = instance.child.class_applying_for.name
                else:
                    response["apply_for"] = instance.child.class_applying_for.name + "/" + cls.name
            else:
                response["apply_for"] = instance.child.class_applying_for.name
        response["child"] = instance.child.name
        return response


class SchoolApplicationDetailSerializer(SchoolApplicationListSerializer):
    form = CommonRegistrationFormDetailSerializer()
    status = ApplicationStatusLogSerializer(many=True)

    class Meta:
        model = SchoolApplication
        exclude = ["user", "school"]
        read_only_fields = (
            "status",
        )

    def to_representation(self, instance):
        response = super().to_representation(instance)
        user = self.context["request"].user
        school = instance.school

        # Logic that returns only the fields configured by the school in their dashboard
        # Common Reg Form Details
        d = []
        for i in response['form'].keys():
            if i not in school.required_admission_form_fields.keys():
                d.append(i)
        d = list(set(d) - set(['child', 'father', 'mother', 'guardian',
                               'street_address', 'short_address', 'pincode', 'city',  'state', 'country']))
        for i in d:
            if i in default_required_admission_form_fields().keys():
                response['form'].pop(i)

        # Child Details
        d = []
        for i in response['form']['child'].keys():
            if i not in school.required_child_fields.keys():
                d.append(i)
        d = list(set(d) - set(['name', 'photo', 'date_of_birth',
                               'gender', 'nationality', 'religion']))
        for i in d:
            if i in default_required_child_fields().keys():
                response['form']['child'].pop(i)

        # Parent Details - Father
        if response['form']['father']:
            d = []
            for i in response['form']['father'].keys():
                if i not in school.required_father_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_father_fields().keys():
                    response['form']['father'].pop(i)

        # Parent Details - Mother
        if response['form']['mother']:
            d = []
            for i in response['form']['mother'].keys():
                if i not in school.required_mother_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_mother_fields().keys():
                    response['form']['mother'].pop(i)

        # Parent Details - Guardian
        if response['form']['guardian']:
            d = []
            for i in response['form']['guardian'].keys():
                if i not in school.required_guardian_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_guardian_fields().keys():
                    response['form']['guardian'].pop(i)
        return response


class ChildPointsPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildPointsPreference
        fields = [
            "single_child_points",
            "siblings_points",
            "parent_alumni_points",
            "staff_ward_points",
            "first_born_child_points",
            "first_girl_child_points",
            "single_girl_child_points",
            "is_christian_points",
            "girl_child_points",
            "single_parent_points",
            "minority_points",
            "student_with_special_needs_points",
            "children_of_armed_force_points",
            "transport_facility_points",
            "short_address",
            "street_address",
            "city",
            "pincode",
            "latitude",
            "longitude",
            "latitude_secondary",
            "longitude_secondary",
            "state",
            "country",
        ]


class SchoolApplicationPDFSerializer(SchoolApplicationListSerializer):
    form = CommonRegistrationFormDetailSerializer()
    school = SchoolPDFProfileSerializer()

    class Meta:
        model = SchoolApplication
        exclude = ["user",]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        school = instance.school
        if(instance.form.last_school_board):
            response["last_school_board"] = instance.form.last_school_board.name
        if(instance.form.last_school_class):
            response["last_school_class"] = instance.form.last_school_class.name
        if(instance.form.sibling1_alumni_school_name):
            response['sibling1_alumni_school_name']= instance.form.sibling1_alumni_school_name.name
        if(instance.form.sibling2_alumni_school_name):
            response['sibling2_alumni_school_name']= instance.form.sibling2_alumni_school_name.name
        if (instance.form.child.first_child_affidavit):
            response['first_child_affidavit']=instance.form.child.first_child_affidavit.url
        if (instance.form.father):
            if (instance.form.father.alumni_school_name):
                response['father_alumni_school_name']=instance.form.father.alumni_school_name.name
        if (instance.form.mother):
            if (instance.form.mother.alumni_school_name):
                response['mother_alumni_school_name']=instance.form.mother.alumni_school_name.name
        if (instance.form.guardian):
            if (instance.form.guardian.alumni_school_name):
                response['guardian_alumni_school_name']=instance.form.guardian.alumni_school_name.name
        if (instance.form.child.minority_proof):
            response['minority_proof'] = instance.form.child.minority_proof.url
        if (instance.form.child.armed_force_proof):
            response['armed_force_proof'] = instance.form.child.armed_force_proof.url
        if (instance.form.child.aadhaar_card_proof):
            response['aadhaar_card_proof'] = instance.form.child.aadhaar_card_proof.url

        # Logic that returns only the fields configured by the school in their dashboard
        # Common Reg Form Details
        d = []
        for i in response['form'].keys():
            if i not in school.required_admission_form_fields.keys():
                d.append(i)
        d = list(set(d) - set(['school', 'child', 'father', 'mother', 'guardian',
                               'street_address', 'short_address', 'pincode', 'city',  'state', 'country']))
        for i in d:
            if i in default_required_admission_form_fields().keys():
                response['form'].pop(i)

        # Child Details
        d = []
        for i in response['form']['child'].keys():
            if i not in school.required_child_fields.keys():
                d.append(i)
        d = list(set(d) - set(['name', 'photo', 'date_of_birth',
                               'gender', 'nationality', 'religion']))
        for i in d:
            if i in default_required_child_fields().keys():
                response['form']['child'].pop(i)

        # Parent Details - Father
        if response['form']['father']:
            d = []
            for i in response['form']['father'].keys():
                if i not in school.required_father_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_father_fields().keys():
                    response['form']['father'].pop(i)
            response["form"]["father"]["date_of_birth"] = instance.form.father.date_of_birth.strftime("%d-%m-%Y")

        # Parent Details - Mother
        if response['form']['mother']:
            d = []
            for i in response['form']['mother'].keys():
                if i not in school.required_mother_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_mother_fields().keys():
                    response['form']['mother'].pop(i)
            response["form"]["mother"]["date_of_birth"] = instance.form.mother.date_of_birth.strftime("%d-%m-%Y")

        # Parent Details - Guardian
        if response['form']['guardian']:
            d = []
            for i in response['form']['guardian'].keys():
                if i not in school.required_guardian_fields.keys():
                    d.append(i)
            d = list(set(d) - set(["name", "email", "phone", "photo"]))
            for i in d:
                if i in default_required_guardian_fields().keys():
                    response['form']['guardian'].pop(i)
            response["form"]["guardian"]["date_of_birth"] = instance.form.guardian.date_of_birth.strftime("%d-%m-%Y")

        response["form"]["child"]["date_of_birth"] = instance.form.child.date_of_birth.strftime("%d-%m-%Y")
        return response





class CopyObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonRegistrationFormAfterPayment
        fields = [
            #child
            'child_name',
            'child_photo',
            'child_date_of_birth',
            'child_gender',
            'child_religion',
            'child_nationality',
            'child_aadhaar_number',
            'child_aadhaar_card_proof',
            'child_blood_group',
            'child_birth_certificate',
            'child_medical_certificate',
            'child_address_proof',
            'child_address_proof2',
            'child_first_child_affidavit',
            'child_vaccination_card',
            'child_minority_proof',
            'child_is_christian',
            'child_minority_points',
            'child_student_with_special_needs_points',
            'child_armed_force_points',
            'child_armed_force_proof',
            'child_orphan',
            'child_no_school',
            'child_class_applying_for',
            'father_email',
            'father_name',
            'father_date_of_birth',
            'father_gender',
            'father_photo',
            'father_companyname',
            'father_aadhaar_number',
            'father_transferable_job',
            'father_special_ground',
            'father_designation',
            'father_profession',
            'father_special_ground_proof',
            'father_parent_aadhar_card',
            'father_pan_card_proof',
            'father_income',
            'father_phone',
            'father_bio',
            'father_parent_type',
            'father_street_address',
            'father_city',
            'father_state',
            'father_pincode',
            'father_country',
            'father_education',
            'father_occupation',
            'father_office_address',
            'father_office_number',
            'father_alumni_school_name',
            'father_alumni_year_of_passing',
            'father_passing_class',
            'father_alumni_proof',
            'mother_email',
            'mother_name',
            'mother_date_of_birth',
            'mother_gender',
            'mother_photo',
            'mother_companyname',
            'mother_aadhaar_number',
            'mother_transferable_job',
            'mother_special_ground',
            'mother_designation',
            'mother_profession',
            'mother_special_ground_proof',
            'mother_parent_aadhar_card',
            'mother_pan_card_proof',
            'mother_income',
            'mother_phone',
            'mother_bio',
            'mother_parent_type',
            'mother_street_address',
            'mother_city',
            'mother_state',
            'mother_pincode',
            'mother_country',
            'mother_education',
            'mother_occupation',
            'mother_office_address',
            'mother_office_number',
            'mother_alumni_school_name',
            'mother_alumni_year_of_passing',
            'mother_passing_class',
            'mother_alumni_proof',
            'guardian_email',
            'guardian_name',
            'guardian_date_of_birth',
            'guardian_gender',
            'guardian_photo',
            'guardian_companyname',
            'guardian_aadhaar_number',
            'guardian_transferable_job',
            'guardian_special_ground',
            'guardian_designation',
            'guardian_profession',
            'guardian_special_ground_proof',
            'guardian_parent_aadhar_card',
            'guardian_pan_card_proof',
            'guardian_income',
            'guardian_phone',
            'guardian_bio',
            'guardian_parent_type',
            'guardian_street_address',
            'guardian_city',
            'guardian_state',
            'guardian_pincode',
            'guardian_country',
            'guardian_education',
            'guardian_occupation',
            'guardian_office_address',
            'guardian_office_number',
            'guardian_alumni_school_name',
            'guardian_alumni_year_of_passing',
            'guardian_passing_class',
            'guardian_alumni_proof',
            'short_address',
            'street_address',
            'city',
            'state',
            'pincode',
            'country',
            'category',
            'last_school_name',
            'last_school_board',
            'last_school_address',
            'last_school_class',
            'transfer_certificate',
            'single_parent_proof',
            'reason_of_leaving',
            'report_card',
            'extra_questions',
            'last_school_result_percentage',
            'transfer_number',
            'transfer_date',
            'latitude',
            'longitude',
            'latitude_secondary',
            'longitude_secondary',
            'email',
            'phone_no',
            'single_child',
            'first_child',
            'single_parent',
            'first_girl_child',
            'staff_ward',
            'sibling1_alumni_name',
            'sibling1_alumni_school_name',
            'sibling2_alumni_name',
            'sibling2_alumni_school_name',
            'sibling1_alumni_proof',
            'sibling2_alumni_proof',
            'family_photo',
            'distance_affidavit',
            'baptism_certificate',
            'parent_signature_upload',
            'mother_tongue',
            'differently_abled_proof',
            'caste_category_certificate',
            'is_twins',
            'second_born_child',
            'third_born_child',
            'lockstatus',
            'transport_facility_required',
            'timestamp',
            'session',
            'father_covid_vaccination_certificate',
            'mother_covid_vaccination_certificate',
            'guardian_covid_vaccination_certificate',
            'father_frontline_helper',
            'mother_frontline_helper',
            'guardian_frontline_helper',
            'child_intre_state_transfer',
            'child_illness',
            'father_college_name',
            'father_course_name',
            'mother_college_name',
            'mother_course_name',
            'guardian_college_name',
            'guardian_course_name',
            'father_staff_ward_school_name',
            'father_staff_ward_department',
            'father_type_of_staff_ward',
            'father_staff_ward_tenure',
            'mother_staff_ward_school_name',
            'mother_staff_ward_department',
            'mother_type_of_staff_ward',
            'mother_staff_ward_tenure',
            'guardian_staff_ward_school_name',
            'guardian_staff_ward_department',
            'guardian_type_of_staff_ward',
            'guardian_staff_ward_tenure',
        ]



class SchoolApplicationNewPDFSerializer(SchoolApplicationListSerializer):
    # form = CommonRegistrationFormDetailSerializer()
    school = SchoolPDFProfileSerializer()
    registration_data = CopyObjectSerializer()
    class Meta:
        model = SchoolApplication
        exclude = ["user",]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        school = instance.school
        registration_data = instance.registration_data
        lists=[]

        if instance.form.father:

            father_data=['father_name','father_email','father_phone','father_date_of_birth','father_photo']
            lists=lists+father_data

            if instance.school.required_father_fields:
               for i in  instance.school.required_father_fields.keys():
                    if i=="company_name":
                        lists.append("companyname")
                    if i == "aadhaar_card_number":
                        lists.append("father_aadhaar_number")
                    lists.append("father_"+str(i))

        if instance.form.mother:
            mother_data=['mother_name','mother_email','mother_phone','mother_date_of_birth','mother_photo']

            lists=lists+mother_data
            if instance.school.required_mother_fields:
               for i in  instance.school.required_mother_fields.keys():
                    if i=="company_name":
                       lists.append("companyname")
                    if i == "aadhaar_card_number":
                       lists.append("mother_aadhaar_number")
                    lists.append("mother_"+str(i))



        if instance.form.guardian:
            guardian_data=['guardian_name','guardian_email','guardian_phone','guardian_date_of_birth','guardian_photo']
            lists=lists+guardian_data
            if instance.school.required_guardian_fields:
               for i in  instance.school.required_guardian_fields.keys():
                    if i=="company_name":
                       lists.append("companyname")
                    if i == "aadhaar_card_number":
                       lists.append("guardian_aadhaar_number")
                    lists.append("guardian_"+str(i))

        if instance.form.child:
            child_data =['child_name','child_date_of_birth','child_photo','child_gender', 'child_nationality', 'child_religion']
            lists=lists+child_data
            if instance.school.required_child_fields:
                for i in  instance.school.required_child_fields.keys():
                    if i == "aadhaar_card_number":
                        lists.append("child_aadhaar_number")
                    lists.append("child_"+str(i))

        if instance.form:
            form_data=['school', 'child', 'father', 'mother', 'guardian',
                               'street_address', 'short_address', 'pincode', 'city',  'state', 'country', "session",'father_staff_ward_school_name','father_staff_ward_department','father_type_of_staff_ward','father_staff_ward_tenure','mother_staff_ward_school_name','mother_staff_ward_department','mother_type_of_staff_ward','mother_staff_ward_tenure','guardian_staff_ward_school_name','guardian_staff_ward_department','guardian_type_of_staff_ward','guardian_staff_ward_tenure',]
            lists=lists+form_data

            if instance.school.required_admission_form_fields:
                 for i in  instance.school.required_admission_form_fields.keys():
                        lists.append(i)


            # if instance.form.sibling1_alumni_school_name != instance.school.name:
            #         lists.remove('sibling1_alumni_school_name')
            #         lists.remove('sibling1_alumni_name')
            #         lists.remove('sibling1_alumni_proof')

            # if instance.form.sibling2_alumni_school_name != instance.school.name:
            #         lists.remove('sibling2_alumni_school_name')
            #         lists.remove('sibling2_alumni_name')
            #         lists.remove('sibling2_alumni_proof')



            # if instance.form.mother:
            #     if instance.form.mother.alumni_school_name != instance.school.name:
            #         lists.remove('mother_alumni_school_name')
            #         lists.remove('mother_passing_class')
            #         lists.remove('mother_alumni_proof')
            #         lists.remove('mother_alumni_year_of_passing')


            # if instance.form.guardian:
            #     if instance.form.guardian.alumni_school_name != instance.school.name:
            #         lists.remove('mother_alumni_school_name')
            #         lists.remove('mother_passing_class')
            #         lists.remove('mother_alumni_proof')
            #         lists.remove('mother_alumni_year_of_passing')




        copy_response = copy.deepcopy(response)
        for i in (response['registration_data'].keys()):
            if i not in lists:
                copy_response['registration_data'].pop(i)


        return copy_response
