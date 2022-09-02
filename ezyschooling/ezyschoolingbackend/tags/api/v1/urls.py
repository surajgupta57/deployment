from django.urls import path

from . import views

app_names = "tags"
urlpatterns = [
    path("", views.TagListAPIView.as_view(), name="tags_list_api_view"),
    path("skills/", views.SkillTagListAPIView.as_view(), name="skill_tags_list_api_view"),
    path("must-skills/", views.MustSkillTagListAPIView.as_view(), name="must_skill_tags_list_api_view"),
]
