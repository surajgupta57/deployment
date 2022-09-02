from django.shortcuts import render
from rest_framework import serializers,generics
from .serializers import *
from faqs.filters import *
from faqs.models import *


# Create your views here.
class CityDistrictFaqView(generics.ListAPIView):
    serializer_class = CityDistrictFaqSerializer
    queryset = CityDistrictFaq.objects.all().filter(status="Published")
    filterset_class = CityDistrictFaqFilter

class CityDistrictBoardFaqView(generics.ListAPIView):
    serializer_class = CityDistrictBoardFaqSerializer
    queryset = CityDistrictBoardFaq.objects.all().filter(status="Published")
    filterset_class = CityDistrictBoardFaqFilter

class CityDistrictSchoolTypeFaqView(generics.ListAPIView):
    serializer_class = CityDistrictSchoolTypeFaqSerializer
    queryset = CityDistrictSchoolTypeFaq.objects.all().filter(status="Published")
    filterset_class = CityDistrictSchoolTypeFaqFilter

class CityDistrictCoedFaqView(generics.ListAPIView):
    serializer_class = CityDistrictCoedFaqSerializer
    queryset = CityDistrictCoedFaq.objects.all().filter(status="Published")
    filterset_class = CityDistrictCoedFaqFilter

class CityDistrictGradeFaqView(generics.ListAPIView):
    serializer_class = CityDistrictGradeFaqSerializer
    queryset = CityDistrictGradeFaq.objects.all().filter(status="Published")
    filterset_class = CityDistrictGradeFaqFilter
