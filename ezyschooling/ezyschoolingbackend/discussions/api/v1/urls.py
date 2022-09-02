from django.urls import path

from . import views

app_name = "discussions"
urlpatterns = [
    path("create/", views.DiscussionCreateView.as_view(), name="discussion_create"),
    path("search/", views.DiscussionSearchView.as_view(), name="discussion_search"),
    path(
        "all-discussions/",
        views.AllDiscussionsAPIView.as_view(),
        name="all_discussions",
    ),
    path(
        "comments/", views.DiscussionCommentView.as_view(), name="discussion_comments"
    ),
    path(
        "sitemap/", views.DiscussionSitemapData.as_view()
    ),
    path(
        "<int:discussion_id>/comments/create/",
        views.DiscussionCommentCreateView.as_view(),
        name="discussion_comments_create",
    ),
    path(
        "comments/<int:comment_id>/like/",
        views.DiscussionCommentLikeApiView.as_view(),
        name="discussion_comments_like_api_view",
    ),
    path(
        "comments/<int:comment_id>/thread/",
        views.DiscussionThreadCommentView.as_view(),
        name="discussion_comments_thread_api_view",
    ),
    path(
        "<int:discussion_id>/comments/<int:comment_id>/thread/create/",
        views.DiscussionThreadCommentCreateView.as_view(),
        name="discussion_comments_thread_create_api_view",
    ),
    path(
        "<int:discussion_id>/like/",
        views.DiscussionLikeApiView.as_view(),
        name="discussion_like_api_view",
    ),
    path(
        "<slug:slug>/related-discussions/",
        views.RelatedDiscussionListView.as_view(),
        name="related_discussion_list",
    ),
    path("<slug:slug>/", views.DiscussionDetailView.as_view(), name="expert_videos"),
    path("", views.DiscussionView.as_view(), name="expert_videos_detail"),
]
