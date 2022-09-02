from django.urls import path

from . import views

app_name = "categories"
urlpatterns = [
    path("boards/", views.BoardView.as_view(), name="boards"),
    path("sub-category/", views.SubCategoryView.as_view(), name="sub_category"),
    path(
        "expert-user-videos-category/",
        views.ExpertUserVideoCategoryView.as_view(),
        name="expert_user_videos_category",
    ),
]
