from django.urls import path

from . import views

app_name = "analatics"
urlpatterns = [
    path("", views.PageVisitedView.as_view(), name="analatics"),
    path("click-logs/", views.ClickLogEntryView.as_view(), name="click_logs"),
]
