from django.urls import path

from . import views

app_name = "videos"
urlpatterns = [
    path("expert-videos/", views.ExpertUserVideoView.as_view(), name="expert_videos"),
    path(
        "search/",
        views.ExpertUserVideoSearchView.as_view(),
        name="expert_videos_search",
    ),
    path("sitemap/", views.VideosSitemapData.as_view()),
    path("all-videos/", views.AllVideoAPIView.as_view(), name="all_videos"),
    path(
        "comments/",
        views.ExpertVideoCommentView.as_view(),
        name="expert_articles_comments",
    ),
    path(
        "<int:video_id>/comments/create/",
        views.ExpertVideoCommentCreateView.as_view(),
        name="expert_video_comments_create",
    ),
    path(
        "comments/<int:comment_id>/like/",
        views.ExpertVideoCommentLikeApiView.as_view(),
        name="expert_video_comments_like_api_view",
    ),
    path(
        "comments/<int:comment_id>/thread/",
        views.ExpertVideoThreadCommentView.as_view(),
        name="expert_video_comments_thread_api_view",
    ),
    path(
        "<int:video_id>/comments/<int:comment_id>/thread/create/",
        views.ExpertVideoThreadCommentCreateView.as_view(),
        name="video_comments_thread_create_api_view",
    ),
    path(
        "<int:video_id>/like/",
        views.ExpertVideoLikeApiView.as_view(),
        name="video_like_api_view",
    ),
    path(
        "<slug:slug>/related-videos/",
        views.RelatedExpertVideoListView.as_view(),
        name="related_expert_video_list",
    ),
    path(
        "<slug:slug>/",
        views.ExpertUserVideoDetailView.as_view(),
        name="expert_videos_detail",
    ),
]
