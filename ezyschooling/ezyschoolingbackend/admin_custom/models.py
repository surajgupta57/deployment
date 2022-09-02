from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from schools.models import *
from accounts.models import *
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField

class UserType(models.Model):
    category_name = models.CharField(max_length=30)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "User Type"
        verbose_name_plural = "User Types"


class CAdminUser(models.Model):
    user_ptr = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_executive = models.BooleanField(default=False)
    user_type = models.ForeignKey("admin_custom.UserType", on_delete=models.SET_NULL, null=True, blank=True)
    phone_no = models.CharField(max_length=255, null=True, blank=True)
    designation = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.user_ptr.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class SalesCAdminUser(models.Model):
    user = models.ForeignKey("admin_custom.CAdminUser", on_delete=models.CASCADE)
    city = models.ForeignKey(
        "schools.city",
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
    district_region = models.ForeignKey(
        "schools.DistrictRegion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        "schools.States", on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_schools = models.ManyToManyField(
        "schools.SchoolProfile", blank=True, related_name="assigned_schools")

    def __str__(self):
        return self.user.user_ptr.username

    class Meta:
        verbose_name = "Sales User"
        verbose_name_plural = "Salses Users"

# class CAdminUser(models.Model):
#     # ID=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
#     user_ptr=models.OneToOneField(User,on_delete=models.CASCADE)
#     class Meta:
#         verbose_name = "Sales User"
#         verbose_name_plural = "Sales Users"


# class Token(AuthToken):
#     key = models.CharField("Key", max_length=40, db_index=True, unique=True)
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name="auth_token",
#         on_delete=models.CASCADE,
#         verbose_name="User",
#     )

class CounselorCAdminUser(models.Model):
    user = models.ForeignKey("admin_custom.CAdminUser", on_delete=models.CASCADE)
    city = models.ManyToManyField(
        "schools.City", blank=True
    )
    district = models.ManyToManyField(
        "schools.District", blank=True
    )
    district_region = models.ManyToManyField(
        "schools.DistrictRegion", blank=True
    )
    online_schools = models.BooleanField(default=False)
    boarding_schools = models.BooleanField(default=False)
    cart_data_permission = models.BooleanField(default=False)
    enquiry_data_permission = models.BooleanField(default=False)
    school_profile_data_permission = models.BooleanField(default=False)
    unassigned_call_data_permission = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.user.user_ptr.username}"

    class Meta:
        verbose_name = "Counsellor User"
        verbose_name_plural = "Counsellor Users"


