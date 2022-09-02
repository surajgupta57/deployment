from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.validators import RegexValidator
from django.utils.text import slugify
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from analatics.models import PageVisited
# from .signals import fetchSchoolClassesView
from core.utils import unique_slug_generator_using_name
from django.core.exceptions import ValidationError
from .utils import (school_activity_image_upload_path,
                    school_activity_type_slider_images,
                    school_cover_upload_path, school_format_photo_upload_path,
                    school_gallery_upload_path, school_logo_upload_path,
                    school_region_photo_upload_path,
                    school_selected_csv_upload_path,
                    school_area_photo_upload_path,
                    school_country_photo_upload_path,
                    school_states_photo_upload_path,
                    school_district_photo_upload_path, school_city_photo_upload_path,
                    school_district_region_photo_upload_path,
                    school_area_photo_upload_path,
                    school_profile_image_upload_path,
                    alumni_image_upload_path,
                    boarding_school_infra_image_upload_path,
                    )
import uuid


class SchoolStream(models.Model):
    stream = models.CharField(max_length=80, null=True)

    def __str__(self):
        return f"{self.stream}"


class SchoolClasses(models.Model):
    rank = models.PositiveIntegerField()
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "School Class"
        verbose_name_plural = "School Classes"




def fetchSchoolClassesView():
    all_data = SchoolMultiClassRelation.objects.filter().order_by("-id")
    for data in all_data:
        if data.multi_class_relation.filter():
            for class_relation in data.multi_class_relation.filter():
                if SchoolMultiClassRelation.objects.filter(multi_class_relation__in=[class_relation]).count() > 1:

                    data.multi_class_relation.remove(class_relation)
    return None


def validate_unique_class_relation( value):
        if value:
            print(type(value), value)
            val = SchoolClasses.objects.get(id=value)
            print(type(val), val)
            flag = SchoolMultiClassRelation.objects.filter(
                    Q(multi_class_relation__in=[val])| Q(unique_class_relation=val)).exists() and not SchoolMultiClassRelation.objects.filter(
                    Q(multi_class_relation__in=[val])).filter(Q(unique_class_relation=val)).count()==0
            if not flag:
                    check = SchoolMultiClassRelation.objects.filter(
                        multi_class_relation__in=[val]).first()
                    if check:
                        raise ValidationError(
                            _(
                                f'%(unique_class_relation)s already present in multi class relation (Record id-{check.id}). Please select another one.'),
                            params={'unique_class_relation': val.name},
                        )
#, help_text="Make Sure that this value not "

class SchoolMultiClassRelation(models.Model):

    unique_class_relation = models.OneToOneField(
        "schools.SchoolClasses",
        on_delete=models.CASCADE,
        related_name='school_unique_class_relation', validators=[validate_unique_class_relation]
    )
    multi_class_relation = models.ManyToManyField(
        "schools.SchoolClasses", blank=True, related_name="school_multiple_class_relation")

    def __str__(self):
        fetchSchoolClassesView()
        return self.unique_class_relation.name

    class Meta:
        verbose_name = "School Multi Class Relation"
        verbose_name_plural = "School Multi Classes Relation"


