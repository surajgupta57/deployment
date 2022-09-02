from import_export import resources,fields
from import_export.fields import Field

from .models import ParentProfile,ParentTracker,ParentAddress
from import_export.widgets import ForeignKeyWidget



class ParentProfileResource(resources.ModelResource):
    class Meta:
        model = ParentProfile
        fields = [
            "name",
            "user",
            "phone",
            "email",
            "gender",
            "income",
            "parent_type",
            "timestamp"
        ]

    def dehydrate_name(self, obj):
        return obj.name.title()


class ParentAddressResource(resources.ModelResource):
    name = Field()
    phone = Field()
    email = Field()
    street_address=Field()
    city=Field()
    state=Field()
    pincode=Field()

    class Meta:
        model = ParentAddress

    def dehydrate_name(self, obj):
        if(obj.parent):
            return obj.parent.name if(obj.parent.name) else 'N/A'
        else:
            return 'N/A'

    def dehydrate_phone(self,obj):
        if(obj.parent):
            return obj.parent.phone if(obj.parent.phone) else 'N/A'
        else:
            return 'N/A'

    def dehydrate_email(self,obj):
        if(obj.parent):
            return obj.parent.email if(obj.parent.email) else 'N/A'
        else:
            return 'N/A'

    def dehydrate_street_address(self,obj):
        if(obj.street_address):
            return obj.street_address
        else:
            return 'N/A'


    def dehydrate_city(self,obj):
        if(obj.city):
            return obj.city
        else:
            return 'N/A'
        

    def dehydrate_state(self,obj):
        if(obj.state):
            return obj.state
        else:
            return 'N/A'
    
    def dehydrate_pincode(self,obj):
        if(obj.pincode):
            return obj.pincode
        else:
            return 'N/A'

    def dehydrate_region(self,obj):
        if(obj.region):
            return obj.region.name
        else:
            return 'N/A'

class ParentTrackResource(resources.ModelResource):
    @classmethod
    def field_from_django_field(self, field_name, django_field, readonly):
        """
        Returns a Resource Field instance for the given Django model field.
        """
        FieldWidget = self.widget_from_django_field(django_field)
        widget_kwargs = self.widget_kwargs_for_field(field_name)
        field = fields.Field(attribute=field_name, column_name=django_field.verbose_name,
                widget=FieldWidget(**widget_kwargs), readonly=readonly)
        return field

    class Meta:
        model = ParentTracker
        fields = [
            "timestamp",
            "parent__name",
            "parent__email",
            "parent__gender",
            "parent__phone",
            "parent__income",
            "address__street_address",
            "address__city",
            "address__state",
            "address__pincode",
            "address__country",
            "address__region__name",
        ]


