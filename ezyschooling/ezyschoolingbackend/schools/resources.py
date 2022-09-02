from accounts.models import User
from django.db.models import F
from import_export import resources
from import_export.fields import Field

from admin_custom.models import ViewedParentPhoneNumberBySchool, AdmissionDoneData, VisitScheduleData, LeadGenerated
from parents.models import ParentProfile,ParentAddress
from admission_forms.models import ChildSchoolCart, SchoolApplication
from .models import *


class SchoolViewResource(resources.ModelResource):
    parent = Field()
    email = Field()
    phone = Field()
    # added_in_cart = Field()
    location = Field()

    class Meta:
        model = SchoolView
        fields = [
            "school",
            # "count",
            "updated_at",
        ]

    def dehydrate_email(self, obj):
        return obj.user.email

    def dehydrate_school(self, obj):
        return obj.school.name.title()

    def dehydrate_parent(self, obj):
        parent_id = int(obj.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        return parent.name

    def dehydrate_phone(self, obj):
        parent = ParentProfile.objects.get(id=obj.user.current_parent)
        school = SchoolProfile.objects.get(id=obj.school.id)
        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, school_view=obj).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            return parent.phone
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = parent.phone.replace(" ", "").split(",") if parent.phone else []
            list2 = []
            if len(n)>0:
                for a in n:
                    list1 = []
                    list1[:0] = a
                    list1.reverse()
                    for index, val in enumerate(list1):
                        if index == 4:
                            break
                        else:
                            list1[index] = 'x'
                    list1.reverse()
                    hidden_number = ''.join(map(str, list1))
                    list2.append(hidden_number)
                hidden_number = ', '.join(map(str, list2))
            else:
                hidden_number = None
            return hidden_number

    def dehydrate_location(self,obj):
        parent = ParentProfile.objects.get(id=obj.user.current_parent)
        address = parent.parent_address.all().first()
        if(address):
            return address.street_address
        else:
            return "N/A"


class SchoolOngoingApplicationsResource(resources.ModelResource):
    parent = Field()
    email = Field()
    phone = Field()
    location = Field()

    class Meta:
        model = ChildSchoolCart
        fields = [
            "school",
            "timestamp",
        ]

    def dehydrate_email(self, obj):
        return obj.user.email

    def dehydrate_school(self, obj):
        return obj.school.name.title()

    def dehydrate_parent(self, obj):
        parent_id = int(obj.user.current_parent)
        parent = ParentProfile.objects.get(pk=parent_id)
        return parent.name

    def dehydrate_phone(self, obj):
        parent = ParentProfile.objects.get(id=obj.user.current_parent)
        school = SchoolProfile.objects.get(id=obj.school.id)
        viewed_no_count = ViewedParentPhoneNumberBySchool.objects.filter(school=school, ongoing_application=obj).count()
        if viewed_no_count > 0 or not school.phone_number_cannot_viewed:
            return parent.phone
        elif viewed_no_count == 0 or school.phone_number_cannot_viewed:
            n = parent.phone.replace(" ", "").split(",") if parent.phone else []
            list2 = []
            if len(n)>0:
                for a in n:
                    list1 = []
                    list1[:0] = a
                    list1.reverse()
                    for index, val in enumerate(list1):
                        if index == 4:
                            break
                        else:
                            list1[index] = 'x'
                    list1.reverse()
                    hidden_number = ''.join(map(str, list1))
                    list2.append(hidden_number)
                hidden_number = ', '.join(map(str, list2))
            else:
                hidden_number = None
            return hidden_number


    def dehydrate_location(self,obj):
        parent = ParentProfile.objects.get(id=obj.user.current_parent)
        address = parent.parent_address.all().first()
        if(address):
            return address.street_address
        else:
            return "N/A"

class SchoolProfileResource(resources.ModelResource):
    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "email",
            "phone_no",
            "website",
            "latitude",
            "longitude",
            "short_address",
            "street_address",
            "zipcode"
            "state",
            "district",
            "district_region",
            "school_city",
            "school_state",
            "school_country",

        ]

    def dehydrate_district(self, obj):
        if obj.district:
            return obj.district.name
        else:
            return ""
    def dehydrate_district_region(self, obj):
        if obj.district_region:
            return obj.district_region.name
        else:
            return ""
    def dehydrate_school_city(self, obj):
        if obj.school_city:
            return obj.school_city.name
        else:
            return ""
    def dehydrate_school_state(self, obj):
        if obj.school_state:
            return obj.school_state.name
        else:
            return ""
    def dehydrate_school_country(self, obj):
        if obj.school_country:
            return obj.school_country.name
        else:
            return ""

