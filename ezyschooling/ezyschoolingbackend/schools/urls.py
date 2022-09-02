from django.urls import path

from . import views

urlpatterns = [
    path("add/", views.add_new_tracking_id_dashboard, name='new_source_add'),
]
