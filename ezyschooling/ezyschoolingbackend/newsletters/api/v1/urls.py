from django.urls import path

from . import views

app_name = "newsletters"

urlpatterns = [
    path("preferences/", views.PreferencesView.as_view()),
    path("subscription/", views.SubscriptionCreateView.as_view()),
    path("subscription/<uuid:uuid>/", views.SubscriptionUpdateView.as_view()),
]
