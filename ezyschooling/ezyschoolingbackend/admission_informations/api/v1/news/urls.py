from django.urls import path

from . import views

app_names = "admission_information_news"
urlpatterns = [
    path("search/", views.AdmissionInformationNewsSearchView.as_view(), name="admission_information_news_search"),
    path("all-news/", views.AllNewsAPIView.as_view(), name="all_news"),
    path("<slug:slug>/", views.AdmissionInformationNewsDetailAPIView.as_view(), name="admission_information_news_detail"),
    path("", views.AdmissionInformationNewsListAPIView.as_view(), name="admission_information_news_list"),
]
