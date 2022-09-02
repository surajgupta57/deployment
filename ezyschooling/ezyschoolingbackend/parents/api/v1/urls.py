from django.urls import path

from . import views

app_name = "parents"
urlpatterns = [
    path("parenting-home/",views.ParentMainPageView.as_view(),name="parent_home_combined_api"),
    path("address/",views.ParentRegisterAddressView.as_view(),name="parent_address"),
    path(
        "registration/", views.ParentRegisterView.as_view(), name="parent_registration"
    ),
    path(
        "notifications/",
        views.ParentNotificationView.as_view(),
        name="all_notifications_list",
    ),
    path(
        "notifications/unread/",
        views.ParentUnreadNotificationView.as_view(),
        name="unread_notifications_list",
    ),
    path(
        "notifications/<int:notification_id>/mark-read/",
        views.ParentNotificationMarkReadView.as_view(),
        name="mark_notification_read",
    ),
    path("admission/receipts/", views.ParentReceiptListView.as_view()),
    path("admission/applications/", views.SchoolsAppliedView.as_view()),
    path("admission/receipts/status/<int:pk>/", views.ParentApplicationStatusLogView.as_view()),
    path("parent-add/", views.ParentAddView.as_view(), name="parent_add"),
    path(
        "bookmarked-articles/",
        views.ParentBookmarkedArticle.as_view(),
        name="parent_bookmarked_articles",
    ),
    path(
        "bookmarked-videos/",
        views.ParentBookmarkedVideo.as_view(),
        name="parent_bookmarked_videos",
    ),
    path(
        "bookmarked-discussions/",
        views.ParentBookmarkedDiscussion.as_view(),
        name="parent_bookmarked_discussions",
    ),
    path(
        "liked-articles/",
        views.ParentLikedArticle.as_view(),
        name="parent_liked_articles",
    ),
    path("liked-videos/", views.ParentLikedVideo.as_view(),
         name="parent_liked_videos"),
    path(
        "liked-discussions/",
        views.ParentLikedDiscussion.as_view(),
        name="parent_liked_discussions",
    ),
    path(
        "<int:article_id>/bookmark-article/",
        views.ParentArticleBookmarkAPIView.as_view(),
        name="bookmark_article",
    ),
    path(
        "<int:video_id>/bookmark-video/",
        views.ParentBookmarkVideoAPIView.as_view(),
        name="bookmark_video",
    ),
    path(
        "<int:discussion_id>/bookmark-discussion/",
        views.ParentBookmarkDiscussionAPIView.as_view(),
        name="bookmark_discussion",
    ),
    path(
        "<slug:tag_slug>/follow/",
        views.ParentFollowTagAPIView.as_view(),
        name="follow_tag",
    ),
    path(
        "followed-tags/",
        views.ParentFollowTagListAPIView.as_view(),
        name="parent_followed_tags",
    ),
    path(
        "all-tags-expert-parent-followed/",
        views.AllTagExpertParentTagListAPIView.as_view(),
        name="tags_except_parent_followed",
    ),
    path(
        "<str:tag_name>/tag-status/",
        views.ParentFollowTagStats.as_view(),
        name="parent_detail",
    ),
    path("<slug:slug>/", views.ParentDetailView.as_view(), name="parent_detail"),
    path("", views.ParentProfileDetailView.as_view(), name="user_parent_detail"),

]