class SchoolDistrictRegionResource(resources.ModelResource):
    class Meta:
        model = DistrictRegion
        fields = [
            "name",
            "city",
            "district",
            "state",
            "country",
            "district",
            "pincode",
        ]

    def dehydrate_city(self, obj):
        if obj.city:
            return obj.city.name
        else:
            return ""

    def dehydrate_district(self, obj):
        if obj.district:
            return obj.district.name
        else:
            return ""
    def dehydrate_state(self, obj):
        if obj.state:
            return obj.state.name
        else:
            return ""
    def dehydrate_country(self, obj):
        if obj.country:
            return obj.country.name
        else:
            return ""
    def dehydrate_pincode(self, obj):
        if obj.pincode:
            data = ''
            for item in obj.pincode.all():
                if data == '':
                    data = item.pincode
                else:
                    data = data + ', ' + item.pincode
            return data
        else:
            return ""

class SchoolEnquiryResource(resources.ModelResource):
    parent_name = Field()
    phone = Field()
    email = Field()


    class Meta:
        model = SchoolEnquiry
        fields = [
            "school",
            "query",
            "class_relation",
            "source",
            "timestamp",
            "school__region__name"
        ]

    def dehydrate_school(self, obj):
        return obj.school.name

    def dehydrate_class_relation(self, obj):
        return obj.class_relation.name if obj.class_relation else "N/A"

    def dehydrate_parent_name(self, obj):
        if obj.user and ParentProfile.objects.filter(id=obj.user.current_parent).exists():
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            return parent.name
        else:
            return obj.parent_name

    def dehydrate_phone(self, obj):
        if obj.user and ParentProfile.objects.filter(id=obj.user.current_parent).exists():
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            if parent.phone:
                return parent.phone
        return obj.phone_no

    def dehydrate_email(self, obj):
        if obj.user and ParentProfile.objects.filter(id=obj.user.current_parent).exists():
            parent = ParentProfile.objects.get(id=obj.user.current_parent)
            return parent.email
        else:
            return obj.email

    def dehydrate_monthly_budget(self, obj):
        if obj.user and ParentAddress.objects.filter(parent=obj.user.current_parent).exists():
            parent = ParentAddress.objects.get(parent=obj.user.current_parent)
            return parent.monthly_budget
        else:
            return "NA"


class VideoTourLinksResource(resources.ModelResource):
    school_name = Field()

    class Meta:
        model = VideoTourLinks

    def dehydrate_school_name(self,obj):
         return obj.school.school


