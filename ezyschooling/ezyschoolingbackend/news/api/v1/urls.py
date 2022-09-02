from django.urls import path

from . import views

app_names = "news"
urlpatterns = [
    path("search/", views.NewsSearchView.as_view(), name="news_search"),
    path("sitemap/", views.NewsSitemapData.as_view()),
    path("all-news/", views.AllNewsAPIView.as_view(), name="all_news"),
    path("<slug:slug>/", views.NewsDetailAPIView.as_view(), name="news_detail"),
    path("", views.NewsListAPIView.as_view(), name="news_list"),
]
