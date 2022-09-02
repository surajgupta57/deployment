from django.urls import path

from . import views

app_name = "ownelasticsearch"
urlpatterns = [
    path("cities/", views.CityElasticData.as_view(),name="city_list"),
    path("classes/", views.GradeElasticData.as_view(),name="class_list"),
    path("boards/", views.BoardsElasticData.as_view(),name="board_list"),
    path("districtregions/", views.PopAreaElasticData.as_view(),name="pop_area_list"),
    path("districts/", views.DistrictElasticData.as_view(), name="district_list"),
]
