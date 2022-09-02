from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "schoolsv2"

urlpatterns = [
    path('get-all-multi-classes/', views.FetchAllMultiSchoolClassesView.as_view(), name="get_multi_class"),
    path('get-multi-classes/', views.FetchMultiSchoolClassesView.as_view(), name="get_multi_classes"),
    path("districtregion/",views.DistrictRegionViewModified.as_view(),name='school_district_region_api_view'),
    path("city/",views.CityView.as_view(),name='school_city_api_view'),
    path("school-classes/", views.SchoolClassesView.as_view(),name="school_classes_api_view"),
    path("search/", views.SchoolBrowseSearchView.as_view(),name="school_search_page"),
    path("district/",views.DistrictView.as_view(),name='school_district_api_view'),
    path("<slug:slug>/enquiry/", views.SchoolEnquiryView.as_view(), name="school_enquiry"),
    path("<slug:slug>/admission-open-classes/", views.SchoolAdmmissionOpenClassesDetailView.as_view(),
         name="school_admission_open_classes_api_view"),
    path("<slug:slug>/school-admission-open-classes/", views.AdmmissionOpenClassesDetailView.as_view(),name="school_admission_open_classes_detail_api_view"),
    path("<slug:slug>/", views.SchoolProfileView.as_view(),
         name="school_profile_api_view"),
]
