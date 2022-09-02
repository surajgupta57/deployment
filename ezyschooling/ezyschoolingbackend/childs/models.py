from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from core.utils import unique_slug_generator_using_name

from .utils import (address_proof_upload_path,
                    child_birth_certificate_upload_path,
                    child_profile_picture_upload_path,
                    child_vaccination_card_upload_path,
                    first_child_affidavit_upload_path,
                    minority_proof_upload_path,
                    child_armed_force_proof_upload_path,
                    child_aadhar_card_path_upload_path,
                    medical_fitness_certificate_upload_path,
                    )


class Child(models.Model):
    GENDER = (("male", "male"), ("female", "female"))
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="user_childs"
    )
    name = models.CharField(max_length=150)
    photo = models.ImageField(
        upload_to=child_profile_picture_upload_path, blank=True, null=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER, default="male")
    timestamp = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, max_length=180)

    # for admission form
    religion = models.CharField(max_length=255, blank=True, null=True)
    nationality = models.CharField(max_length=255, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=16,blank=True,null=True)
    aadhaar_card_proof=  models.FileField(upload_to=child_aadhar_card_path_upload_path,blank=True,null=True)
    blood_group = models.CharField(max_length=15, blank=True, null=True)
    birth_certificate = models.FileField(
        upload_to=child_birth_certificate_upload_path, blank=True, null=True
    )
    medical_certificate = models.FileField(
        upload_to=medical_fitness_certificate_upload_path, blank=True, null=True
    )
    address_proof = models.FileField(
        upload_to=address_proof_upload_path, blank=True, null=True
    )
    address_proof2= models.FileField(
        upload_to=address_proof_upload_path, blank=True, null=True
    )
    first_child_affidavit = models.FileField(
        upload_to=first_child_affidavit_upload_path, blank=True, null=True
    )
    vaccination_card = models.FileField(
        upload_to=child_vaccination_card_upload_path, blank=True, null=True
    )
    minority_proof = models.FileField(
        upload_to=minority_proof_upload_path, blank=True, null=True
    )
    is_christian = models.BooleanField(null=True, blank=True)
    minority_points = models.BooleanField(null=True, blank=True)
    student_with_special_needs_points = models.BooleanField(
        null=True, blank=True)
    armed_force_points = models.BooleanField(null=True, blank=True)
    armed_force_proof=models.FileField(upload_to=child_armed_force_proof_upload_path, blank=True, null=True)
    orphan = models.BooleanField(null=True, blank=True)
    no_school = models.BooleanField(
        verbose_name="Doesn't attend school", default=False)
    class_applying_for = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.SET_NULL, blank=True, null=True
    )
    intre_state_transfer = models.BooleanField(null=True, blank=True, default=False)
    illness = models.CharField(null=True, blank=True, max_length=50)
    @property
    def age(self):
        current_year = timezone.now().date().year
        check_date = timezone.datetime(current_year, 3, 31).date()
        return relativedelta(check_date, self.date_of_birth)

    @property
    def age_str(self):
        total = self.age
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

    class Meta:
        verbose_name = "Child Profile"
        verbose_name_plural = "Child Profiles"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)
