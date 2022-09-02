from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("", views.CourseEnrollmentView.as_view()),
    path("demo/", views.CourseDemoClassView.as_view()),
    path("order/", views.CourseOrderView.as_view()),
    path("capture/", views.CourseTransactionView.as_view()),
    path("enquiry/", views.CourseEnquiryView.as_view()),
]