class MasterActionCategory(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Action Category"
        verbose_name_plural = "Action Categories"


class ActionSection(models.Model):
    category = models.ForeignKey(MasterActionCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="enquiry_action_type")
    name = models.CharField(max_length=50)
    slug = models.SlugField(null=True,blank=True)
    requires_datetime = models.BooleanField(default=False)
    considered_as_call_done = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(ActionSection, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Action"
        verbose_name_plural = "Actions"

    def __str__(self):
        return self.name + "(" + self.category.name +')'

class SubActionSection(models.Model):
    action_realtion = models.ForeignKey(ActionSection, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="head_action")
    name = models.CharField(max_length=50)
    slug = models.SlugField(null=True,blank=True)
    requires_datetime = models.BooleanField(default=False)
    considered_as_call_done = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(SubActionSection, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Sub Action"
        verbose_name_plural = "Sub Actions"

    def __str__(self):
        return f"{self.name} ( {self.action_realtion.name} )"


class CommentSection(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_counseling_comment",
                             verbose_name="User")
    child = models.ForeignKey(Child, null=True, blank=True, on_delete=models.SET_NULL, related_name="comment_wrt_child",
                             verbose_name="Users' Child")
    counseling = models.ForeignKey(CounselorCAdminUser, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="counseling_to_user",
                                   verbose_name="counseling User")  # counseling user
    enquiry_comment = models.ForeignKey(SchoolEnquiry, null=True, blank=True, on_delete=models.SET_NULL, related_name="enquiry_comment_data") # only for not registered user
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="parent_call_scheduled_comment_data")
    comment = models.TextField(max_length=500)
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    class Meta:
        verbose_name = "Counsellor Comment"
        verbose_name_plural = "Counsellor Comments"

    def __str__(self):
        return self.counseling.user.user_ptr.name


class CounselingAction(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_for_counseling",verbose_name="User")
    counseling_user = models.ForeignKey(CounselorCAdminUser, null=True, on_delete=models.SET_NULL,
                                        related_name="counseling_user_action",
                                        verbose_name="Counseling Action User")
    enquiry_data = models.ForeignKey(SchoolEnquiry, null=True, blank=True, on_delete=models.SET_NULL, related_name="enquiry_data") # only for not registered user
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="parent_call_scheduled_counseling_data")
    enquiry_action = models.ForeignKey(ActionSection, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="enquiry_action")
    action = models.ForeignKey(ActionSection, null=True, blank=True, on_delete=models.SET_NULL)
    sub_actiom = models.ForeignKey(SubActionSection, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry_scheduled_time = models.DateTimeField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    first_action = JSONField(null=True, blank=True, default=dict)
    action_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    action_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Counsellor Action"
        verbose_name_plural = "Counsellor Actions"

    def __str__(self):
        if self.user:
            return self.user.name
        elif self.call_scheduled_by_parent:
            return self.call_scheduled_by_parent.name
        else:
            return str(self.id)


class LeadGenerated(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="User")
    counseling_user = models.ForeignKey(CounselorCAdminUser, null=True, on_delete= models.SET_NULL,verbose_name="Counseling Action User")
    enquiry = models.ForeignKey(SchoolEnquiry, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="enquiry_data")
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="parent_call_scheduled_lead_data")
    user_name = models.CharField(help_text="User's Name", max_length=150, null=True,blank=True)
    user_phone_number = models.TextField(help_text="number", null=True,blank=True)
    user_email = models.TextField(help_text="email", null=True,blank=True)
    classes = models.CharField(help_text="classes", max_length=60, null=True,blank=True)
    budget = models.CharField(help_text="budget", max_length=75, null=True,blank=True)
    location = models.CharField(help_text="location", max_length=150, null=True,blank=True)
    lead_for = models.ManyToManyField("schools.SchoolProfile" ,blank=True, related_name='lead_generated_schools')
    lead_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    lead_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Lead Generated"
        verbose_name_plural = "Leads Generated"

    def __str__(self):
        if self.user:
            return self.user.name
        elif self.enquiry:
            return self.enquiry.parent_name
        elif self.call_scheduled_by_parent:
            return self.call_scheduled_by_parent.name
        else:
            return str(self.id)

class VisitScheduleData(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="User")
    counseling_user = models.ForeignKey(CounselorCAdminUser, null=True, on_delete= models.SET_NULL,verbose_name="Counseling Action User")
    enquiry = models.ForeignKey(SchoolEnquiry, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="enquiry_data")
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="parent_call_scheduled_visit_scheduled_data")
    user_name = models.CharField(help_text="User's Name", max_length=150, null=True,blank=True)
    user_phone_number = models.TextField(help_text="number", null=True,blank=True)
    user_email = models.TextField(help_text="email", null=True,blank=True)
    walk_in_for = models.ManyToManyField("schools.SchoolProfile" ,blank=True, related_name='walk_in_schools')
    walk_in_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    walk_in_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Visit Scheduled"
        verbose_name_plural = "Visits Scheduled"

    def __str__(self):
        if self.user:
            return self.user.name
        elif self.enquiry:
            return self.enquiry.parent_name
        elif self.call_scheduled_by_parent:
            return self.call_scheduled_by_parent.name
        else:
            return str(self.id)

class AdmissionDoneData(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="User")
    counseling_user = models.ForeignKey(CounselorCAdminUser, null=True, on_delete= models.SET_NULL,verbose_name="Counseling Action User")
    enquiry = models.ForeignKey(SchoolEnquiry, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="enquiry_data")
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="parent_call_scheduled_admission_done_data")
    user_name = models.CharField(help_text="User's Name", max_length=150, null=True,blank=True)
    child_name = models.CharField(help_text="Child Name", max_length=50, null=True,blank=True)
    user_phone_number = models.TextField(help_text="number", null=True,blank=True)
    user_email = models.TextField(help_text="email", null=True,blank=True)
    admission_done_for = models.ManyToManyField("schools.SchoolProfile" ,blank=True, related_name='admission_done_in_schools')
    admissiomn_done_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    admissiomn_done_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Admission Done"
        verbose_name_plural = "Admissions Done"

    def __str__(self):
        if self.user:
            return self.user.name
        elif self.enquiry:
            return self.enquiry.parent_name
        elif self.call_scheduled_by_parent:
            return self.call_scheduled_by_parent.name
        else:
            return str(self.id)

