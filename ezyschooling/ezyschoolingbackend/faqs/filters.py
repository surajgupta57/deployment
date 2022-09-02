from django_filters import rest_framework as filters
from core.filters import CharInFilter
from .models import *

class CityDistrictFaqFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    class Meta:
        model=CityDistrictFaq
        fields='__all__'

class CityDistrictBoardFaqFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    school_board=CharInFilter(field_name="school_board__slug",lookup_expr="in")
    class Meta:
        model=CityDistrictBoardFaq
        fields='__all__'

class CityDistrictSchoolTypeFaqFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    school_type= CharInFilter(field_name="school_type__slug", lookup_expr="in")
    class Meta:
        model=CityDistrictSchoolTypeFaq
        fields='__all__'

class CityDistrictCoedFaqFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    school_category = CharInFilter(field_name="school_category__slug", lookup_expr="in")
    class Meta:
        model=CityDistrictCoedFaq
        fields='__all__'

class CityDistrictGradeFaqFilter(filters.FilterSet):
    city = CharInFilter(field_name="city__slug",lookup_expr="in")
    district = CharInFilter(field_name="district__slug",lookup_expr="in")
    grade = CharInFilter(field_name="grade__slug", lookup_expr="in")
    class Meta:
        model=CityDistrictGradeFaq
        fields='__all__'
