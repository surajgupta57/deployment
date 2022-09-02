from django.urls import path

from . import views

app_name = "childs"
urlpatterns = [
    path("<int:pk>/", views.ChildDetailView.as_view(), name="pk_single_child_details_api_view"),
    path("<slug:slug>/", views.ChildDetailView.as_view(), name="slug_single_child_details_api_view"),
    path(
        "<int:user_id>/parent-childs/",
        views.ChildView.as_view(),
        name="user_childs_api_view",
    ),
    path("", views.ChildView.as_view(), name="parent_child_api_view"),
]
