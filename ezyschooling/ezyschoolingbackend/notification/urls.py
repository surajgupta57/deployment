from django.urls import path

from . import views

urlpatterns = [
    path("", views.webpush_dashboard, name='webpush_dashboard'),
    path("new/", views.new_webpush_dashboard, name='new_webpush_dashboard'),
    path("sent/", views.sent, name='sent'),
]
