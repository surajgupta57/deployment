from email.policy import default
from statistics import mode
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.validators import RegexValidator
from .utils import (
    sibling1_alumni_proof_upload_path,
    sibling2_alumni_proof_upload_path,
    transfer_certificate_upload_path,
    report_card_upload_path,
    family_photo_upload_path,
    distance_affidavit_upload_path,
    baptism_certificate_upload_path,
    parent_signature_upload_path,
    differently_abled_upload_path,
    non_collab_receipt_upload_path,
    single_parent_proof_upload_path,
    caste_category_certificate_upload_path,
    get_current_session,
)
from childs.utils import *
from parents.utils import *
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class CommonRegistrationForm(models.Model):
    CATEGORY = (("General", "General"), ("OBC", "OBC"), ("SC", "SC"), ("ST", "ST"))
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="user_admission_forms",
        blank=True,
        null=True,
    )
    father = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        related_name="father_admission_forms",
        blank=True,
        null=True,
    )
    mother = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        related_name="mother_admission_forms",
        blank=True,
        null=True,
    )
    guardian = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        related_name="guardian_admission_forms",
        blank=True,
        null=True,
    )
    child = models.OneToOneField(
        "childs.Child",
        on_delete=models.SET_NULL,
        related_name="child_admission_forms",
        blank=True,
        null=True,
    )
    short_address = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY, default="General")
    last_school_name = models.CharField(max_length=255, null=True, blank=True)
    last_school_board = models.ForeignKey(
        "schools.SchoolBoard", null=True, blank=True, on_delete=models.SET_NULL
    )
    last_school_address = models.CharField(max_length=255, null=True, blank=True)
    last_school_class = models.ForeignKey(
        "schools.SchoolClasses",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    transfer_certificate = models.FileField(
        upload_to=transfer_certificate_upload_path, blank=True, null=True
    )
    single_parent_proof = models.FileField(
        upload_to=single_parent_proof_upload_path, blank=True, null=True
    )
    reason_of_leaving = models.TextField(blank=True, null=True)
    report_card = models.FileField(
        upload_to=report_card_upload_path,
        blank=True,
        null=True,
    )
    extra_questions = JSONField(null=True, blank=True)
    last_school_result_percentage = models.DecimalField(
        max_digits=6, decimal_places=3, blank=True, null=True
    )

    transfer_number = models.CharField(
        verbose_name="Transfer Certificate SNo.", max_length=15, blank=True, null=True
    )
    transfer_date = models.DateField(blank=True, null=True)

    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    latitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    single_child = models.BooleanField(null=True, blank=True)
    first_child = models.BooleanField(null=True, blank=True)
    single_parent = models.BooleanField(null=True, blank=True)
    first_girl_child = models.BooleanField(null=True, blank=True)
    staff_ward = models.BooleanField(null=True, blank=True)

    sibling1_alumni_name = models.CharField(max_length=50, blank=True, null=True)
    sibling1_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="sibling1_school_name",
        on_delete=models.SET_NULL,
    )

    sibling2_alumni_name = models.CharField(max_length=50, blank=True, null=True)
    sibling2_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="sibling2_school_name",
        on_delete=models.SET_NULL,
    )
    sibling1_alumni_proof = models.FileField(
        upload_to=sibling1_alumni_proof_upload_path, blank=True, null=True
    )
    sibling2_alumni_proof = models.FileField(
        upload_to=sibling2_alumni_proof_upload_path, blank=True, null=True
    )

    family_photo = models.ImageField(
        upload_to=family_photo_upload_path, blank=True, null=True
    )

    distance_affidavit = models.FileField(
        upload_to=distance_affidavit_upload_path, blank=True, null=True
    )

    baptism_certificate = models.FileField(
        upload_to=baptism_certificate_upload_path, blank=True, null=True
    )

    parent_signature_upload = models.FileField(
        upload_to=parent_signature_upload_path, blank=True, null=True
    )

    mother_tongue = models.CharField(max_length=255, blank=True, null=True)

    differently_abled_proof = models.FileField(
        upload_to=differently_abled_upload_path, blank=True, null=True
    )
    caste_category_certificate = models.FileField(
        upload_to=caste_category_certificate_upload_path, blank=True, null=True
    )
    is_twins = models.BooleanField(null=True, blank=True)
    second_born_child = models.BooleanField(null=True, blank=True)
    third_born_child = models.BooleanField(null=True, blank=True)

    lockstatus = models.CharField(max_length=255, blank=True)
    transport_facility_required = models.BooleanField(
        default=False, null=True, blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    session = models.CharField(
        "Session",
        help_text="ex YYYY-YYYY",
        max_length=9,
        validators=[
            RegexValidator(
                regex="^.{9}$", message="Please Input Correct Format", code="nomatch"
            )
        ],
        default=get_current_session(),
        null=True,
        blank=True,
    )
    # father staff ward
    father_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="father_staff_ward_school",
        on_delete=models.SET_NULL,
    )
    father_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    father_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    father_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)
    # mother staff ward
    mother_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="mother_staff_ward_school",
        on_delete=models.SET_NULL,
    )
    mother_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    mother_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    mother_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)
    # guardian staff ward
    guardian_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="guardian_staff_ward_school",
        on_delete=models.SET_NULL,
    )
    guardian_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    guardian_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    guardian_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)

    @property
    def formatted_address(self):
        return f"{self.street_address}, {self.city} {self.pincode}, {self.state}"

    class Meta:
        verbose_name = "Common Registration Form"
        verbose_name_plural = "Common Registration Forms"

    def __str__(self):
        return self.child.name if self.child else ""