class SchoolEnquirySourceResource(resources.ModelResource):
    user = Field()
    enquiries = Field()
    cart = Field()
    applications = Field()
    lead_generated = Field()
    visit_scheduled = Field()
    admission_done = Field()
    school_signup = Field()
    class Meta:
        model = SchoolEqnuirySource
        fields = [
            "id",
            "source_name",
            "total_clicks",
            "user",
            "enquiries",
            "cart",
            "applications",
            "lead_generated",
            "visit_scheduled",
            "admission_done",
            "school_signup"
        ]

    def dehydrate_enquiries(self, obj):
        all_city = City.objects.all()
        data = []
        for city in all_city:
            if SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=True).count() > 0 or SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=False).count() > 0:
                data.append({'City': city.name,
                            "Collab": SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=True).count(),
                            "Non-Collab": SchoolEnquiry.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug,school__collab=False).count(),
                })
        if len(data)>0:
            return data
        return "-"

    def dehydrate_user(self, obj):
        return User.objects.filter(ad_source=obj.source_name.title()).count()

    def dehydrate_cart(self, obj):
        return ChildSchoolCart.objects.filter(ad_source=obj.source_name.title()).count()

    def dehydrate_applications(self, obj):
        all_city = City.objects.all()
        data = []
        for city in all_city:
            if SchoolApplication.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug).count()>0:
                data.append({'City': city.name,
                            "Total": SchoolApplication.objects.filter(ad_source=obj.source_name.title(), school__school_city__slug=city.slug).count(),
                })

        if len(data) > 0:
            return data
        return "-"

    def dehydrate_lead_generated(self, obj):
        ad_src = obj.source_name.title()
        adm_objs, adm_cnt = [], 0
        visits_objs, visits_cnt = [], 0
        leads_objs, leads_cnt = [], 0
        if AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
            Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            adm_objs = [obj for obj in AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if VisitScheduleData.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            visits_objs = [obj for obj in VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if LeadGenerated.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            leads_objs = [obj for obj in
                          LeadGenerated.objects.filter(
                              Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                              Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]
            leads_cnt = LeadGenerated.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).count()

        remove_visit_cnt = 0
        remove_lead_cnt = 0
        for adm_usr in adm_objs:
            for visit_usr in visits_objs:
                if adm_usr.user and visit_usr.user and adm_usr.user.id == visit_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and visit_usr.enquiry and adm_usr.enquiry.id == visit_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
            for lead_usr in leads_objs:
                if adm_usr.user and lead_usr.user and adm_usr.user.id == lead_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and lead_usr.enquiry and adm_usr.enquiry.id == lead_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
        for lead_usr in leads_objs:
            for visit_usr in visits_objs:
                if lead_usr.user and visit_usr.user and lead_usr.user.id == visit_usr.user.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1
                if lead_usr.enquiry and visit_usr.enquiry and lead_usr.enquiry.id == visit_usr.enquiry.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1

        leads_cnt = leads_cnt - remove_lead_cnt
        return leads_cnt

    def dehydrate_visit_scheduled(self, obj):
        ad_src = obj.source_name.title()
        adm_objs, adm_cnt = [], 0
        visits_objs, visits_cnt = [], 0
        leads_objs, leads_cnt = [], 0
        if AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
            Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            adm_objs = [obj for obj in AdmissionDoneData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        if VisitScheduleData.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            visits_objs = [obj for obj in VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]
            visits_cnt = VisitScheduleData.objects.filter(
                Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).count()

        if LeadGenerated.objects.filter(Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False).exists():
            leads_objs = [obj for obj in
                          LeadGenerated.objects.filter(
                              Q(user__ad_source=ad_src) | Q(enquiry__ad_source=ad_src)).filter(
                              Q(user__isnull=True) | Q(enquiry__isnull=True)).filter(counseling_user__isnull=False)]

        remove_visit_cnt = 0
        remove_lead_cnt = 0
        for adm_usr in adm_objs:
            for visit_usr in visits_objs:
                if adm_usr.user and visit_usr.user and adm_usr.user.id == visit_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and visit_usr.enquiry and adm_usr.enquiry.id == visit_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        pass
            for lead_usr in leads_objs:
                if adm_usr.user and lead_usr.user and adm_usr.user.id == lead_usr.user.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
                if adm_usr.enquiry and lead_usr.enquiry and adm_usr.enquiry.id == lead_usr.enquiry.id:
                    if adm_usr.admissiomn_done_updated_at > lead_usr.lead_updated_at:
                        remove_lead_cnt = remove_lead_cnt + 1
                    else:
                        pass
        for lead_usr in leads_objs:
            for visit_usr in visits_objs:
                if lead_usr.user and visit_usr.user and lead_usr.user.id == visit_usr.user.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1
                if lead_usr.enquiry and visit_usr.enquiry and lead_usr.enquiry.id == visit_usr.enquiry.id:
                    if lead_usr.lead_updated_at > visit_usr.walk_in_updated_at:
                        remove_visit_cnt = remove_visit_cnt + 1
                    else:
                        remove_lead_cnt = remove_lead_cnt + 1

        visits_cnt = visits_cnt - remove_visit_cnt
        return visits_cnt

    def dehydrate_admission_done(self,obj):
        return AdmissionDoneData.objects.filter(user__ad_source=obj.source_name.title(),counseling_user__isnull=False,enquiry__isnull=True).count() + AdmissionDoneData.objects.filter(enquiry__ad_source=obj.source_name.title(),counseling_user__isnull=False,user__isnull=True).count()

    def dehydrate_school_signup(self, obj):
        return SchoolProfile.objects.filter(ad_source=obj.source_name.title()).count()
