from faqs.models import *
from rest_framework import serializers

class CityDistrictFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistrictFaq
        fields='__all__'

class CityDistrictBoardFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistrictBoardFaq
        fields='__all__'

class CityDistrictSchoolTypeFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistrictSchoolTypeFaq
        fields='__all__'

class CityDistrictCoedFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistrictCoedFaq
        fields='__all__'

class CityDistrictGradeFaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityDistrictGradeFaq
        fields='__all__'
