from django.urls import include, path
from .views import *

app_name = "faqs"
urlpatterns = [
    path("", CityDistrictFaqView.as_view(), name="city-district-faq-filter"),
    path("boards", CityDistrictBoardFaqView.as_view(), name="city-district-board-faq-filter"),
    path("school-type/", CityDistrictSchoolTypeFaqView.as_view(), name="city-district-school_type-filter"),
    path("coed/", CityDistrictCoedFaqView.as_view(), name="city-district-coed-filter"),
    path("grade/", CityDistrictGradeFaqView.as_view(), name="city-district-grade-filter"),
]
