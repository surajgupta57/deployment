from rest_framework import serializers

from careers.models import *
from core.utils import Base64ImageField
from tags.api.v1.serializers import (FeaturedTagSerializer, TaggitSerializer,
                                     TagListSerializerField)

class AppliedJobsSerialzer(serializers.ModelSerializer):

    class Meta:
        model = AppliedJobs
        fields = '__all__'

class JobExperienceRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobExperienceRange
        fields='__all__'

class JobLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobLocation
        fields='__all__'

class JobJoiningTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobJoiningType
        fields='__all__'

class JobDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDomain
        fields='__all__'

class JobProfileSerializer(serializers.ModelSerializer):
    must_have_skills = TagListSerializerField()
    skills = TagListSerializerField()
    experience = JobExperienceRangeSerializer()
    location = JobLocationSerializer()
    joining_type = JobJoiningTypeSerializer()
    job_domain = JobDomainSerializer()
    class Meta:
        model = JobProfile
        fields='__all__'

class JobProfileDetailSerializer(TaggitSerializer, JobProfileSerializer):
    class Meta:
        model = JobProfile
        fields='__all__'
