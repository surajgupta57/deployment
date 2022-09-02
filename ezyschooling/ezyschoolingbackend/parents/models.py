from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone

from core.utils import unique_slug_generator_using_name
from schools.models import Region
from .utils import parent_profile_picture_upload_path,parent_addhar_card_path,parent_pan_card_path, parent_special_ground_proof


class ParentProfile(models.Model):
    GENDER = (("male", "male"), ("female", "female"))
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="parent_profile"
    )
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER, default="male")
    slug = models.SlugField(
        unique=True, max_length=180, db_index=True, blank=True, null=True
    )
    photo = models.ImageField(
        upload_to=parent_profile_picture_upload_path, blank=True, null=True
    )
    companyname = models.CharField(max_length=150,blank=True,null=True)
    aadhaar_number = models.CharField(max_length=16,blank=True,null=True)
    transferable_job = models.BooleanField(blank=True,null=True)
    special_ground = models.BooleanField(blank=True,null=True)
    designation = models.CharField(max_length=50,blank=True,null=True)
    profession = models.CharField(max_length=50,blank=True,null=True)
    special_ground_proof = models.FileField(upload_to=parent_special_ground_proof,blank=True, null=True)
    parent_aadhar_card = models.FileField(upload_to=parent_addhar_card_path,blank=True, null=True)
    pan_card_proof = models.FileField(upload_to=parent_pan_card_path,blank=True, null=True)
    income = models.CharField(max_length=12, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    bio = models.CharField(max_length=255, null=True, blank=True)
    parent_type = models.CharField(max_length=50, null=True, blank=True)
    bookmarked_articles = models.ManyToManyField(
        "articles.ExpertArticle", blank=True, related_name="bookmarked_parents"
    )
    bookmarked_admission_articles = models.ManyToManyField(
        "admission_informations.AdmissionInformationArticle", blank=True, related_name="bookmarked_parents"
    )
    bookmarked_discussions = models.ManyToManyField(
        "discussions.Discussion", blank=True, related_name="bookmarked_parents"
    )
    bookmarked_videos = models.ManyToManyField(
        "videos.ExpertUserVideo", blank=True, related_name="bookmarked_parents"
    )
    bookmarked_admission_videos = models.ManyToManyField(
        "admission_informations.AdmissionInformationUserVideo", blank=True, related_name="bookmarked_parents"
    )
    follow_tags = models.ManyToManyField(
        "tags.CustomTag", blank=True, related_name="followers"
    )
    # Address Fields
    street_address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)

    # for admission form
    education = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    office_address = models.CharField(max_length=255, blank=True, null=True)
    office_number = models.CharField(max_length=15, blank=True, null=True)
    alumni_school_name = models.ForeignKey(
        "schools.SchoolProfile",
        blank=True,
        null=True,
        related_name="school_name",
        on_delete=models.SET_NULL,
    )
    alumni_year_of_passing = models.CharField(max_length=5, blank=True, null=True)
    passing_class = models.CharField(max_length=15, blank=True, null=True)
    alumni_proof = models.FileField(upload_to="images", blank=True, null=True)
    covid_vaccination_certificate = models.FileField(upload_to="images", blank=True, null=True)
    frontline_helper = models.BooleanField(blank=True,null=True, default=False)
    college_name = models.CharField(max_length=200, blank=True, null=True)
    course_name = models.CharField(max_length=200, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def age(self):
        return relativedelta(timezone.now().date(), self.date_of_birth).years

    class Meta:
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parent Profiles"

    def __str__(self):
        return str(self.email) if self.email else self.user.username

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class ParentAddress(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        limit_choices_to={'is_parent':True},
        on_delete=models.CASCADE,
        related_name="parent_address_user",
        null = True,
        blank=True
    )
    parent = models.ForeignKey(
        "parents.ParentProfile", on_delete=models.CASCADE, related_name="parent_address"
    )
    street_address = models.CharField(max_length=250,null=True,blank=True)
    city = models.CharField(max_length=150,blank=True,null=True)
    state = models.CharField(max_length=100,blank=True,null=True)
    pincode = models.CharField(max_length=10,blank=True,null=True)
    country = models.CharField(max_length=150,blank=True,null=True)
    phone_no = models.CharField(max_length=50,blank=True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    monthly_budget = models.CharField(max_length=200,blank=True,null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE,verbose_name="Region",null = True,blank=True)

    class Meta:
        verbose_name = "Parent Address"
        verbose_name_plural = "Parent Address"

    def __str__(self):
        return self.parent.email


class ParentTracker(models.Model):
        parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE,null=True,blank=True)
        address= models.ForeignKey(ParentAddress, on_delete=models.CASCADE,null = True,blank=True)
        timestamp = models.DateTimeField(auto_now_add=True,verbose_name="Date",null=True,blank=True)