class ChildSchoolCart(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        limit_choices_to={"is_parent": True},
        on_delete=models.CASCADE,
        related_name="child_cart_user",
        blank=True,
        null=True,
    )
    child = models.ForeignKey(
        "childs.Child",
        on_delete=models.CASCADE,
        related_name="child_cart",
    )
    form = models.ForeignKey(
        "admission_forms.CommonRegistrationForm",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    school = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE)
    session = models.CharField(
        "Session",
        help_text="ex YYYY-YYYY",
        max_length=9,
        validators=[
            RegexValidator(
                regex="^.{9}$", message="Please Input Correct Format", code="nomatch"
            )
        ],
        default=get_current_session(),
        null=True,
        blank=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    form_price = models.IntegerField(default=0, null=True, blank=True)
    ad_source = models.CharField(max_length=100, blank=True, null=True)

    coupon_code = models.CharField(max_length=50,null=True,blank=True)
    discount = models.FloatField(default=0,null=True,blank=True)

    class Meta:
        unique_together = (("child", "school", "session"),)
        verbose_name = "Child School Cart Item"
        verbose_name_plural = "Child School Cart Items"

    def __str__(self):
        return self.child.name + " - " + self.school.name


class SchoolApplication(models.Model):
    apply_for = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.SET_NULL, blank=True, null=True
    )
    uid = models.CharField(max_length=70, default="", db_index=True)
    child = models.ForeignKey(
        "childs.Child",
        on_delete=models.SET_NULL,
        related_name="schools",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="forms",
        blank=True,
        null=True,
    )
    school = models.ForeignKey(
        "schools.SchoolProfile", on_delete=models.CASCADE, related_name="forms"
    )
    form = models.ForeignKey(
        "admission_forms.CommonRegistrationForm",
        on_delete=models.SET_NULL,
        related_name="common_reg_form",
        blank=True,
        null=True,
    )

    registration_data = models.ForeignKey(
        "admission_forms.CommonRegistrationFormAfterPayment",
        on_delete=models.SET_NULL,
        related_name="common_reg_form_after_payment",
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    calculated_distance = models.DecimalField(
        max_digits=10, decimal_places=5, blank=True, null=True
    )
    total_points = models.IntegerField(blank=True, null=True)
    distance_points = models.IntegerField(blank=True, null=True)
    single_child_points = models.IntegerField(blank=True, null=True)
    siblings_studied_points = models.IntegerField(blank=True, null=True)
    parents_alumni_points = models.IntegerField(blank=True, null=True)
    staff_ward_points = models.IntegerField(blank=True, null=True)
    first_born_child_points = models.IntegerField(blank=True, null=True)
    first_girl_child_points = models.IntegerField(blank=True, null=True)
    single_girl_child_points = models.IntegerField(blank=True, null=True)
    christian_points = models.IntegerField(blank=True, null=True)
    viewed = models.BooleanField(default=False, blank=True, db_index=True)
    girl_child_point = models.IntegerField(blank=True, null=False, default=0)
    single_parent_point = models.IntegerField(blank=True, null=False, default=0)
    minority_points = models.IntegerField(blank=True, null=False, default=0)
    student_with_special_needs_points = models.IntegerField(
        blank=True, null=False, default=0
    )
    children_of_armed_force_points = models.IntegerField(
        blank=True, null=False, default=0
    )
    transport_facility_points = models.IntegerField(blank=True, null=True, default=0)
    non_collab_receipt = models.FileField(
        upload_to=non_collab_receipt_upload_path, null=True, blank=True
    )
    father_covid_vacination_certifiacte_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    mother_covid_vacination_certifiacte_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    guardian_covid_vacination_certifiacte_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    mother_covid_19_frontline_warrior_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    father_covid_19_frontline_warrior_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    guardian_covid_19_frontline_warrior_points = models.IntegerField(
        blank=True, null=True, default=0
    )
    state_transfer_points = models.IntegerField(blank=True, null=True, default=0)
    ad_source = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(blank=True,null=True,max_length=100)
    order_id = models.CharField(blank=True,null=True,max_length=100)
    form_fee= models.FloatField(blank=True,null=True,default=0)
    convenience_fee=models.FloatField(blank=True,null=True,default=0)
    ezyschool_commission_percentage=models.FloatField(blank=True,null=True,default=0) # it can be any 
    school_settlement_amount= models.FloatField(blank=True,null=True,default=0) # after everything 
    ezyschool_commission=models.FloatField(blank=True,null=True,default=0) # actull amount after convenience %
    ezyschool_total_amount= models.FloatField(blank=True,null=True,default=0) # adding convenience fee + ezyshool_commission total
    coupon_code = models.CharField(blank=True,null=True,max_length=100)
    coupon_discount = models.FloatField(blank=True,null=True,default=0)
    coupon_applied_on = models.CharField(blank=True,null=True,max_length=100)
    
    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "School Application"
        verbose_name_plural = "School Applications"

    # def save(self, *args, **kwargs):
    #     flag = 0
    #     if self.school.id == 1697:
    #         start_value_form = SchoolApplication.objects.filter(school=self.school).count()
    #         base_start_value = 2001
    #         current_value = base_start_value + start_value_form
    #         self.uid = "N" + str(current_value) + "-22"
    #     else:
    #         cval = SchoolApplication.objects.filter(school=self.school).count() + self.school.count_start
    #         self.uid = "ezy_" + str(self.school.short_name) + "_" + str(cval)
    #
    #     super().save(*args, **kwargs)

    def __str__(self):
        return str(self.pk) + " - " + self.form.child.name + " - " + self.school.name


class CheckPoint(models.Model):
    form = models.ForeignKey(
        "admission_forms.CommonRegistrationForm",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name="check_point",
        blank=True,
        null=True,
    )
    schools_applied = models.ForeignKey(
        "admission_forms.SchoolApplication", on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.form.name + " - " + self.school.name


class FormReceipt(models.Model):
    receipt_id = models.CharField(max_length=70, db_index=True)
    school_applied = models.OneToOneField(
        "admission_forms.SchoolApplication",
        on_delete=models.CASCADE,
        related_name="receipt",
    )
    form_fee = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Form Receipt"
        verbose_name_plural = "Form Receipts"

    def __str__(self):
        return str(self.pk)


class ChildPointsPreference(models.Model):
    child = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="child_points",
    )
    single_child_points = models.BooleanField(blank=True, null=True)
    siblings_points = models.BooleanField(blank=True, null=True)
    parent_alumni_points = models.BooleanField(blank=True, null=True)
    staff_ward_points = models.BooleanField(blank=True, null=True)
    first_born_child_points = models.BooleanField(blank=True, null=True)
    first_girl_child_points = models.BooleanField(blank=True, null=True)
    single_girl_child_points = models.BooleanField(blank=True, null=True)
    is_christian_points = models.BooleanField(blank=True, null=True)
    girl_child_points = models.BooleanField(blank=True, null=True)
    single_parent_points = models.BooleanField(blank=True, null=True)
    minority_points = models.BooleanField(blank=True, null=True)
    student_with_special_needs_points = models.BooleanField(blank=True, null=True)
    children_of_armed_force_points = models.BooleanField(blank=True, null=True)
    transport_facility_points = models.BooleanField(blank=True, null=True)

    # Address Fields
    short_address = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    latitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Child Points Preference"
        verbose_name_plural = "Child Points Preferences"

    def __str__(self):
        return f"{self.child.name}"


class ChildPointsPreferenceSchoolWise(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile", on_delete=models.CASCADE, related_name="schools"
    )

    pref = models.ForeignKey(
        ChildPointsPreference, on_delete=models.CASCADE, related_name="pointspref"
    )

    total_points = models.IntegerField(blank=True, null=False, default=0)
    children_of_armed_force_points = models.IntegerField(
        blank=True, null=False, default=0
    )
    single_child_points = models.IntegerField(blank=True, null=False, default=0)
    siblings_points = models.IntegerField(blank=True, null=False, default=0)
    parent_alumni_points = models.IntegerField(blank=True, null=False, default=0)
    staff_ward_points = models.IntegerField(blank=True, null=False, default=0)
    first_born_child_points = models.IntegerField(blank=True, null=False, default=0)
    first_girl_child_points = models.IntegerField(blank=True, null=False, default=0)
    single_girl_child_points = models.IntegerField(blank=True, null=False, default=0)
    is_christian_points = models.IntegerField(blank=True, null=False, default=0)
    girl_child_points = models.IntegerField(blank=True, null=False, default=0)
    single_parent_points = models.IntegerField(blank=True, null=False, default=0)
    minority_points = models.IntegerField(blank=True, null=False, default=0)
    student_with_special_needs_points = models.IntegerField(
        blank=True, null=False, default=0
    )
    transport_facility_points = models.IntegerField(blank=True, null=False, default=0)
    distance_points = models.IntegerField(blank=True, null=False, default=0)

    class Meta:
        verbose_name = "Child Points School Preference"
        verbose_name_plural = "Child Points School Preferences"

    def __str__(self):
        return f"{self.school.name}"


class ApplicationStatus(models.Model):
    TYPE_CHOICES = (("C", "Collab"), ("N", "Non-Collab"))
    name = models.CharField(max_length=50)
    rank = models.IntegerField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="C")
    mail_content = models.TextField(blank=True, null=True)
    sms_content = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ApplicationStatusLog(models.Model):
    status = models.ForeignKey(
        "admission_forms.ApplicationStatus", on_delete=models.PROTECT
    )
    application = models.ForeignKey(
        "admission_forms.SchoolApplication",
        on_delete=models.CASCADE,
        related_name="status",
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status.name + " " + str(self.timestamp)


class CommonRegistrationFormAfterPayment(models.Model):
    CATEGORY = (("General", "General"), ("OBC", "OBC"), ("SC", "SC"), ("ST", "ST"))
    GENDER = (("male", "male"), ("female", "female"))
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="user_admission_forms_after_pay",
        blank=True,
        null=True,
    )
    # child_data
    child_name = models.CharField(max_length=150, null=True, blank=True)
    child_photo = models.ImageField(
        upload_to=child_profile_picture_upload_path, blank=True, null=True
    )
    child_date_of_birth = models.DateField(null=True, blank=True)
    child_gender = models.CharField(max_length=10, choices=GENDER, default="male")
    # child_slug = models.SlugField(unique=True, max_length=180,null=True)
    child_religion = models.CharField(max_length=255, blank=True, null=True)
    child_nationality = models.CharField(max_length=255, blank=True, null=True)
    child_aadhaar_number = models.CharField(max_length=16, blank=True, null=True)
    child_aadhaar_card_proof = models.FileField(
        upload_to=child_aadhar_card_path_upload_path, blank=True, null=True
    )
    child_blood_group = models.CharField(max_length=15, blank=True, null=True)
    child_birth_certificate = models.FileField(
        upload_to=child_birth_certificate_upload_path, blank=True, null=True
    )
    child_medical_certificate = models.FileField(
        upload_to=medical_fitness_certificate_upload_path, blank=True, null=True
    )
    child_address_proof = models.FileField(
        upload_to=address_proof_upload_path, blank=True, null=True
    )
    child_address_proof2 = models.FileField(
        upload_to=address_proof_upload_path, blank=True, null=True
    )
    child_first_child_affidavit = models.FileField(
        upload_to=first_child_affidavit_upload_path, blank=True, null=True
    )
    child_vaccination_card = models.FileField(
        upload_to=child_vaccination_card_upload_path, blank=True, null=True
    )
    child_minority_proof = models.FileField(
        upload_to=minority_proof_upload_path, blank=True, null=True
    )
    child_is_christian = models.BooleanField(null=True, blank=True)
    child_minority_points = models.BooleanField(null=True, blank=True)
    child_student_with_special_needs_points = models.BooleanField(null=True, blank=True)
    child_armed_force_points = models.BooleanField(null=True, blank=True)
    child_armed_force_proof = models.FileField(
        upload_to=child_armed_force_proof_upload_path, blank=True, null=True
    )
    child_orphan = models.BooleanField(null=True, blank=True)
    child_no_school = models.BooleanField(
        verbose_name="Doesn't attend school", default=False
    )
    child_class_applying_for = models.ForeignKey(
        "schools.SchoolClasses",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="child_applying_for_class",
    )
    child_intre_state_transfer = models.BooleanField(
        null=True, blank=True, default=False
    )
    child_illness = models.CharField(null=True, blank=True, max_length=50)
    # parent data father_
    father_email = models.EmailField(null=True, blank=True)
    father_name = models.CharField(max_length=150, null=True, blank=True)
    father_date_of_birth = models.DateField(null=True, blank=True)
    father_gender = models.CharField(max_length=10, choices=GENDER, default="male")

    father_photo = models.ImageField(
        upload_to=parent_profile_picture_upload_path, blank=True, null=True
    )
    father_companyname = models.CharField(max_length=150, blank=True, null=True)
    father_aadhaar_number = models.CharField(max_length=16, blank=True, null=True)
    father_transferable_job = models.BooleanField(blank=True, null=True)
    father_special_ground = models.BooleanField(blank=True, null=True)
    father_designation = models.CharField(max_length=50, blank=True, null=True)
    father_profession = models.CharField(max_length=50, blank=True, null=True)
    father_special_ground_proof = models.FileField(
        upload_to=parent_special_ground_proof, blank=True, null=True
    )
    father_parent_aadhar_card = models.FileField(
        upload_to=parent_addhar_card_path, blank=True, null=True
    )
    father_pan_card_proof = models.FileField(
        upload_to=parent_pan_card_path, blank=True, null=True
    )
    father_income = models.CharField(max_length=12, null=True, blank=True)
    father_phone = models.CharField(max_length=30, null=True, blank=True)
    father_bio = models.CharField(max_length=255, null=True, blank=True)
    father_parent_type = models.CharField(max_length=50, null=True, blank=True)
    father_street_address = models.CharField(max_length=250, blank=True, null=True)
    father_city = models.CharField(max_length=150, blank=True, null=True)
    father_state = models.CharField(max_length=100, blank=True, null=True)
    father_pincode = models.CharField(max_length=10, blank=True, null=True)
    father_country = models.CharField(max_length=150, blank=True, null=True)
    father_education = models.CharField(max_length=255, blank=True, null=True)
    father_occupation = models.CharField(max_length=255, blank=True, null=True)
    father_office_address = models.CharField(max_length=255, blank=True, null=True)
    father_office_number = models.CharField(max_length=15, blank=True, null=True)
    father_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="father_school_name",
        on_delete=models.SET_NULL,
    )
    father_alumni_year_of_passing = models.CharField(
        max_length=5, blank=True, null=True
    )
    father_passing_class = models.CharField(max_length=15, blank=True, null=True)
    father_alumni_proof = models.FileField(upload_to="images", blank=True, null=True)
    father_covid_vaccination_certificate = models.FileField(
        upload_to="images", blank=True, null=True
    )
    father_frontline_helper = models.BooleanField(null=True, blank=True, default=False)
    father_college_name = models.CharField(max_length=200, blank=True, null=True)
    father_course_name = models.CharField(max_length=200, blank=True, null=True)
    # parent data mother_
    mother_email = models.EmailField(null=True, blank=True)
    mother_name = models.CharField(max_length=150)
    mother_date_of_birth = models.DateField(null=True, blank=True)
    mother_gender = models.CharField(max_length=10, choices=GENDER, default="male")

    mother_photo = models.ImageField(
        upload_to=parent_profile_picture_upload_path, blank=True, null=True
    )
    mother_companyname = models.CharField(max_length=150, blank=True, null=True)
    mother_aadhaar_number = models.CharField(max_length=16, blank=True, null=True)
    mother_transferable_job = models.BooleanField(blank=True, null=True)
    mother_special_ground = models.BooleanField(blank=True, null=True)
    mother_designation = models.CharField(max_length=50, blank=True, null=True)
    mother_profession = models.CharField(max_length=50, blank=True, null=True)
    mother_special_ground_proof = models.FileField(
        upload_to=parent_special_ground_proof, blank=True, null=True
    )
    mother_parent_aadhar_card = models.FileField(
        upload_to=parent_addhar_card_path, blank=True, null=True
    )
    mother_pan_card_proof = models.FileField(
        upload_to=parent_pan_card_path, blank=True, null=True
    )
    mother_income = models.CharField(max_length=12, null=True, blank=True)
    mother_phone = models.CharField(max_length=30, null=True, blank=True)
    mother_bio = models.CharField(max_length=255, null=True, blank=True)
    mother_parent_type = models.CharField(max_length=50, null=True, blank=True)
    mother_street_address = models.CharField(max_length=250, blank=True, null=True)
    mother_city = models.CharField(max_length=150, blank=True, null=True)
    mother_state = models.CharField(max_length=100, blank=True, null=True)
    mother_pincode = models.CharField(max_length=10, blank=True, null=True)
    mother_country = models.CharField(max_length=150, blank=True, null=True)
    mother_education = models.CharField(max_length=255, blank=True, null=True)
    mother_occupation = models.CharField(max_length=255, blank=True, null=True)
    mother_office_address = models.CharField(max_length=255, blank=True, null=True)
    mother_office_number = models.CharField(max_length=15, blank=True, null=True)
    mother_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="mother_school_name",
        on_delete=models.SET_NULL,
    )
    mother_alumni_year_of_passing = models.CharField(
        max_length=5, blank=True, null=True
    )
    mother_passing_class = models.CharField(max_length=15, blank=True, null=True)
    mother_alumni_proof = models.FileField(upload_to="images", blank=True, null=True)
    mother_covid_vaccination_certificate = models.FileField(
        upload_to="images", blank=True, null=True
    )
    mother_frontline_helper = models.BooleanField(null=True, blank=True, default=False)
    mother_college_name = models.CharField(max_length=200, blank=True, null=True)
    mother_course_name = models.CharField(max_length=200, blank=True, null=True)
    # parent data guardian_
    guardian_email = models.EmailField(null=True, blank=True)
    guardian_name = models.CharField(max_length=150, null=True, blank=True)
    guardian_date_of_birth = models.DateField(null=True, blank=True)
    guardian_gender = models.CharField(max_length=10, choices=GENDER, default="male")

    guardian_photo = models.ImageField(
        upload_to=parent_profile_picture_upload_path, blank=True, null=True
    )
    guardian_companyname = models.CharField(max_length=150, blank=True, null=True)
    guardian_aadhaar_number = models.CharField(max_length=16, blank=True, null=True)
    guardian_transferable_job = models.BooleanField(blank=True, null=True)
    guardian_special_ground = models.BooleanField(blank=True, null=True)
    guardian_designation = models.CharField(max_length=50, blank=True, null=True)
    guardian_profession = models.CharField(max_length=50, blank=True, null=True)
    guardian_special_ground_proof = models.FileField(
        upload_to=parent_special_ground_proof, blank=True, null=True
    )
    guardian_parent_aadhar_card = models.FileField(
        upload_to=parent_addhar_card_path, blank=True, null=True
    )
    guardian_pan_card_proof = models.FileField(
        upload_to=parent_pan_card_path, blank=True, null=True
    )
    guardian_income = models.CharField(max_length=12, null=True, blank=True)
    guardian_phone = models.CharField(max_length=30, null=True, blank=True)
    guardian_bio = models.CharField(max_length=255, null=True, blank=True)
    guardian_parent_type = models.CharField(max_length=50, null=True, blank=True)
    guardian_street_address = models.CharField(max_length=250, blank=True, null=True)
    guardian_city = models.CharField(max_length=150, blank=True, null=True)
    guardian_state = models.CharField(max_length=100, blank=True, null=True)
    guardian_pincode = models.CharField(max_length=10, blank=True, null=True)
    guardian_country = models.CharField(max_length=150, blank=True, null=True)
    guardian_education = models.CharField(max_length=255, blank=True, null=True)
    guardian_occupation = models.CharField(max_length=255, blank=True, null=True)
    guardian_office_address = models.CharField(max_length=255, blank=True, null=True)
    guardian_office_number = models.CharField(max_length=15, blank=True, null=True)
    guardian_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="guardian_school_name",
        on_delete=models.SET_NULL,
    )
    guardian_alumni_year_of_passing = models.CharField(
        max_length=5, blank=True, null=True
    )
    guardian_passing_class = models.CharField(max_length=15, blank=True, null=True)
    guardian_alumni_proof = models.FileField(upload_to="images", blank=True, null=True)
    guardian_covid_vaccination_certificate = models.FileField(
        upload_to="images", blank=True, null=True
    )
    guardian_frontline_helper = models.BooleanField(
        null=True, blank=True, default=False
    )
    guardian_college_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_course_name = models.CharField(max_length=200, blank=True, null=True)
    # common reg form
    short_address = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY, default="General")
    last_school_name = models.CharField(max_length=255, null=True, blank=True)
    last_school_board = models.ForeignKey(
        "schools.SchoolBoard", null=True, blank=True, on_delete=models.SET_NULL
    )
    last_school_address = models.CharField(max_length=255, null=True, blank=True)
    last_school_class = models.ForeignKey(
        "schools.SchoolClasses",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    transfer_certificate = models.FileField(
        upload_to=transfer_certificate_upload_path, blank=True, null=True
    )
    single_parent_proof = models.FileField(
        upload_to=single_parent_proof_upload_path, blank=True, null=True
    )
    reason_of_leaving = models.TextField(blank=True, null=True)
    report_card = models.FileField(
        upload_to=report_card_upload_path,
        blank=True,
        null=True,
    )
    extra_questions = JSONField(null=True, blank=True)
    last_school_result_percentage = models.DecimalField(
        max_digits=6, decimal_places=3, blank=True, null=True
    )

    transfer_number = models.CharField(
        verbose_name="Transfer Certificate SNo.", max_length=15, blank=True, null=True
    )
    transfer_date = models.DateField(blank=True, null=True)

    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    latitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    longitude_secondary = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True
    )
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    single_child = models.BooleanField(null=True, blank=True)
    first_child = models.BooleanField(null=True, blank=True)
    single_parent = models.BooleanField(null=True, blank=True)
    first_girl_child = models.BooleanField(null=True, blank=True)
    staff_ward = models.BooleanField(null=True, blank=True)

    sibling1_alumni_name = models.CharField(max_length=50, blank=True, null=True)
    sibling1_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="sibling1_school_name_after_pay",
        on_delete=models.SET_NULL,
    )

    sibling2_alumni_name = models.CharField(max_length=50, blank=True, null=True)
    sibling2_alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="sibling2_school_name_after_pay",
        on_delete=models.SET_NULL,
    )
    sibling1_alumni_proof = models.FileField(
        upload_to=sibling1_alumni_proof_upload_path, blank=True, null=True
    )
    sibling2_alumni_proof = models.FileField(
        upload_to=sibling2_alumni_proof_upload_path, blank=True, null=True
    )

    family_photo = models.ImageField(
        upload_to=family_photo_upload_path, blank=True, null=True
    )

    distance_affidavit = models.FileField(
        upload_to=distance_affidavit_upload_path, blank=True, null=True
    )

    baptism_certificate = models.FileField(
        upload_to=baptism_certificate_upload_path, blank=True, null=True
    )

    parent_signature_upload = models.FileField(
        upload_to=parent_signature_upload_path, blank=True, null=True
    )

    mother_tongue = models.CharField(max_length=255, blank=True, null=True)

    differently_abled_proof = models.FileField(
        upload_to=differently_abled_upload_path, blank=True, null=True
    )
    caste_category_certificate = models.FileField(
        upload_to=caste_category_certificate_upload_path, blank=True, null=True
    )
    is_twins = models.BooleanField(null=True, blank=True)
    second_born_child = models.BooleanField(null=True, blank=True)
    third_born_child = models.BooleanField(null=True, blank=True)

    lockstatus = models.CharField(max_length=255, blank=True)
    transport_facility_required = models.BooleanField(
        default=False, null=True, blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    session = models.CharField(
        "Session",
        help_text="ex YYYY-YYYY",
        max_length=9,
        validators=[
            RegexValidator(
                regex="^.{9}$", message="Please Input Correct Format", code="nomatch"
            )
        ],
        default=get_current_session(),
        null=True,
        blank=True,
    )
    # father staff ward
    father_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="father_staff_ward_school_after_pay",
        on_delete=models.SET_NULL,
    )
    father_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    father_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    father_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)
    # mother staff ward
    mother_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="mother_staff_ward_school_after_pay",
        on_delete=models.SET_NULL,
    )
    mother_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    mother_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    mother_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)
    # guardian staff ward
    guardian_staff_ward_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="guardian_staff_ward_school_after_pay",
        on_delete=models.SET_NULL,
    )
    guardian_staff_ward_department = models.CharField(
        max_length=60, blank=True, null=True
    )
    guardian_type_of_staff_ward = models.CharField(max_length=60, blank=True, null=True)
    guardian_staff_ward_tenure = models.CharField(max_length=60, blank=True, null=True)

    @property
    def formatted_address(self):
        return f"{self.street_address}, {self.city} {self.pincode}, {self.state}"

    @property
    def child_age(self):
        current_year = timezone.now().date().year
        check_date = timezone.datetime(current_year, 3, 31).date()
        return relativedelta(check_date, self.child_date_of_birth)

    @property
    def child_age_str(self):
        total = self.child_age
        if total.__nonzero__():
            d = []
            if total.years > 0:
                d.append(f"{total.years} Years")
            if total.months > 0:
                d.append(f"{total.months} Months")
            if total.days > 0:
                d.append(f"{total.days} Days")
            return ", ".join(d)
        return None

    @property
    def father_age(self):
        if self.father_date_of_birth:
            return relativedelta(timezone.now().date(), self.father_date_of_birth).years
        else:
            return ""

    @property
    def mother_age(self):
        if self.mother_date_of_birth:
            return relativedelta(timezone.now().date(), self.mother_date_of_birth).years
        else:
            return ""

    @property
    def guardian_age(self):
        if self.guardian_date_of_birth:
            return relativedelta(
                timezone.now().date(), self.guardian_date_of_birth
            ).years
        else:
            return ""

    class Meta:
        verbose_name = "Registration Form data "
        verbose_name_plural = "Registration Forms data"
