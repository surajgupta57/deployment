from django.urls import path

from . import views

app_name = "phones"
urlpatterns = [
    path("", views.PhoneNumberView.as_view()),
    path("verify/", views.PhoneNumberVerify.as_view())
]
