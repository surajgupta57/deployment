from import_export import resources
from .models import LeadGenerated, AdmissionDoneData, VisitScheduleData,CounselingAction
from import_export.fields import Field
from .utils import get_user_phone_numbers

class CounselingActionResource(resources.ModelResource):
    counseling_user = Field()
    username = Field()
    phone_no = Field()
    enquiry_query = Field()
    school = Field()
    action = Field()
    sub_action = Field()
    class Meta:
        model = CounselingAction
        fields = [
            "counseling_user",
            "username",
            "phone_no",
            "enquiry_query",
            "school",
            "action",
            "sub_action",
            "action_updated_at",
        ]

    def dehydrate_school(self,obj):
        if obj.enquiry_data:
            return obj.enquiry_data.school.name
        else:
            return "-"

    def dehydrate_username(self,obj):
        if obj.user:
            return obj.user.name or obj.user.username
        elif obj.enquiry_data:
            return obj.enquiry_data.parent_name
        else:
            return "-"
    
    def dehydrate_enquiry_query(self,obj):
        if obj.enquiry_data:
            return obj.enquiry_data.query 
        else:
            return "-"

    def dehydrate_phone_no(self,obj):
        if obj.user:
            a = ""
            for i in get_user_phone_numbers(obj.user.id):
                a += f"{i}," 
            return a[0:-1]
        elif obj.enquiry_data:
            return obj.enquiry_data.phone_no
        else:
            return "-"

    def dehydrate_counseling_user(self,obj):
        if obj.counseling_user:
            return obj.counseling_user.user.user_ptr.name or obj.counseling_user.user.user_ptr.username
        else:
            return "-"

    def dehydrate_action(self,obj):
        if obj.enquiry_action:
            return obj.enquiry_action.name
        elif obj.action:
            return obj.action.name 
        else:
            return "-"

    def dehydrate_sub_action(self,obj):
        if obj.sub_actiom:
            return obj.sub_actiom.name
        else:
            return "-"

class LeadGeneratedResource(resources.ModelResource):
    school = Field()
    enquiry = Field()
    location = Field()
    parent_name = Field()

    class Meta:
        model = LeadGenerated
        fields = [
            "school",
            "parent_name",
            "enquiry",
            "user_email",
            "user_phone_number",
            "classes",
            "budget",
            "location",
            "lead_updated_at",
        ]

    def dehydrate_parent_name(self,obj):
        if obj.user:
            return obj.user.name or obj.user.username
        elif obj.enquiry:
            return obj.enquiry.parent_name
        else:
            return "-"

    def dehydrate_school(self, obj):
        return ", ".join([school.name for school in obj.lead_for.all()])

    def dehydrate_enquiry(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name or obj.enquiry.user.name
        else:
            return "N/A"

    def dehydrate_location(self, obj):
        if obj.location:
            return obj.location
        else:
            return ""

class AdmissionDoneDataResource(resources.ModelResource):
    school = Field()
    enquiry = Field()
    parent_name = Field()
    done_by = Field()

    class Meta:
        model = AdmissionDoneData
        fields = [
            "school",
            "parent_name",
            "enquiry",
            "user_email",
            "user_phone_number",
            "done_by",
            "admissiomn_done_updated_at",
        ]
    def dehydrate_parent_name(self,obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.enquiry:
            return obj.enquiry.parent_name.title()
        else:
            return "-"

    def dehydrate_school(self, obj):
        return ", ".join([school.name for school in obj.admission_done_for.all()])

    def dehydrate_enquiry(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name.title() or obj.enquiry.user.name.title()
        else:
            return ""

    def dehydrate_done_by(self, obj):
        if obj.counseling_user:
            return obj.counseling_user.user.user_ptr.name.title()
        else:
            return obj.admission_done_for.all().first().name.title()

class VisitScheduleDataResource(resources.ModelResource):
    school = Field()
    enquiry = Field()
    parent_name = Field()
    scheduled_by = Field()

    class Meta:
        model = VisitScheduleData
        fields = [
            "school",
            "parent_name",
            "enquiry",
            "user_email",
            "user_phone_number",
            "walk_in_updated_at",
        ]
    def dehydrate_parent_name(self,obj):
        if obj.user:
            return obj.user.name.title() or obj.user.username.title()
        elif obj.enquiry:
            return obj.enquiry.parent_name.title()
        else:
            return "-"
    def dehydrate_school(self, obj):
        return ", ".join([school.name for school in obj.walk_in_for.all()])

    def dehydrate_enquiry(self, obj):
        if obj.enquiry:
            return obj.enquiry.parent_name.title() or obj.enquiry.user.name.title()
        else:
            return ""

    def dehydrate_scheduled_by(self, obj):
        if obj.counseling_user:
            return obj.counseling_user.user.user_ptr.name.title()
        else:
            return obj.walk_in_for.all().first().name.title()
