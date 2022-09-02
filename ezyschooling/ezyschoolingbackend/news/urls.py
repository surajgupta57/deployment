from django.urls import path

from . import views

urlpatterns = [
    path("", views.news_email_dashboard, name='news_email_dashboard'),
]