class CounsellorDailyCallRecord(models.Model):
    counsellor = models.ForeignKey(CounselorCAdminUser, null=True,blank=True, on_delete=models.SET_NULL,verbose_name="Counsellor")
    total_number_of_calls = models.PositiveIntegerField(default=0)
    anonymous_enquiry_calls = models.PositiveIntegerField(default=0)
    user_calls = models.PositiveIntegerField(default=0)
    first_call_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    latest_call_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Counsellor Daily Call Reocord"
        verbose_name_plural = "Counsellors Daily Call Reocord"

    def __str__(self):
        return f"{self.counsellor.user.user_ptr.name} - {self.total_number_of_calls} - {self.first_call_at}"

class SchoolDashboardMasterActionCategory(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "School Action Category"
        verbose_name_plural = "School Action Categories"

class SchoolDashboardActionSection(models.Model):
    category = models.ForeignKey(SchoolDashboardMasterActionCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="school_action_type")
    name = models.CharField(max_length=50)
    slug = models.SlugField(null=True,blank=True)
    requires_datetime = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(SchoolDashboardActionSection, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "School Action"
        verbose_name_plural = "School Actions"

    def __str__(self):
        return F"{self.name} ({self.category.name})"

class SchoolCommentSection(models.Model):
    action = models.ForeignKey(CounselingAction, null=True, blank=True, on_delete=models.SET_NULL, related_name="counselling_action_relation_c",verbose_name="Counsellor's Action(C)")
    lead = models.ForeignKey(LeadGenerated, null=True, blank=True, on_delete=models.SET_NULL)
    visit = models.ForeignKey(VisitScheduleData, null=True, blank=True, on_delete=models.SET_NULL)
    admissions = models.ForeignKey(AdmissionDoneData, null=True, blank=True, on_delete=models.SET_NULL)
    counsellor = models.ForeignKey(CounselorCAdminUser, null=True, blank=True, on_delete=models.SET_NULL,verbose_name="counseling User")
    school = models.ForeignKey("schools.SchoolProfile",null=True, blank=True, on_delete=models.SET_NULL)
    comment = models.TextField(max_length=500)
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    class Meta:
        verbose_name = "School Comment"
        verbose_name_plural = "School Comments"

    def __str__(self):
        return self.school.name

class SchoolAction(models.Model):
    parent_action = models.ForeignKey(CounselingAction, null=True, blank=True, on_delete=models.SET_NULL, related_name="counselling_action_relation_a",verbose_name="Counsellor's Action(A)")
    counsellor = models.ForeignKey(CounselorCAdminUser, null=True, on_delete=models.SET_NULL,verbose_name="Counsellor User")
    school = models.ForeignKey("schools.SchoolProfile",null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey(LeadGenerated, null=True, blank=True, on_delete=models.SET_NULL)
    visit = models.ForeignKey(VisitScheduleData, null=True, blank=True, on_delete=models.SET_NULL)
    admissions = models.ForeignKey(AdmissionDoneData, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.ForeignKey(SchoolDashboardActionSection, null=True, blank=True, on_delete=models.SET_NULL)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    action_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    action_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        verbose_name = "Action Performed by School"
        verbose_name_plural =  "Actions Performed by School"

    def __str__(self):
        return self.school.name

class SchoolPerformedActionOnEnquiry(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry = models.ForeignKey("schools.SchoolEnquiry",null=True,blank=True,on_delete=models.SET_NULL)
    action = models.ForeignKey(SchoolDashboardActionSection, null=True, blank=True, on_delete=models.SET_NULL)
    child_name = models.CharField(help_text="Child Name", max_length=150, null=True,blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    action_created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    action_updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    def __str__(self):
        return self.enquiry.school.name


class SchoolPerformedCommentEnquiry(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry = models.ForeignKey("schools.SchoolEnquiry",null=True,blank=True,on_delete=models.SET_NULL)
    comment = models.TextField(null=True,blank=True)
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return self.enquiry.school.name

class DatabaseCAdminUser(models.Model):
    user = models.ForeignKey("admin_custom.CAdminUser", on_delete=models.CASCADE)
    delete_permission = models.BooleanField(default=False)
    edit_permission = models.BooleanField(default=False)

    def __str__(self):
        return self.user.user_ptr.username

    class Meta:
        verbose_name = "DB Team User"
        verbose_name_plural = "DB Team Users"

class ViewedParentPhoneNumberBySchool(models.Model):
    school = models.ForeignKey("schools.SchoolProfile", null=True, blank=True, on_delete=models.SET_NULL)
    school_view = models.ForeignKey("schools.SchoolView", null=True, blank=True, on_delete=models.SET_NULL)
    school_performed_action_on_enquiry = models.ForeignKey(SchoolPerformedActionOnEnquiry, null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey(LeadGenerated, null=True, blank=True, on_delete=models.SET_NULL)
    visit = models.ForeignKey(VisitScheduleData, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry = models.ForeignKey("schools.SchoolEnquiry", null=True, blank=True, on_delete=models.SET_NULL)
    parent_called = models.ForeignKey("schools.SchoolContactClickData", null=True, blank=True, on_delete=models.SET_NULL)
    ongoing_application = models.ForeignKey("admission_forms.ChildSchoolCart", null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return self.school.name

class ParentCallScheduled(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(
        "schools.city",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=50, null=True,blank=True)
    phone = models.CharField(max_length=20, null=True,blank=True)
    message = models.CharField(max_length=512, null=True,blank=True)
    time_slot = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return self.name


class TransferredCounsellor(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry = models.ForeignKey("schools.SchoolEnquiry", null=True, blank=True, on_delete=models.SET_NULL)
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="transferred_counsellor_parent_call_scheduled")
    transfer_by = models.ForeignKey(CounselorCAdminUser, null=True, on_delete=models.SET_NULL, related_name='transferred_to', verbose_name="Transfer By")
    transfer_to = models.ForeignKey(CounselorCAdminUser, null=True, on_delete=models.SET_NULL, related_name='transferred_by', verbose_name="Transfer To")
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return "Transferred to " + self.transfer_to.user.user_ptr.name


class SharedCounsellor(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    enquiry = models.ForeignKey("schools.SchoolEnquiry", null=True, blank=True, on_delete=models.SET_NULL)
    call_scheduled_by_parent = models.ForeignKey("admin_custom.ParentCallScheduled", null=True, blank=True, on_delete=models.SET_NULL, related_name="shared_counsellor_parent_call_scheduled")
    counsellor = models.ForeignKey(CounselorCAdminUser, null=True, on_delete=models.SET_NULL, related_name='previous_counsellor', verbose_name="Counsellor")
    shared_with = models.ManyToManyField(CounselorCAdminUser,blank=True, related_name='shared_with')
    timestamp = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return "Shared By " + self.counsellor.user.user_ptr.name