class SchoolType(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    order_rank= models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "School Type"
        verbose_name_plural = "School Types"


class SchoolBoard(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "School Board"
        verbose_name_plural = "School Boards"


class Pincode(models.Model):
    type = models.CharField(max_length=30, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.pincode


class Country(models.Model):
    name = models.CharField(max_length=120, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)
    description = models.TextField(
        max_length=3000, null=True, blank=True)
    photo = models.FileField(
        upload_to=school_country_photo_upload_path, blank=True, null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class States(models.Model):
    name = models.CharField(max_length=120, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField(
        max_length=3000, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)
    photo = models.FileField(
        upload_to=school_states_photo_upload_path, blank=True, null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class City(models.Model):
    OPTIONS = (("Main", "Main"), ("Other", "Other"), ("Category", "Category"))
    name = models.CharField(max_length=120, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    states = models.ForeignKey(
        "schools.States",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField(
        max_length=3000, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)
    photo = models.FileField(
        upload_to=school_city_photo_upload_path, blank=True, null=True
    )
    type = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="Other")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class District(models.Model):
    name = models.CharField(max_length=120, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    state = models.ForeignKey(
        "schools.States",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    city = models.ForeignKey(
        "schools.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    photo = models.FileField(
        upload_to=school_district_photo_upload_path, blank=True, null=True
    )
    description = models.TextField(
        max_length=3000, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class DistrictRegion(models.Model):
    name = models.CharField(max_length=120, null=True, blank=True)
    district = models.ForeignKey(
        "schools.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        "schools.States",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    city = models.ForeignKey(
        "schools.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    photo = models.FileField(
        upload_to=school_district_region_photo_upload_path, blank=True, null=True
    )
    pincode = models.ManyToManyField(
        "schools.Pincode",
        blank=True,
    )
    description = models.TextField(max_length=3000, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)
    latitude = models.DecimalField(max_digits=22,decimal_places=16,blank=True,null=True)
    longitude = models.DecimalField(max_digits=22,decimal_places=16,blank=True,null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        # calculating lat/long of the region
        # checking if region is not of online schools
        if not self.latitude and not self.longitude:
            if self.city:
                if self.city.slug != 'online-schools':
                    # cchecking if city is boarding or not
                    if self.city.slug == 'boarding-schools':
                        """if city is boarding than only getting lat/long by name of region as region names in case of boarding schools are city names (ex: delhi, noida etc)"""
                        from geopy.geocoders import Nominatim
                        from geopy.distance import geodesic
                        app = Nominatim(user_agent="Ezyschool",timeout=3)
                        name = f"{self.name}"
                        if app.geocode(name):
                            coordinates = app.geocode(name)
                            self.latitude = coordinates.latitude
                            self.longitude = coordinates.longitude
                    # if it's normal city than calculating lat/long for particular city's region
                    else:
                        from geopy.geocoders import Nominatim
                        from geopy.distance import geodesic
                        app = Nominatim(user_agent="Ezyschool",timeout=3)
                        name = f"{self.name}, {self.city.name}"
                        if app.geocode(name):
                            # getting coordinates of region
                            coordinates = app.geocode(name)
                            # getting coordinates of city
                            city_coardinates = app.geocode(self.city.name)
                            # checking if calculated distance between city and region is not more than 50kms
                            city = (city_coardinates.latitude,city_coardinates.longitude)
                            region = (coordinates.latitude, coordinates.longitude)
                            # if distance is more than 50kms, neglacting the coordinates
                            if int(geodesic(city, region).km) > 50:
                                pass
                            else:
                                self.latitude = coordinates.latitude
                                self.longitude = coordinates.longitude
        super().save(*args, **kwargs)

class Area(models.Model):
    name = models.CharField(max_length=150, verbose_name="school_area")
    district_region = models.ForeignKey(
        "schools.DistrictRegion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    district = models.ForeignKey(
        "schools.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        "schools.States",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pincode = models.ManyToManyField(
        "schools.Pincode",
        blank=True
    )
    slug = models.SlugField(max_length=120, null=True, blank=True)
    photo = models.FileField(
        upload_to=school_area_photo_upload_path, blank=True, null=True
    )
    params = JSONField(null=True, blank=True, default=dict)

    city = models.ForeignKey(
        "schools.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


#################old db Schema######################

class State(models.Model):
    rank = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class Region(models.Model):
    rank = models.PositiveIntegerField()
    name = models.CharField(max_length=80, verbose_name="school_regions")
    state = models.ForeignKey(
        "schools.State",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    photo = models.FileField(
        upload_to=school_region_photo_upload_path, blank=True, null=True
    )
    is_featured = models.BooleanField(default=False)
    admission_description = models.TextField(
        max_length=3000, null=True, blank=True)
    slug = models.SlugField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


################# old Db schema#####################


class SchoolProfile(models.Model):
    SCHOOL_CATEGORY = (("Girls", "Girls"), ("Boys", "Boys"), ("Coed", "Coed"))
    OWNERSHIP_CHOICES = [("G", "Government"), ("P", "Private")]
    LANGUAGE_CHOICES = [
        ("E", "English"),
        ("H", "Hindi")
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    common_id = models.CharField(max_length=20, null=True, blank=True)
    count_start = models.IntegerField(default=0)
    name = models.CharField(max_length=255, null=True, blank=True)
    short_name = models.CharField(
        max_length=5, blank=True, null=True)  # excel update
    global_rank = models.IntegerField(default=0, blank=True, null=True)
    region_rank = models.PositiveIntegerField(default=0, blank=True, null=True)
    states_rank = models.IntegerField(default=0, blank=True, null=True)
    district_rank = models.IntegerField(default=0, blank=True, null=True)
    district_region_rank = models.IntegerField(default=0, blank=True, null=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    sending_email_ids = models.TextField(null=True, blank=True)
    head_email_ids = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=255, blank=True,null=True, db_index=True)
    phone_no = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    school_timings = models.CharField(max_length=254, null=True, blank=True)
    school_type = models.ForeignKey(
        "schools.SchoolType", on_delete=models.SET_NULL, null=True, blank=True
    )
    school_board = models.ForeignKey(
        "schools.SchoolBoard", on_delete=models.SET_NULL, null=True, blank=True
    )
    school_boardss = models.ManyToManyField(
        "schools.SchoolBoard", blank=True, related_name="schools")
    medium = models.CharField(verbose_name="Medium of Instruction", max_length=10,
                              choices=LANGUAGE_CHOICES, default="E")
    languages = models.ManyToManyField("schools.Language",blank=True, related_name="language_options")
    academic_session = models.CharField(max_length=25, null=True, blank=True)
    school_format = models.ForeignKey(
        "schools.SchoolFormat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    latitude = models.DecimalField(
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True,
        default=28.644800)
    longitude = models.DecimalField(
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True,
        default=77.216721)
    short_address = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    region = models.ForeignKey(
        "schools.Region", on_delete=models.SET_NULL, null=True, blank=True
    )
    state = models.ForeignKey(
        "schools.State", on_delete=models.SET_NULL, null=True, blank=True
    )
    zipcode = models.CharField(max_length=7, null=True, blank=True)
    logo = models.ImageField(
        upload_to=school_logo_upload_path,
        default="schools/logos/default.png",
        null=True,
        blank=True,
    )
    cover = models.ImageField(
        upload_to=school_cover_upload_path,
        default="schools/cover/default.jpg",
        null=True,
        blank=True,
    )
    class_relation = models.ManyToManyField(
        "schools.SchoolClasses", blank=True)
    collab = models.BooleanField(
        default=False, db_index=True, null=True, blank=True)
    online_school = models.BooleanField(default=False, null=True, blank=True)
    boarding_school = models.BooleanField(default=False,null=True,blank=True)
    scholarship_program = models.BooleanField(default=False,null=True,blank=True)
    year_established = models.CharField(max_length=254, null=True, blank=True)
    built_in_area = models.CharField(max_length=120,null=True,blank=True)
    school_category = models.CharField(
        max_length=10,
        choices=SCHOOL_CATEGORY,
        null=True,
        blank=True,
        default="Coed")
    avg_fee = models.PositiveIntegerField(null=True, blank=True)
    calculated_avg_fee = models.CharField(null=True, blank=True, max_length=50)
    ownership = models.CharField(
        max_length=5,
        choices=OWNERSHIP_CHOICES,
        null=True,
        blank=True
    )
    description = models.TextField(null=True, blank=True)
    student_teacher_ratio = models.CharField(
        max_length=50, blank=True, null=True)
    is_active = models.BooleanField(
        default=True, db_index=True, null=True, blank=True)
    for_homepage = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, null=True, blank=True)
    form_price = models.IntegerField(default=0, null=True, blank=True)
    convenience_fee = models.IntegerField(default=0, null=True, blank=True)
    commission_percentage = models.FloatField(blank=True,null=True,default=0)
    video_tour_link = models.CharField(max_length=250, null=True, blank=True)
    point_system = models.BooleanField(default=False)
    hide_point_calculator = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    required_admission_form_fields = JSONField(
        null=True, blank=True, default=dict)
    required_child_fields = JSONField(null=True, blank=True, default=dict)
    required_father_fields = JSONField(null=True, blank=True, default=dict)
    required_mother_fields = JSONField(null=True, blank=True, default=dict)
    required_guardian_fields = JSONField(null=True, blank=True, default=dict)

    school_area = models.ForeignKey(
        "schools.Area",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    district_region = models.ForeignKey(
        "schools.DistrictRegion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    district = models.ForeignKey(
        "schools.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    school_city = models.ForeignKey(
        "schools.city",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    school_state = models.ForeignKey(
        "schools.States", on_delete=models.SET_NULL, null=True, blank=True
    )
    school_country = models.ForeignKey(
        "schools.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pincode = models.ForeignKey(
        "schools.Pincode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    views = models.PositiveIntegerField(default=0)
    visits = GenericRelation(PageVisited)
    views_permission = models.BooleanField(
        default=False, verbose_name="School Cart Data Permission")
    views_check_permission = models.BooleanField(
        default=False, verbose_name="School Views Permission")
    enquiry_permission = models.BooleanField(
        default=False, verbose_name="School Enquiry Permission")
    contact_data_permission = models.BooleanField(
        default=False, verbose_name="School Contact Data Permission")
    counselling_data_permission = models.BooleanField(
        default=False, verbose_name="Counselling Data Permission")
    send_whatsapp_notification = models.BooleanField(default=False,verbose_name="Whatsapp Message Notification Permission")
    phone_number_cannot_viewed = models.BooleanField(default=False, verbose_name="Phone Number Cannot Viewed Permission")
    virtual_tour = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_avg_fee_calculated = models.DateField(null=True, blank=True)
    ad_source = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/school/profile/" + self.slug

    class Meta:
        verbose_name = "School Profile"
        verbose_name_plural = "School Profiles"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        # calculating long-lat of school
        self_lat = str(self.latitude)
        self_long = str(self.longitude)
        # comparing if current lat/long are default ones
        if self_lat == '28.6448000000000000' and self_long == '77.2167210000000068':
            """
            if current lat/longs are default one then getting district regions lat/long
            """
            # checking if district region is present and have lat/log
            if self.district_region and self.district_region.latitude and self.district_region.longitude:
                self.latitude = self.district_region.latitude
                self.longitude = self.district_region.longitude
            else:
                pass
        else:
            pass
        super().save(*args, **kwargs)
        count = Feature.objects.filter(school=self).count()
        if (count == 0):
            for j in Subfeature.objects.all():
                obj, created = Feature.objects.get_or_create(features=j, school=self)


class Gallery(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile",
        related_name="gallery",
        on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=school_gallery_upload_path,
        null=True,
        blank=True,
        help_text=mark_safe(
            "Please compress the images before uploading using this <a href='https://www.iloveimg.com/compress-image'>tool</a>."
        ),
    )
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}-{1}".format(self.school.name, self.image)

    class Meta:
        verbose_name = "School Gallery"
        verbose_name_plural = "School Gallery"


class DistancePoint(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile", on_delete=models.CASCADE, related_name="distance_points")
    start = models.DecimalField(max_digits=10, decimal_places=2)
    end = models.DecimalField(max_digits=10, decimal_places=2)
    point = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school} - {self.start} - {self.end}"

    class Meta:
        verbose_name = "School Distance Point"
        verbose_name_plural = "School Distance Points"


class AdmmissionOpenClasses(models.Model):
    STATUS = [("OPEN", "OPEN"), ("ABOUT TO CLOSE", "ABOUT TO CLOSE"), ("CLOSE", "CLOSE")]
    class_relation = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.CASCADE
    )
    school = models.ForeignKey(
        "schools.SchoolProfile", on_delete=models.CASCADE)
    admission_open = models.CharField(
        max_length=15,
        choices=STATUS,
        null=True,
        blank=True,
        default="CLOSE"
    )
    form_limit = models.IntegerField(default=10000)
    draft = models.BooleanField(default=False)
    available_seats = models.PositiveIntegerField(default=0)
    last_date = models.DateField(blank=True, null=True)
    session = models.CharField("Session", help_text="ex YYYY-YYYY",
                               max_length=9, validators=[
            RegexValidator(regex='^.{9}$', message='Please Input Correct Format', code='nomatch')], default="2021-2022",
                               null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.class_relation} - {self.session} - {self.admission_open}"

    class Meta:
        verbose_name = "School Admission Open Classes"
        verbose_name_plural = "School Admission Open Classes"
        ordering = ["class_relation__rank"]
        unique_together = ["class_relation", "school", "session"]


class SchoolFeesType(models.Model):
    head = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return self.head

    class Meta:
        verbose_name = "School Fees Type"


class SchoolFeesParameters(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name='school_fees_parameter',
        blank=True,
        null=True
    )
    head = models.ForeignKey(SchoolFeesType, on_delete=models.CASCADE, null=True)
    tenure = models.CharField(null=True, blank=True, max_length=50)
    price = models.IntegerField(default=0, null=True, blank=True)
    upper_price = models.IntegerField(default=0, null=True, blank=True)
    range = models.BooleanField(default=False, null=True)
    refundable = models.BooleanField(default=False, null=True)

    def __str__(self):
        if self.school:
            return f"{self.id}-{self.school.name} - {self.head} - {self.tenure} - {self.price}"
        return f"{self.id}-{self.head} - {self.tenure} - {self.price}"


class FeeStructure(models.Model):
    class_relation = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.CASCADE
    )
    stream_relation = models.ForeignKey(SchoolStream, null=True, blank=True, on_delete=models.CASCADE)
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name='school_fee_structure',
    )
    fees_parameters = models.ManyToManyField(SchoolFeesParameters, related_name='feestructure', blank=True)
    active = models.BooleanField(default=True)
    draft = models.BooleanField(default=False)
    fee_price = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session = models.CharField("Session", help_text="ex YYYY-YYYY",
                                max_length=9, validators=[RegexValidator(regex='^.{9}$', message='Please Input Correct Format', code='nomatch')], default="2021-2022", null=True, blank=True)
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.school.name or str(self.id)

    # def validate_unique(self, exclude=None):
    #     all_structure = FeeStructure.objects.filter(class_relation=self.class_relation, school=self.school, session=self.session)
    #     is_unique = True
    #     if not self.stream_relation:
    #         is_stream_blank = True
    #     else:
    #         is_stream_blank = False
    #
    #     if all_structure:
    #         for item in all_structure:
    #             if not item.stream_relation and not self.stream_relation:
    #                 is_unique = False
    #             elif item.stream_relation and not self.stream_relation:
    #                 is_unique = True
    #             elif item.stream_relation == self.stream_relation:
    #                 is_unique = False
    #
    #             if is_unique == False:
    #                 id = item.id
    #                 break
    #
    #         if self.id == id:
    #             pass
    #         else:
    #             if is_unique == True:
    #                 pass
    #             elif is_unique == False:
    #                 raise ValidationError('Data Already Exists')
    #     else:
    #         pass
    #     super(FeeStructure, self).validate_unique(exclude=exclude)

    @property
    def max_fees(self):
        final_list = []
        feestr = FeeStructure.objects.filter(school=self.school)
        if feestr.exists():
            for i in feestr:
                if i and i.fee_price:
                    final_list.append(i.fee_price)
            if len(final_list) > 0:
                return max(final_list)
            else:
                return 0
        else:
            return 0

    @property
    def min_fees(self):
        final_list = []
        feestr = FeeStructure.objects.filter(school=self.school)
        if feestr.exists():
            for i in feestr:
                if i and i.fee_price:
                    final_list.append(i.fee_price)
            if len(final_list) > 0:
                return min(final_list)
            else:
                return 0
        else:
            return 0

    class Meta:
        verbose_name = "School Fee Structure"
        verbose_name_plural = "School Fee Structure"
        unique_together = ["class_relation", "school", "session", 'stream_relation']


class ActivityType(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name="activities_type",
        null=True,
        blank=True)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School Activity Type"
        verbose_name_plural = "School Activities Types"
        ordering = ("order", "id")


class Activity(models.Model):
    activity_type = models.ForeignKey(
        "schools.ActivityType",
        on_delete=models.CASCADE,
        related_name="activities",
        null=True,
        blank=True)
    name = models.TextField()
    order = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School Activity"
        verbose_name_plural = "School Activities"
        ordering = ("order", "id")


class ActivityTypeAutocomplete(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School Activity Type Autocomplete Data"
        verbose_name_plural = "School Activity Type Autocomplete Data"

    def __str__(self):
        return self.name


class ActivityAutocomplete(models.Model):
    activity_type = models.ForeignKey(
        "schools.ActivityTypeAutocomplete",
        on_delete=models.CASCADE,
        related_name="activities",
        null=True,
        blank=True)
    name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School Activity Autocomplete Data"
        verbose_name_plural = "School Activity Autocomplete Data"

    def __str__(self):
        return self.name


class Contact(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name="contacts")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}-{1}".format(self.school.name, self.name)

    class Meta:
        verbose_name = "School Contact"
        verbose_name_plural = "School Contacts"


class SchoolView(models.Model):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, blank=True, null=True)
    school = models.ForeignKey(
        "schools.SchoolProfile",
        on_delete=models.CASCADE,
        related_name="profile_views")
    count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School View"
        verbose_name_plural = "School Views"
        ordering = ("-updated_at", "id")

    def __str__(self):
        return str(self.user) + " - " + str(self.count)


class SchoolPoint(models.Model):
    school = models.ForeignKey(
        "schools.SchoolProfile",
        related_name="points",
        on_delete=models.CASCADE)
    single_child_points = models.IntegerField(blank=True, null=True, default=0)
    siblings_points = models.IntegerField(blank=True, null=True, default=0)
    parent_alumni_points = models.IntegerField(
        blank=True, null=True, default=0)
    staff_ward_points = models.IntegerField(blank=True, null=True, default=0)
    first_born_child_points = models.IntegerField(
        blank=True, null=True, default=0)
    first_girl_child_points = models.IntegerField(
        blank=True, null=True, default=0)
    single_girl_child_points = models.IntegerField(
        blank=True, null=True, default=0)
    is_christian_points = models.IntegerField(blank=True, null=True, default=0)
    girl_child_points = models.IntegerField(blank=True, null=True, default=0)
    single_parent_points = models.IntegerField(
        blank=True, null=True, default=0)
    minority_points = models.IntegerField(blank=True, null=True, default=0)
    student_with_special_needs_points = models.IntegerField(
        blank=True, null=True, default=0)
    children_of_armed_force_points = models.IntegerField(
        blank=True, null=True, default=0)
    transport_facility_points = models.IntegerField(
        blank=True, null=True, default=0)
    # new points
    father_covid_vacination_certifiacte_points = models.IntegerField(blank=True, null=True, default=0)
    mother_covid_vacination_certifiacte_points = models.IntegerField(blank=True, null=True, default=0)
    guardian_covid_vacination_certifiacte_points = models.IntegerField(blank=True, null=True, default=0)
    mother_covid_19_frontline_warrior_points = models.IntegerField(blank=True, null=True, default=0)
    father_covid_19_frontline_warrior_points = models.IntegerField(blank=True, null=True, default=0)
    guardian_covid_19_frontline_warrior_points = models.IntegerField(blank=True, null=True, default=0)
    state_transfer_points = models.IntegerField(blank=True, null=True, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def total_points(self):
        dist_points = 0
        if self.school.distance_points.exists():
            dist_points = self.school.distance_points.order_by("-point").first().point
        return sum([
            self.single_child_points,
            self.siblings_points,
            self.parent_alumni_points,
            self.staff_ward_points,
            self.first_born_child_points,
            self.first_girl_child_points,
            self.transport_facility_points,
            self.single_girl_child_points,
            self.is_christian_points,
            self.girl_child_points,
            self.single_parent_points,
            self.minority_points,
            self.student_with_special_needs_points,
            self.children_of_armed_force_points,
            self.father_covid_vacination_certifiacte_points,
            self.mother_covid_vacination_certifiacte_points,
            self.guardian_covid_vacination_certifiacte_points,
            self.mother_covid_19_frontline_warrior_points,
            self.father_covid_19_frontline_warrior_points,
            self.state_transfer_points,
            dist_points
        ])

    def __str__(self):
        return self.school.name

from django.db.models import Q



from django.db.models import Q
class AgeCriteria(models.Model):
    school = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE)
    session = models.CharField("Session", help_text="ex 2021-2022, 2022-2023",
                               max_length=9, validators=[
            RegexValidator(regex='^.{9}$', message='Please Input Correct Format', code='nomatch')], default="2021-2022",
                               null=True, blank=True)
    class_relation = models.ForeignKey(
        "schools.SchoolClasses", on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "Age Criteria"
        verbose_name_plural = "Age Criteria"
        unique_together = ["school", "class_relation", "session"]

        # constraints = [models.UniqueConstraint(fields=["school","class_relation", "session"], condition=Q(class_relation__active=True),name='unique_age_criteria_per_school'),
        #     ]

    def __str__(self):
        return f"{self.school} - {self.class_relation} - {self.session}"


class SchoolEnquiry(models.Model):
    school = models.ForeignKey(
        "SchoolProfile",
        on_delete=models.CASCADE,
        related_name="enquiries")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                             null=True, blank=True, related_name='user_enquiry')
    parent_name = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=25, null=True, blank=True)
    class_relation = models.ForeignKey("schools.SchoolClasses", on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='child_class_relation_enquiry')
    email = models.EmailField(max_length=254, null=True, blank=True)
    query = models.TextField(max_length=10000, null=True, blank=True)
    source = models.CharField(max_length=50, default='general')
    ad_source = models.CharField(max_length=100, blank=True, null=True)
    child_name = models.CharField(max_length=250, null=True, blank=True)
    tentative_date_of_visit = models.DateField(null=True, blank=True)
    second_number = models.CharField(max_length=25,null=True, blank=True)
    second_number_verified = models.BooleanField(default=False)
    interested_for_visit = models.BooleanField(default=False)
    interested_for_visit_but_no_data_provided = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Enquiry'
        verbose_name_plural = 'School Enquiries'

    def __str__(self):
        return self.query


class SchoolFormat(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    photo = models.FileField(
        upload_to=school_format_photo_upload_path, blank=True, null=True
    )

    class Meta:
        verbose_name = "School Format"
        verbose_name_plural = "School Formats"

    def __str__(self):
        return self.title


class SchoolVerificationCode(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    code = models.CharField(max_length=20, db_index=True)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "School Verification Code"
        verbose_name_plural = "School Verification Codes"

    def __str__(self):
        return f"{self.name} - {self.address}"


class SchoolAdmissionAlert(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True)
    school_relation = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE, null=True)
    class_relation = models.ForeignKey("schools.SchoolClasses", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School Admission Alert"
        verbose_name_plural = "School Admission Alerts"


class SchoolAdmissionFormFee(models.Model):
    school_relation = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE, null=True)
    class_relation = models.ForeignKey("schools.SchoolClasses", on_delete=models.CASCADE, null=True)
    form_price = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "School Admission Form Fee"
        verbose_name_plural = "School Admission Form Fee"


class AppliedSchoolSelectedCsv(models.Model):
    school_relation = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE, null=True)
    csv_file = models.FileField(upload_to=school_selected_csv_upload_path, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CSV Uploaded From School"
        verbose_name_plural = "CSV'S Uploaded From Schools"


class SelectedStudentFromCsv(models.Model):
    school_relation = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE, null=True)
    document = models.ForeignKey("schools.AppliedSchoolSelectedCsv", on_delete=models.CASCADE, null=True)
    child_name = models.CharField(max_length=255, null=True, blank=True)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    mother_name = models.CharField(max_length=255, null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)
    receipt_id = models.CharField(max_length=255, null=True, blank=True)
    school_csv_name = models.CharField(max_length=400, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class FeatureName(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = "Feature Name"
        verbose_name_plural = "Feature Names"

    def __str__(self):
        return f"{self.name}"


class Subfeature(models.Model):
    parent = models.ForeignKey(
        "schools.FeatureName", on_delete=models.SET_NULL, null=True, blank=True,
        related_name='feature_subfeature'
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    params = JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = "Feature Name (Sub)"
        verbose_name_plural = "Feature Names (Sub)"

    def __str__(self):
        return f"{self.name}"


class Feature(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"), ("Undefined", "Undefined"))
    school = models.ForeignKey("schools.SchoolProfile", on_delete=models.CASCADE, null=True)
    features = models.ForeignKey(
        "schools.Subfeature", on_delete=models.SET_NULL, null=True, blank=True
    )
    filter_string = models.CharField(max_length=250, null=True, blank=True)
    exist = models.CharField(
        max_length=15,
        choices=OPTIONS,
        null=True,
        blank=True,
        default="Undefined")

    class Meta:
        verbose_name = "School Features Sets"
        verbose_name_plural = "School Features Sets"

    def __str__(self):
        return f"{self.school}"

    def save(self, *args, **kwargs):
        if self.features.name:
            self.filter_string = str(self.features.name) + "_" + str(self.exist)
        super().save(*args, **kwargs)


class Subjects(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = "Schools Subject"
        verbose_name_plural = "Schools Subjects"


# For Multiple Session Based Admissions
class AdmissionSession(models.Model):
    name = models.CharField("Session year", help_text="ex format YYYY-YYYY",
                            max_length=9, validators=[
            RegexValidator(regex='^.{9}$', message='Please Input Correct Format', code='nomatch')])

    slug = models.SlugField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Admission Session"
        verbose_name_plural = "Admission Sessions"

    def save(self, *args, **kwargs):
        self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


# Admission Page Content/Explore School Content
class AdmissionPageContent(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    city = models.ForeignKey("schools.City", on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey("schools.District", on_delete=models.CASCADE, null=True, blank=True)
    district_region = models.ForeignKey("schools.DistrictRegion", on_delete=models.CASCADE,null=True, blank=True)
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.district_region:
            return f"{self.city} - {self.district} - {self.district_region}"
        else:
            return f"{self.city} - {self.district} - {self.is_popular}"

    class Meta:
        verbose_name = "Admission Open Page Content"
        verbose_name_plural = "Admission Open Page Content"


# Notify Me API

class SchoolClassNotification(models.Model):
    school = models.ForeignKey("SchoolProfile", on_delete=models.CASCADE, related_name="class_notifications")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                             null=True, blank=True, related_name='user_class_notification')
    parent_name = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=25, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    notify_class = models.ForeignKey("SchoolClasses", on_delete=models.CASCADE, related_name="notify_classes")
    session = models.CharField("Session", help_text="ex 2021-2022, 2022-2023",
                               max_length=9, validators=[
            RegexValidator(regex='^.{9}$', message='Please Input Correct Format', code='nomatch')], default="2021-2022",
                               null=True, blank=True)
    notification_sent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'School Class Notifications'
        verbose_name_plural = 'School Class Notifications'
        unique_together = ["school", "user", "notify_class", "session"]

    def __str__(self):
        return f"{self.parent_name} - {self.notify_class} - {self.school}"


class VideoTourLinks(models.Model):
    school = models.ForeignKey('schools.SchoolProfile', on_delete=models.CASCADE)
    link = models.TextField("Links",
                            help_text="Seprate multiple links using comma(,) . Also do not use space in between the links",
                            null=True, blank=True)

    class Meta:
        verbose_name = "Video Tour Link "
        verbose_name_plural = "Video Tour Links"

    def __str__(self):
        return self.school.name


class GroupedSchools(models.Model):
    schools = models.ManyToManyField(
        "schools.SchoolProfile", blank=True)
    group_name = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True, default=False)
    api_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        verbose_name = "Grouped School"
        verbose_name_plural = "Grouped Schools"

    def __str__(self):
        return f"{self.api_key} : {self.group_name}"


class SchoolAdmissionResultImage(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    school = models.ForeignKey("schools.SchoolProfile", on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(
        upload_to=school_profile_image_upload_path,
        null=True,
        blank=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School Admission Result"
        verbose_name_plural = "School Admission Results"

    def __str__(self):
        return f"{self.school.name} : {self.name}"


class SchoolContactClickData(models.Model):
    school = models.ForeignKey("schools.SchoolProfile", on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True, blank=True)
    count_school = models.PositiveIntegerField(default=0)
    count_ezyschooling = models.PositiveIntegerField(default=0)
    user_region = models.CharField(max_length=30, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School Contact Detail"
        verbose_name_plural = "School Contact Details"
        ordering = ("-updated_at", "id")

    def __str__(self):
        total_count = self.count_school + self.count_ezyschooling
        return str(self.user) + ' - ' + str(self.school.name) + " - " + str(total_count)

class Language(models.Model):
    rank = models.IntegerField()
    name = models.CharField(max_length=120,null=True,blank=True,unique=True)
    slug = models.CharField(max_length=120,blank=True,unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SchoolAlumni(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="Provide Full name of alumni")
    image = models.ImageField(upload_to=alumni_image_upload_path,null=True,blank=True,
        default="alumni/images/default.png")
    passing_year = models.PositiveIntegerField(help_text="ex: 1988 or 1999 or 2004 or 2015 ")
    current_designation = models.CharField(max_length=100, help_text="Provide Designation of alumni", null=True,blank=True)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.passing_year}"

    class Meta:
        verbose_name = "School Alumni"
        verbose_name_plural = "School Alumni List"

class FoodCategories(models.Model):
    OPTIONS = (("Veg", "Veg"), ("Non-Veg", "Non-Veg"), ("Jain", "Jain"), ("Egg", "Egg"), ("Vegan", "Vegan"))
    name = models.CharField(max_length=25)
    type = models.CharField(max_length=25,choices=OPTIONS,null=True,blank=True,default="Veg")
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Food Type"
        verbose_name_plural = "Food Types"

class ScheduleTimings(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(null=True,blank=True)

    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.name} - {self.start_time} - {self.start_time}"
        elif self.duration:
            return f"{self.name}-{self.duration}"
        else:
            return self.name
    class Meta:
        verbose_name = "Daywise Schedule Time/Parameter"
        verbose_name_plural = "Daywise Schedule Times/Parameters"

class DaywiseSchedule(models.Model):
    Type_Options = (("Weekdays", "Weekdays"), ("Weekends", "Weekends"))
    school =  models.ForeignKey("schools.SchoolProfile",on_delete=models.CASCADE,blank = True,null = True)
    type = models.CharField(max_length=50,choices=Type_Options,null=True,blank=True,default="Weekdays")
    starting_class = models.ForeignKey(SchoolClasses,on_delete=models.CASCADE,null=True,blank=True, related_name='daywise_class_ranage_starting')
    ending_class = models.ForeignKey(SchoolClasses,on_delete=models.CASCADE,null=True,blank=True, related_name='daywise_class_ranage_ending')
    values = models.ManyToManyField(ScheduleTimings,blank=True)
    session = models.CharField(max_length=20,null=True,blank=True)

    def __str__(self):
        if self.starting_class and self.ending_class:
            return f"{self.school.name}- {self.type} - {self.starting_class} - {self.ending_class}"
        else:
            return f"{self.school.name}- {self.type}"
    class Meta:
        verbose_name = "Daywise Schedule"
        verbose_name_plural = "Daywise Schedules"

class BoardingSchoolInfrastructureHead(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=80)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Boarding School Infrastruture Type"
        verbose_name_plural = "Boarding School Infrastruture Types"

class BoardingSchoolInfrastrutureImages(models.Model):
    image = models.ImageField(upload_to=boarding_school_infra_image_upload_path,null=True,blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.visible}"

    class Meta:
        verbose_name = "Boarding School Infrastruture Image"
        verbose_name_plural = "Boarding School Infrastruture Images"

class BoardingSchoolInfrastructure(models.Model):
    type = models.ForeignKey(BoardingSchoolInfrastructureHead, on_delete=models.CASCADE)
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE)
    description = models.TextField(null=True,blank=True)
    related_images = models.ManyToManyField(BoardingSchoolInfrastrutureImages,blank=True)

    def __str__(self):
        return f"{self.school.name} - {self.type.name}"

    class Meta:
        verbose_name = "Boarding School Infrastruture"
        verbose_name_plural = "Boarding Schools Infrastruture"

class BoardingSchoolExtend(models.Model):
    extended_school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE)
    pre_post_admission_process = models.TextField(null=True, blank=True)
    withdrawl_policy = models.TextField(null=True, blank=True)
    food_option = models.ManyToManyField(FoodCategories,blank=True)
    food_details = models.TextField(null=True, blank=True)
    weekday_schedule = models.ManyToManyField(DaywiseSchedule,blank=True,related_name='daywise_weekday_schedule')
    weekend_schedule = models.ManyToManyField(DaywiseSchedule,blank=True,related_name='daywise_weekend_schedule')
    infrastruture = models.ManyToManyField(BoardingSchoolInfrastructure,blank=True,related_name='school_infra')
    faq_related_data = JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return f"{self.extended_school.name}"

    class Meta:
        verbose_name = "Boarding School Extended Profile"
        verbose_name_plural = "Boarding School Extended Profiles"

class SchoolClaimRequests(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=15,null=True,blank=True)
    designation = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name.capitalize()} - {self.school.name}"

    class Meta:
        verbose_name = "School Claim Request"
        verbose_name_plural = "School Claim Requests"


class SchoolEqnuirySource(models.Model):
    campaign_name = models.CharField(max_length=80, null=True, blank=True)
    source_name = models.CharField(unique=True,max_length=100)
    related_id = models.CharField(unique=True, max_length=200,null=True,blank=True)
    total_clicks = models.PositiveIntegerField(default=0,null=True,blank=True)

    class Meta:
        verbose_name = "Ad Source ID"
        verbose_name_plural = "Ad Source IDs"

    def __str__(self):
        return f"{self.source_name} : {self.related_id}"

    def save(self, *args, **kwargs):
        if not self.related_id:
            new_id = uuid.uuid4()
            new_id = get_new_id(new_id)
            self.related_id = new_id
        super().save(*args, **kwargs)

def get_new_id(id):
    if SchoolEqnuirySource.objects.filter(related_id=id).exists():
        new_id = uuid.uuid4()
        new_id = get_new_id(new_id)
        return new_id
    else:
        return id

class Coupons(models.Model):
    choice =(('P','Percentage'),
                ('F','Flat'))
    school = models.OneToOneField(
        "schools.SchoolProfile",
        related_name="coupon",on_delete=models.DO_NOTHING)
    school_code = models.CharField(max_length=100,null=True,blank=True)
    school_amount = models.FloatField(null=True,blank=True)
    school_coupon_type = models.CharField(choices=choice,default=None,max_length=10)
    ezyschool_code = models.CharField(max_length=100,null=True,blank=True)
    ezyschool_amount = models.FloatField(null=True,blank=True)
    ezyschool_coupon_type = models.CharField(choices=choice,default=None,max_length=10)
    timestamp=models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.school_code, self.ezyschool_code = self.school_code.upper() if self.school_code else None, self.ezyschool_code.upper() if self.ezyschool_code else None

        if self.school_code and self.ezyschool_code and self.school_code != self.ezyschool_code:
            if self.school_amount and self.school_amount:
                return super(Coupons, self).save(*args, **kwargs)

        elif self.school_code and self.ezyschool_code and self.school_code == self.ezyschool_code:
            if not self.school_amount:
                self.school_code = ""
            if not self.ezyschool_amount:
                self.ezyschool_code = ""
            return f"Both school_code {self.school_code} and Ezyschool_code {self.ezyschool_code} can't be same !"

        elif self.school_code:
            if not self.school_amount:
                return f"school amount can't be empty !"
            else:
                return super(Coupons, self).save(*args, **kwargs)
        elif self.ezyschool_code:
            if not self.ezyschool_amount:
                return f"ezyschool amount can't be empty !"
            else:
                return super(Coupons, self).save(*args, **kwargs)
        elif not self.ezyschool_code and not self.school_code:
            return f"Both school_code {self.school_code} and Ezyschool_code {self.ezyschool_code} can't be empty !"

    def __str__(self):
        return f'{self.id}'


class RequiredOptionalSchoolFields(models.Model):
    school = models.ForeignKey("schools.SchoolProfile", related_name="required_optional_school_fields", on_delete=models.CASCADE)
    required_admission_form_fields = JSONField(null=True, blank=True, default=dict)
    required_child_fields = JSONField(null=True, blank=True, default=dict)
    required_father_fields = JSONField(null=True, blank=True, default=dict)
    required_mother_fields = JSONField(null=True, blank=True, default=dict)
    required_guardian_fields = JSONField(null=True, blank=True, default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Required Optional Application Field"
        verbose_name_plural = "Required Optional Application Fields"
