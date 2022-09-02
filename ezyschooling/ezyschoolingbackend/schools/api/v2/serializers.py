from rest_framework import serializers
from schools.models import City, District, DistrictRegion, SchoolClasses, SchoolProfile, VideoTourLinks,FeatureName,Feature,Gallery,SchoolView
from schools.api.v1.serializers import AdmmissionOpenClassesSerializer,SchoolClassesSerializer,SchoolTypeSerializer,SchoolBoardSerializer,SchoolBoardSerializer,SchoolFormatSerializer,DistrictRegionSerializer,SchoolAdmissionFormFeeSerializer,AgeCriteriaSerializer,GallerySerializer, Language


class CitySerializerWithoutState(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "slug",
        ]


class DistrictSerializerWithoutStateCountry(serializers.ModelSerializer):
    city = CitySerializerWithoutState()
    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "slug",
            "city",
        ]

class DistrictRegionSerializerModified(serializers.ModelSerializer):
    district = DistrictSerializerWithoutStateCountry()
    # pincode = PincodeSerializer(many=True)
    class Meta:
        model = DistrictRegion
        fields = [
            "id",
            "name",
            "slug",
            "district",
            # "pincode"
        ]

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "is_featured",
            "slug",
            "photo",
        ]

class SchoolClassesSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolClasses
        fields = [
            "id",
            "name",
            "slug",
            "rank",
        ]

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields= ['id','rank','name','slug']

class SchoolProfileSerializer(serializers.ModelSerializer):

    # unique_views = serializers.SerializerMethodField()

    # enquiries_count = serializers.SerializerMethodField()
    admmissionopenclasses_set = AdmmissionOpenClassesSerializer(read_only=True, many=True)
    agecriteria_set = AgeCriteriaSerializer(read_only=True, many=True)
    # class_relation = SchoolClassesSerializer(read_only=True, many=True)
    # schooladmissionformfee_set = SchoolAdmissionFormFeeSerializer(read_only=True,many=True)
    # school_board = SchoolBoardSerializer()
    # region = RegionSerializer()
    # state = StateSerializer()
    # school_country = CountrySerializer()
    # school_state = StatesSerializer()
    # school_city = CitySerializer()
    # district = DistrictSerializer()
    total_views = serializers.SerializerMethodField()
    feature_list = serializers.SerializerMethodField()
    gallery_list = serializers.SerializerMethodField()
    video_tour_links = serializers.SerializerMethodField()
    school_type = SchoolTypeSerializer()
    school_boardss = SchoolBoardSerializer(read_only=True,many=True)
    school_format = SchoolFormatSerializer()
    medium = serializers.CharField(source="get_medium_display")
    ownership = serializers.CharField(source="get_ownership_display")
    district_region = DistrictRegionSerializer()
    languages = LanguageSerializer(many=True)
    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "name",
            "email",
            "slug",
            "phone_no",
            "website",
            "school_timings",
            "school_type",
            "school_boardss",
            "medium",
            "academic_session",
            "latitude",
            "longitude",
            "district_region",
            "logo",
            "collab",
            "online_school",
            "boarding_school",
            "scholarship_program",
            "ownership",
            "school_format",
            "year_established",
            "school_category",
            "description",
            "student_teacher_ratio",
            "video_tour_links",
            "required_admission_form_fields",
            "required_child_fields",
            "required_father_fields",
            "required_mother_fields",
            "required_guardian_fields",
            "total_views",
            "point_system",
            "is_active",
            "is_verified",
            "admmissionopenclasses_set",
            "feature_list",
            "gallery_list",
            "virtual_tour",
            "built_in_area",
            # "enquiries_count",
            # "views_permission",
            # "views_check_permission",
            # "enquiry_permission",
            # "contact_data_permission",
            # "class_relation",

            "agecriteria_set",
            # "region",
            # "unique_views",
            # "form_price",
            # "cover",
            # "zipcode",
            # "school_board",
            "short_address",
            # "street_address",
            # "city",
            # "state",
            # "school_country",
            # "school_state",
            # "school_city",
            # "district",
            "languages",
        ]
        read_only_fields = (
            "school_type",
            "school_board",
            "district_region",
            "collab",
            "admmissionopenclasses_set",
            "languages",
            # "school_country",
            # "school_state",
            # "school_city",
            # "district",
            # "class_relation",
            # "schooladmissionformfee_set",
            )

    # def get_unique_views(self, instance):
    #     return instance.profile_views.count()
    #
    # def get_enquiries_count(self, instance):
    #     return instance.enquiries.count()
    def get_video_tour_links(self, instance):
        data = []
        if VideoTourLinks.objects.filter(school=instance).exists():
            school_link=VideoTourLinks.objects.get(school=instance)
            all_link=school_link.link.split(",")
            for link in all_link:
                thumbnail = ''
                if 'v=' in link:
                    id = link.split('v=')[1];
                    if "&" in id:
                        thumbnail = id.split('&')[0];
                    else:
                        thumbnail = id
                thumbnail = 'https://img.youtube.com/vi/' + str(thumbnail) + '/mqdefault.jpg'
                data.append({
                    'thumb':thumbnail,
                    'src': link
                })
        return data

    def get_total_views(self, instance):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if request.user.id is not None:
                user = request.user
                if user.is_parent:
                    print("here3")
                    if SchoolView.objects.filter(school=instance, user=request.user).exists():
                        school_view = SchoolView.objects.get(school=instance, user_id=request.user.id)
                        school_view.count += 1
                        school_view.save()
                    else:
                        school_view_create = SchoolView.objects.create(school=instance, user=request.user)
                        school_view = SchoolView.objects.get(school=instance, user=request.user)
                        school_view.count += 1
                        school_view.save()
        instance.views = instance.views + 1
        instance.save()
        return instance.views

    def get_feature_list(self,instance):
        count=Feature.objects.filter(school=instance).count()
        if(count==0):
            return []
        feature_list = FeatureName.objects.all()
        response_list=[]
        for j in feature_list:
            data={}
            data['feature'] = j.name
            nesteddata_query = Feature.objects.filter(school=instance,features__parent=j)
            sub_feature=[]
            for i in nesteddata_query:
                nesteddata={}
                nesteddata['id']= i.features.id
                nesteddata['name']=i.features.name
                nesteddata['exist']= i.exist
                sub_feature.append(nesteddata)
            data['subfeature']=sub_feature
            response_list.append(data)
        return response_list

    def get_gallery_list(self, instance):
        data = []
        all_photos = Gallery.objects.filter(school=instance)
        for item in all_photos:
            data.append({
                'id' : item.id,
                'image' : item.image.url
            })
        return data
