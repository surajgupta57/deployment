from django.urls import path

from . import views

app_name = "admin_custom3"
urlpatterns = [
    path("counsellor/self/analytics/", views.AdminSideCounsellorSelfDataView.as_view(), name='counsellor_wise_analytics'),
]
