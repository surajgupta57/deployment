from . import serializers
from careers.models import *
from rest_framework import generics, permissions, status
from careers.filters import JobProfileFilter
from rest_framework.views import APIView
from rest_framework import response
from django.http import Http404, HttpResponse, JsonResponse
from rest_framework.response import Response
# Views
class AppliedProfileView(generics.ListCreateAPIView):
    queryset = AppliedJobs.objects.all()
    serializer_class = serializers.AppliedJobsSerialzer

class JobProfileView(generics.ListAPIView):
    serializer_class = serializers.JobProfileSerializer
    queryset = JobProfile.objects.all().filter(status="Active")
    filterset_class = JobProfileFilter

class JobProfileDetailView(generics.ListAPIView):
    serializer_class = serializers.JobProfileSerializer
    def get_queryset(self):
        current_id = self.kwargs.get("pk")
        queryset = JobProfile.objects.all().filter(id=current_id)
        return queryset

class ExperienceListView(generics.ListAPIView):
    serializer_class = serializers.JobExperienceRangeSerializer
    queryset = JobExperienceRange.objects.all()

class LocationListView(generics.ListAPIView):
    serializer_class = serializers.JobLocationSerializer
    queryset = JobLocation.objects.all()

class JobJoiningTypeListView(generics.ListAPIView):
    serializer_class = serializers.JobJoiningTypeSerializer
    queryset = JobJoiningType.objects.all()

class JobDomainListView(generics.ListAPIView):
    serializer_class = serializers.JobDomainSerializer
    queryset = JobDomain.objects.all()
