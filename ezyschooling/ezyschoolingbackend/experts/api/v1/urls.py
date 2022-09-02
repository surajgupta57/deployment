from django.urls import path

from . import views

app_names = "experts"
urlpatterns = [
    path(
        "notifications/",
        views.ExpertNotificationView.as_view(),
        name="expert_notification_list",
    ),
    path("sitemap/", views.ExpertProfileSitemapData.as_view()),
    path(
        "<slug:slug>/related-videos/",
        views.ExpertRelatedVideos.as_view(),
        name="expert_user_related_videos",
    ),
    path("<slug:slug>/", views.ExpertUserDetails.as_view(), name="expert_user_profile"),
    path("", views.ExpertPanelUserList.as_view(), name="expert_panel_lists"),
]
