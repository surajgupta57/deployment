from django_filters import rest_framework as filters
from core.filters import CharInFilter
from .models import Region,States,City,District,DistrictRegion,AgeCriteria,FeeStructure, AdmmissionOpenClasses, AdmissionPageContent


class RegionFilter(filters.FilterSet):
    state = CharInFilter(field_name="state__slug", lookup_expr="in")

    class Meta:
        model = Region
        fields = [
            "state",
            "is_featured"
        ]

class StateFilter(filters.FilterSet):
    country = CharInFilter(field_name="country__slug",lookup_expr="in")
    class Meta:
        model = States
        fields= [
            "country"
        ]


class CityFilter(filters.FilterSet):
    country = CharInFilter(field_name="country__slug",lookup_expr="in")
    states = CharInFilter(field_name="states__slug",lookup_expr="in")
    class Meta:
        model = City
        fields= [
            "country",
            "states",
            'type'
        ]


class DistrictFilter(filters.FilterSet):
    country = CharInFilter(field_name="country__slug",lookup_expr="in")
    state = CharInFilter(field_name="state__slug",lookup_expr="in")
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    city_id = CharInFilter(field_name="city__id",lookup_expr="in")
    class Meta:
        model = District
        fields= [
            "country",
            "state",
            "city",
            "city_id"
        ]

class DistrictRegionFilter(filters.FilterSet):
    country = CharInFilter(field_name="country__slug",lookup_expr="in")
    state = CharInFilter(field_name="state__slug",lookup_expr="in")
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    district_id = CharInFilter(field_name="district__id",lookup_expr="in")
    class Meta:
        model = DistrictRegion
        fields= [
            "country",
            "state",
            "city",
            "district_id",
            "district",
        ]

class AgeCiteriaFilter(filters.FilterSet):
    session = CharInFilter(field_name="session",lookup_expr="in")
    class Meta:
        model = AgeCriteria
        fields= [
            "session",
        ]

class FeeStructureFilter(filters.FilterSet):
    session = CharInFilter(field_name="session",lookup_expr="in")
    class Meta:
        model = FeeStructure
        fields= [
            "session",
        ]

class AdmissionOpenClassesFilter(filters.FilterSet):
    session = CharInFilter(field_name="session",lookup_expr="in")
    class Meta:
        model = AdmmissionOpenClasses
        fields= [
            "session",
        ]

class AdmissionPageContentFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    district_region = CharInFilter(field_name="district_region__slug",lookup_expr="in")
    class Meta:
        model=AdmissionPageContent
        fields='__all__'
