from django_filters import rest_framework as filters

from tags.models import CustomTag, CustomSkillTag, CustomMustSkillTag


class TagsFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = CustomTag
        fields = [
            "name",
        ]

class CustomSkillTagFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = CustomSkillTag
        fields = [
            "name",
        ]

class CustomMustSkillTagFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = CustomMustSkillTag
        fields = [
            "name",
        ]
