from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from analatics.models import PageVisited
from core.utils import (unique_slug_generator_using_name,
                        unique_slug_generator_using_title)

from .utils import (activity_image_upload_path, activity_video_upload_path,
                    carousel_image_upload_path,employee_img_upload_path,
                    ezyschooling_new_article_image_upload_path,
                    online_event_speaker_image_upload_path,principal_pic_upload_path,user_testimonial_upload_path,impactinar_upload_path)


class ContactUs(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(max_length=3000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us"

    def __str__(self):
        if self.user:
            return self.user.username
        else:
            return self.name


class CarouselCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Carousel Categories"


class Carousel(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to=carousel_image_upload_path)
    small_image = models.ImageField(
        upload_to=carousel_image_upload_path, null=True, blank=True)
    link = models.CharField(max_length=200, blank=True, null=True)
    button_text = models.CharField(max_length=200, null=True, blank=True)
    category = models.ForeignKey(
        "miscs.CarouselCategory", on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.button_text

    class Meta:
        ordering = [
            "order",
        ]
        verbose_name = "Carousel"
        verbose_name_plural = "Carousels"


class Activity(models.Model):
    videos = models.FileField(
        upload_to=activity_video_upload_path, null=True, blank=True)
    image = models.ImageField(
        upload_to=activity_image_upload_path,
        max_length=200,
        null=True,
        blank=True)
    link = models.CharField(max_length=200, null=True, blank=True)
    button_text = models.CharField(max_length=200, null=True, blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.link

    class Meta:
        ordering = [
            "order",
        ]
        verbose_name = "Ezyschooling Activity"
        verbose_name_plural = "Ezyschooling Activities"


class EzySchoolingNewsArticle(models.Model):
    image = models.ImageField(
        upload_to=ezyschooling_new_article_image_upload_path)
    link = models.CharField(max_length=200, blank=True, null=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.link

    class Meta:
        ordering = [
            "order",
        ]
        verbose_name = "Ezyschooling News Article"
        verbose_name_plural = "Ezyschooling News Articles"


class CompetitionCarouselCategory(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Competition Carousel Categories"


class CompetitionCarousel(models.Model):
    parent_name = models.CharField(max_length=200, null=True, blank=True)
    child_name = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        "miscs.CompetitionCarouselCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    image = models.ImageField(upload_to="competition/", null=True, blank=True)
    order = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.child_name

    class Meta:
        verbose_name_plural = "Competition Carousel"


class OnlineEvent(models.Model):
    title = models.CharField(max_length=250)
    url = models.URLField(help_text="Link to event goes here.")
    description = models.TextField(max_length=1000)
    speaker_name = models.CharField(max_length=200)
    speaker_photo = models.ImageField(
        upload_to=online_event_speaker_image_upload_path, null=True, blank=True)
    event_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Achiever(models.Model):
    child_name = models.CharField(max_length=200)
    parent_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    description = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ezyschooling Achiever"
        verbose_name_plural = "Ezyschooling Achievers"

    def __str__(self):
        return self.child_name


class TalentHuntSubmission(models.Model):
    referrer = models.ForeignKey("self", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="referrals")
    title = models.CharField(max_length=250)
    video = models.TextField(blank=True, null=True)
    photo = models.TextField(blank=True, null=True)
    child_name = models.CharField(max_length=200)
    parent_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField(max_length=255)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    is_winner = models.BooleanField(default=False)
    likes = models.ManyToManyField(
        "accounts.User",
        db_index=True,
        related_name="user_liked_talenthunt_video",
        blank=True)

    views = GenericRelation(PageVisited)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Talent Hunt Submission"
        verbose_name_plural = "Talent Hunt Submissions"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class FaqCategory(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, null=True)

    class Meta:
        verbose_name = "FAQ Category"
        verbose_name_plural = "FAQ Categories"

    def __str__(self):
        return self.title


class FaqQuestion(models.Model):
    SCHOOL_CATEGORY = (("Girls", "Girls"), ("Boys", "Boys"), ("Coed", "Coed"))
    title = models.CharField(max_length=250)
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS,
         default=DRAFT,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        "miscs.FaqCategory",
        related_name="faq_question",
        null=True,
        blank=True,
        on_delete=models.CASCADE)

    region = models.ForeignKey(
        "schools.Region",
        related_name="faqs",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    city = models.ForeignKey(
        "schools.city",
        related_name="faqs_city",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    district = models.ForeignKey(
            "schools.District",
            related_name="faqs_district",
            null=True,
            blank=True,
            on_delete=models.CASCADE)

    district_region = models.ForeignKey(
            "schools.DistrictRegion",
             related_name="faqs_districtregion",
             null=True,
             blank=True,
             on_delete=models.CASCADE)

    school_category = models.CharField(
        max_length=10,
        choices=SCHOOL_CATEGORY,
        null=True,
        blank=True,
        default="Coed")

    board = models.ForeignKey(
            "schools.SchoolBoard",
            related_name="faqs_board",
            null=True,
            blank=True,
            on_delete=models.CASCADE)

    school_type = models.ForeignKey(
            "schools.SchoolType",
            related_name="faqs_school_type",
            null=True,
            blank=True,
            on_delete=models.CASCADE)

    class_relation = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.CASCADE,
        null=True,blank=True,related_name="faqs_school_classes",
    )

    popular = models.BooleanField(default=False, blank=True , null=True)
    class Meta:
        verbose_name = "FAQ Question"
        verbose_name_plural = "FAQ Questions"

    def __str__(self):
        return self.title


class FaqAnswer(models.Model):
    question = models.ForeignKey(
        "miscs.FaqQuestion",
        related_name='faq_answer',
        on_delete=models.CASCADE)
    answer = models.TextField()

    class Meta:
        verbose_name = "FAQ Answer"
        verbose_name_plural = "FAQ Answers"

    def __str__(self):
        return self.question.title


class AdmissionGuidanceSlot(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    day = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    time_slot = models.TimeField()
    zoom_link = models.URLField(max_length=255)
    meeting_id = models.CharField(
        max_length=255, help_text="Include the spaces in the ID, because it will be exactly how it will be shown to user in email.")
    meeting_passcode = models.CharField(max_length=255)
    event_date = models.DateField(
        help_text="Change the date for the latest version of the event here, this will be the date mentioned in the emails.")

    class Meta:
        verbose_name = "Admission Guidance Slot"
        verbose_name_plural = "Admission Guidance Slots"

    def __str__(self):
        return f"{self.day} - {str(self.time_slot)}"


class AdmissionGuidance(models.Model):
    parent_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    dob = models.DateField(verbose_name="Child's Date of Birth", null=True, blank=True)
    target_region = models.CharField(max_length=255, null=True,blank=True)
    budget = models.CharField(max_length=255, blank=True)
    slot = models.ForeignKey("miscs.AdmissionGuidanceSlot",
                             on_delete=models.SET_NULL, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admission Guidance Registration"
        verbose_name_plural = "Admission Guidance Registrations"

    def __str__(self):
        return self.parent_name


class AdmissionAlert(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    phone_no = models.CharField(max_length=255)
    region = models.ForeignKey(
        "schools.Region", on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admission Alert"
        verbose_name_plural = "Admission Alerts"

    def __str__(self):
        return self.name

class AdmissionGuidanceProgrammePackage(models.Model):
    name = models.CharField(max_length=150)
    amount = models.PositiveIntegerField()
    def __str__(self):
        return self.name

class AdmissionGuidanceProgramme(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    phone_no = models.CharField(max_length=255)
    region = models.ForeignKey(
        "schools.Region", on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admission Guidance Programme"
        verbose_name_plural = "Admission Guidance Programme"

    def __str__(self):
        return self.name

class SurveyQuestions(models.Model):
    label = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Survey Question"
        verbose_name_plural = "Survey Questions"

    def __str__(self):
        return self.label

class SurveyChoices(models.Model):
    question = models.ForeignKey(SurveyQuestions,on_delete=models.CASCADE, related_name="choices")
    name = models.CharField(max_length=150)

    class Meta:
        verbose_name = "Survey Choice"
        verbose_name_plural = "Survey Choices"

    def __str__(self):
        return self.name

class SurveyTaker(models.Model):
    user= models.ForeignKey("accounts.User",on_delete=models.CASCADE, )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username



class SurveyResponses(models.Model):
    question = models.ForeignKey(SurveyQuestions,on_delete=models.CASCADE)
    answer = models.ForeignKey(SurveyChoices,on_delete=models.CASCADE)
    taker = models.ForeignKey(SurveyTaker,on_delete=models.CASCADE, related_name='responses',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"

    def __str__(self):
        return self.question.label



class WebinarRegistrations(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    school_name = models.CharField(max_length=255,null=True,blank=True)
    designation  = models.CharField(max_length=255,null=True,blank=True)
    city = models.CharField(max_length=255,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Webinar Registration"
        verbose_name_plural = "Webinar Registrations"

class SponsorsRegistrations(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    companyname = models.CharField(max_length=255, null=True, blank=True)
    website_link = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sponsors Registration"
        verbose_name_plural = "Sponsors Registration"


class PastAndCurrentImpactinars(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS,
         default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    title = models.CharField(max_length=400, null=True, blank=True)
    descriptions = models.TextField(blank=True, null=True)
    video_link= models.CharField(max_length=250, null=True, blank=True)
    held_on = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    photo =   models.FileField(
        upload_to=impactinar_upload_path, blank=True, null=True
    )

    class Meta:
        verbose_name = "Past And Current Impactinar"
        verbose_name_plural = "Past And Current Impactinars"

class InvitedPrincipals(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    designation =  models.CharField(max_length=255, null=True, blank=True)
    school_name =  models.CharField(max_length=255, null=True, blank=True)
    photo =   models.FileField(
        upload_to=principal_pic_upload_path, blank=True, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    about_principal = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Invited Principal"
        verbose_name_plural = "Invited Principals"



class Testimonials(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    designation =  models.CharField(max_length=255, null=True, blank=True)
    photo = models.FileField(upload_to=user_testimonial_upload_path, blank=True, null=True)
    is_school = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Testimonial"
        verbose_name_plural = "User Testimonials"

class OurSponsers(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)
    photo = models.FileField(upload_to=user_testimonial_upload_path, blank=True, null=True)
    website_link = models.CharField(max_length=250, null=True, blank=True)

    class Meta:
        verbose_name = "Our Sponser"
        verbose_name_plural = "Our Sponser"


class EzyschoolingEmployees(models.Model):
    name = models.CharField(max_length=255, null=True,blank=True)
    photo = models.FileField(upload_to=employee_img_upload_path, blank=True, null=True)
    designation = models.CharField(max_length=255, null=True,blank=True)
    linkedinurl= models.CharField(max_length=255, null=True,blank=True)

    class Meta:
        verbose_name="Ezyschooling Employee"
        verbose_name_plural="Ezyschooling Employees"


class UnsubscribeEmail(models.Model):
   email=models.EmailField(unique=True)
   timestamp = models.DateTimeField(auto_now_add=True)

   def __str__(self):
       return self.email
