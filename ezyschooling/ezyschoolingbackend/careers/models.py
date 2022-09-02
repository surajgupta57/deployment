from django.db import models
from taggit_selectize.managers import TaggableManager
from tags.models import Tagged, SkillTagged, MustSkillTagged
from .utils import *
# Create your models here.

class JobType(models.Model):
    name = models.CharField("Job type", help_text="Ex. Full Time / Internship",max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Types"
        verbose_name_plural = "Job Type"

    def __str__(self):
        return f"Type - {self.name} & Rank - {self.rank}"

class JobDomain(models.Model):
    name = models.CharField("Job Domain", help_text="Ex. Tech / Marketing", max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Domains"
        verbose_name_plural = "Job Domain"

    def __str__(self):
        return f"Domain - {self.name} & Rank - {self.rank}"

class JobLocation(models.Model):
    name = models.CharField("Location Name", help_text="Ex. Delhi / Banglore", max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Locations"
        verbose_name_plural = "Job Location"

    def __str__(self):
        return f"Location - {self.name} & Rank - {self.rank}"

class JobExperienceRange(models.Model):
    range = models.CharField("Experience Range", help_text="Ex. Fresher / 2 Years / 2 - 4 Years", max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Experience Ranges"
        verbose_name_plural = "Job Experience Range"

    def __str__(self):
        return f"Range - {self.range} & Rank - {self.rank}"

class JobSalary(models.Model):
    salary = models.CharField("Job Salary", help_text="Ex. 3LPA / 6LPA", max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Salaries"
        verbose_name_plural = "Job Salary"

    def __str__(self):
        return f"Salary - {self.salary} & Rank - {self.rank}"

class JobJoiningType(models.Model):
    type = models.CharField("Joining Type", help_text="Ex. Immediate / 0 - 15 Days", max_length=200)
    rank = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Job Joining Types"
        verbose_name_plural = "Job Joining type"

    def __str__(self):
        return f"Type - {self.type} & Rank - {self.rank}"

class JobProfile(models.Model):
    STATUS = (("Draft", "Draft Job"), ("Active", "Active Job"))
    name = models.CharField("Job Profile Name", help_text="Ex. Software Developer / Sales Manager", max_length=200)
    experience = models.ForeignKey(JobExperienceRange, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(JobLocation, on_delete=models.SET_NULL, null=True, blank=True)
    joining_type = models.ForeignKey(JobJoiningType, on_delete=models.SET_NULL, null=True, blank=True)
    job_domain = models.ForeignKey(JobDomain, on_delete=models.SET_NULL, null=True, blank=True)
    locality = models.CharField("Locality / District", help_text="Ex. Sector 62 / Central Delhi", max_length=200, null=True, blank=True)
    must_have_skills = TaggableManager("Must Have Skills", help_text="Atleast add one" ,through=MustSkillTagged)
    skills = TaggableManager("Add On Skills", help_text="Atleast add one" ,through=SkillTagged)
    description = models.TextField("Job Description", null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location} - {self.experience}"

    class Meta:
        verbose_name = "Job Profiles"
        verbose_name_plural = "Job Profile"

class AppliedJobs(models.Model):
    profile = models.ForeignKey(JobProfile, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField("Full Name", help_text="Ex. Joen Dave", max_length=250)
    email = models.EmailField("Email ID", help_text="Ex. user@domain.com", max_length=200)
    city = models.CharField("City", help_text="Ex. Delhi / Bhubaneswar", max_length=200)
    experience = models.CharField("Experience", help_text="Ex. Fresher / 1 Year", max_length=50)
    notice_period = models.CharField("Notice Period", help_text="Ex. Immediate / 15 Days", max_length=150)
    mobile_number = models.CharField("Contact Number", help_text="Ex. 9837xx-xxx01", max_length=10)
    resume = models.FileField("Resume", upload_to=applied_resume_upload_path, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.mobile_number} - {self.profile.name}"

    class Meta:
        verbose_name = "Applied Job Data"
        verbose_name_plural = "Applied Job Data"
