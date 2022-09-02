from django.db.models import Count
from rest_framework import generics

from tags.filters import TagsFilter, CustomSkillTagFilter, CustomMustSkillTagFilter
from tags.models import CustomTag, CustomSkillTag, CustomMustSkillTag

from .serializers import CustomTagSerializer, CustomSkillTagSerializer, CustomMustSkillTagSerializer


class TagListAPIView(generics.ListAPIView):
    serializer_class = CustomTagSerializer
    filterset_class = TagsFilter

    def get_queryset(self):
        queryset = (
            CustomTag.objects.all()
            .annotate(parent_following_count=Count("followers"))
            .order_by("-parent_following_count")
        )
        return queryset

class SkillTagListAPIView(generics.ListAPIView):
    serializer_class = CustomSkillTagSerializer
    filterset_class = CustomSkillTagFilter

    def get_queryset(self):
        queryset = (
            CustomSkillTag.objects.all()
        )
        return queryset

class MustSkillTagListAPIView(generics.ListAPIView):
    serializer_class = CustomMustSkillTagSerializer
    filterset_class = CustomMustSkillTagFilter

    def get_queryset(self):
        queryset = (
            CustomMustSkillTag.objects.all()
        )
        return queryset
