from django.urls import path

from . import views

app_name = "admission_informations_videos"
urlpatterns = [
    path("", views.AdmissionInformationUserVideoView.as_view(), name="admission_videos"),
    path(
        "search/",
        views.AdmissionInformationUserVideoSearchView.as_view(),
        name="admission_videos_search",
    ),
    path("all-videos/", views.AllVideoAPIView.as_view(), name="all_videos"),
    path(
        "comments/",
        views.AdmissionInformationVideoCommentView.as_view(),
        name="admission_articles_comments",
    ),
    path(
        "<int:video_id>/comments/create/",
        views.AdmissionInformationVideoCommentCreateView.as_view(),
        name="admission_video_comments_create",
    ),
    path(
        "comments/<int:comment_id>/like/",
        views.AdmissionInformationVideoCommentLikeApiView.as_view(),
        name="admission_video_comments_like_api_view",
    ),
    path(
        "comments/<int:comment_id>/thread/",
        views.AdmissionInformationVideoThreadCommentView.as_view(),
        name="admission_video_comments_thread_api_view",
    ),
    path(
        "<int:video_id>/comments/<int:comment_id>/thread/create/",
        views.AdmissionInformationVideoThreadCommentCreateView.as_view(),
        name="video_comments_thread_create_api_view",
    ),
    path(
        "<int:video_id>/like/",
        views.AdmissionInformationVideoLikeApiView.as_view(),
        name="video_like_api_view",
    ),
    path(
        "<slug:slug>/related-videos/",
        views.RelatedAdmissionInformationVideoListView.as_view(),
        name="related_expert_video_list",
    ),
    path(
        "<slug:slug>/",
        views.AdmissionInformationUserVideoDetailView.as_view(),
        name="admission_videos_detail",
    ),
]
