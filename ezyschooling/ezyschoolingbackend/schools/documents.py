from django.db.models import Sum
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings
from .models import *


@registry.register_document
class SchoolProfileDocument(Document):

    name = fields.TextField(
        fields = {
            'raw':fields.TextField(),
            'suggest': fields.CompletionField()
        }
    )

    school_type = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )

    school_format = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "title": fields.TextField(),
            "slug": fields.TextField()
        }
    )

    school_board = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
        }
    )

    school_boardss = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(analyzer="whitespace"),
        }
    )

    region = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )
    state = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )

    school_country = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )

    school_state = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )
    school_city = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(fields = {
                             'raw':fields.TextField(),
                             'suggest': fields.CompletionField()
                                    }),
            "slug": fields.KeywordField(),
        }
    )
    district = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )
    district_region = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )

    class_relation = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(),
            "slug": fields.TextField(),
            "rank": fields.IntegerField(),
        }
    )

    admmissionopenclasses_set = fields.NestedField(
        properties={
            "id": fields.IntegerField(attr='id'),
            "class_relation": class_relation,
            "admission_open": fields.KeywordField(),
            "form_limit": fields.IntegerField(),
            "draft": fields.BooleanField(),
            "available_seats": fields.IntegerField(),
            "timestamp": fields.DateField(),
            "updated_at": fields.DateField(),
        }
    )

    agecriteria_set = fields.NestedField(
        properties={
            "id": fields.IntegerField(),
            # "class_relation": class_relation,
            "start_date": fields.DateField(),
            "end_date": fields.DateField(),
        }
    )

   # feature_set = fields.NestedField(
   #         properties ={
   #             "id":fields.IntegerField(),
   #             "exist": fields.TextField(),
   #             "filter_string":fields.KeywordField(),
   #             "features":fields.ObjectField(
   #                 properties={
   #                 "id":fields.IntegerField(),
   #                 "name":fields.KeywordField(),
   #                 "parent":fields.ObjectField(
   #                     properties={
   #                         "id":fields.IntegerField(),
   #                         "name":fields.KeywordField()
   #                         }
   #                     )
   #
   #                }
   #                )
   #        }
   #         )

    school_fee_structure = fields.NestedField(
        properties={

            "id": fields.IntegerField(),
            "class_relation": class_relation,
            "stream_relation":fields.NestedField(
                    properties={
                    "id": fields.IntegerField(),
                    "stream":fields.TextField()
                    }
                ),
            'fees_parameters':fields.NestedField(
                    properties={
                        "id":fields.IntegerField(),
                        "head":fields.ObjectField(
                            properties={
                                'head':fields.TextField(),
                                }),
                        "tenure":fields.TextField(),
                        "price":fields.IntegerField(),
                        "refundable":fields.BooleanField(),
                        }
                ),
            "draft": fields.BooleanField(),
            "active": fields.BooleanField(),
            "fee_price": fields.IntegerField(),
            "timestamp": fields.DateField(),
            "updated_at": fields.DateField(),
        }
    )



    # required_admission_form_fields = fields.ObjectField()

    # def prepare_required_admission_form_fields(self, instance):
    #     return instance.required_admission_form_fields

    geocoords = fields.GeoPointField()

    def prepare_geocoords(self, instance):
        return {
            'lon': instance.longitude,
            'lat': instance.latitude
        }

    id = fields.IntegerField()
    unique_views = fields.IntegerField()
    total_views = fields.IntegerField()
    total_points = fields.IntegerField()
    min_fees = fields.IntegerField()
    max_fees = fields.IntegerField()
    admissionclasses_open_count = fields.IntegerField()
    timestamp = fields.DateField()
    updated_at = fields.DateField()


    def prepare_unique_views(self, instance):
        return instance.profile_views.count()

    def prepare_total_views(self, instance):
        return instance.views

    def prepare_admissionclasses_open_count(self, instance):
        return instance.admmissionopenclasses_set.count()

    def prepare_total_points(self, instance):
        if instance.points.exists():
            return instance.points.first().total_points
        return 0

    def prepare_min_fees(self,instance):
        if instance.school_fee_structure.exists():
            return instance.school_fee_structure.first().min_fees
        return 0

    def prepare_max_fees(self,instance):
        if instance.school_fee_structure.exists():
            return instance.school_fee_structure.first().max_fees
        return 0


    class Index:
        name = settings.ELASTIC_SEARCH_INDEX


    class Django:
        model = SchoolProfile
        fields = [
            "email",
            "slug",
            "phone_no",
            "website",
            "school_timings",
            "street_address",
            "city",
            "zipcode",
            "collab",
            "global_rank",
            "region_rank",
            "district_rank",
            "district_region_rank",
            "year_established",
            "school_category",
            "description",
            "student_teacher_ratio",
            "is_active",
            "is_verified",
            "form_price",
            "video_tour_link",
            "logo",
            "point_system",
            "hide_point_calculator"
        ]
        related_models = [
            SchoolType,
            SchoolBoard,
            Region,
            State,
            Country,
            States,
            City,
            District,
            AdmmissionOpenClasses,
            SchoolClasses,
            FeeStructure,
            SchoolFormat,
            AgeCriteria,
        #    Feature,
        ]

        def get_queryset(self):
            return (
                super() .get_queryset() .select_related(
                    "school_type",
                    "school_board",
                    "district_region",
                    "district",
                    "region",
                    'school_country',
                    'school_state',
                    "state",
                    "school_format"))

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, SchoolType):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, SchoolBoard):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, Region):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, State):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, SchoolFormat):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, Country):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, States):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, City):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, District):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, DistrictRegion):
            return related_instance.schoolprofile_set.all()
        if isinstance(related_instance, SchoolFormat):
            return related_instance.schoolprofile_set.all()
