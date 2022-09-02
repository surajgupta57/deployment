from import_export import resources
from import_export.fields import Field

from parents.models import ParentProfile

from .models import ChildSchoolCart, FormReceipt


class ChildSchoolCartResource(resources.ModelResource):
    parent = Field()
    father_phone = Field()
    mother_phone = Field()
    guardian_phone=Field()
    email = Field()
    apply_for = Field()

    class Meta:
        model = ChildSchoolCart
        fields = [
            "school",
            "timestamp"
        ]

    def dehydrate_apply_for(self, obj):
        return obj.child.class_applying_for

    def dehydrate_email(self, obj):
        return obj.form.user.email

    def dehydrate_parent(self, obj):
        return obj.form.user.name

    def dehydrate_school(self, obj):
        return obj.school.name.title()

    def dehydrate_father_phone(self, obj):
        if obj.form.father:
            father = ParentProfile.objects.get(id=obj.form.father.id)
            return father.phone
        else:
            return 'N/A'

    def dehydrate_mother_phone(self, obj):
        if obj.form.mother:
            mother = ParentProfile.objects.get(id=obj.form.mother.id)
            return mother.phone
        else:
            return 'N/A'

    def dehydrate_guardian_phone(self, obj):
        if obj.form.guardian:
            guardian = ParentProfile.objects.get(id=obj.form.guardian.id)
            return guardian.phone
        else:
            return 'N/A'

class CommonRegistrationFormresource(resources.ModelResource):
    father = Field()
    mother = Field()
    guardian = Field()
    child = Field()
    father_phone = Field()
    mother_phone = Field()
    guardian_phone=Field()
    email = Field()
    short_address=Field()
    city=Field()
    state=Field()
    pincode=Field()
    category=Field()

    def dehydrate_email(self, obj):
        if obj.user:
            return obj.user.email
        else:
            return 'N/A'

    def dehydrate_father(self, obj):
        if obj.father:
            return obj.father.name
        else:
            return 'N/A'

    def dehydrate_mother(self, obj):
        if obj.mother:
            return obj.mother.name
        else:
            return 'N/A'


    def dehydrate_guardian(self, obj):
        if obj.guardian:
            return obj.guardian.name
        else:
            return 'N/A'

    def dehydrate_school(self, obj):
        return obj.school.name.title()

    def dehydrate_father_phone(self, obj):
        if obj.father:
            father = ParentProfile.objects.get(id=obj.father.id)
            return father.phone
        else:
            return 'N/A'

    def dehydrate_mother_phone(self, obj):
        if obj.mother:
            mother = ParentProfile.objects.get(id=obj.mother.id)
            return mother.phone
        else:
            return 'N/A'


    def dehydrate_guardian_phone(self, obj):
        if obj.guardian:
            guardian = ParentProfile.objects.get(id=obj.guardian.id)
            return guardian.phone
        else:
            return 'N/A'

    def dehydrate_child(self,obj):
         if obj.child:
            return obj.child.name
         else:
            return 'N/A'

    def dehydrate_short_address(self,obj):
        if obj.short_address:
            return obj.short_address
        else:
            return 'N/A'

    def dehydrate_city(self,obj):
        if obj.city:
            return obj.city
        else:
            return 'N/A'

    def dehydrate_state(self,obj):
        if obj.state:
            return obj.state
        else:
            return 'N/A'

    def dehydrate_pincode(self,obj):
        if obj.pincode:
            return obj.pincode
        else:
            return 'N/A'

    def dehydrate_category(self,obj):
         if obj.category:
            return obj.category
         else:
            return 'N/A'

class FormReceiptresource(resources.ModelResource):
    school_name = Field()
    receipt_id = Field()
    form_fee = Field()

    class Meta:
        model = FormReceipt
        fields = [
            "timestamp"
        ]

    def dehydrate_school_name(self,obj):
         return obj.school_applied.school

    def dehydrate_receipt_id(self, obj):
        return obj.receipt_id

    def dehydrate_form_fee(self, obj):
        return obj.form_fee
