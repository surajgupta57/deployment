from . import views
from django.conf.urls import url

urlpatterns = [
    url("", views.quiz_email_dashboard, name='quiz_email_dashboard'),
]

