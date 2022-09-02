from django.urls import path

from . import views

app_name = "admission_informations_articles"
urlpatterns = [
    path("", views.AdmissionInformationArticleView.as_view(), name="admission_articles"),
    path(
        "articles/search/",
        views.AdmissionInformationArticleSearchView.as_view(),
        name="admission_articles_search",
    ),
    path("all-articles/", views.AllArticleAPIView.as_view(), name="all_articles"),
    path(
        "articles/comments/",
        views.AdmissionInformationArticleCommentView.as_view(),
        name="admission_articles_comments",
    ),
    path(
        "articles/<int:article_id>/comments/create/",
        views.AdmissionInformationArticleCommentCreateView.as_view(),
        name="admission_articles_comments_create",
    ),
    path(
        "articles/comments/<int:comment_id>/like/",
        views.AdmissionInformationArticleCommentLikeApiView.as_view(),
        name="admission_article_comments_like_api_view",
    ),
    path(
        "articles/comments/<int:comment_id>/thread/",
        views.AdmissionInformationArticleThreadCommentView.as_view(),
        name="admission_article_comments_thread_api_view",
    ),
    path(
        "articles/<int:article_id>/comments/<int:comment_id>/thread/create/",
        views.AdmissionInformationArticleThreadCommentCreateView.as_view(),
        name="article_comments_thread_create_api_view",
    ),
    path(
        "articles/<int:article_id>/like/",
        views.AdmissionInformationArticleLikeApiView.as_view(),
        name="article_like_api_view",
    ),
    path(
        "articles/<slug:slug>/related-articles/",
        views.RelatedAdmissionInformationArticleListView.as_view(),
        name="related_expert_articles_list",
    ),
    path(
        "articles/<slug:slug>/",
        views.AdmissionInformationArticleDetailView.as_view(),
        name="admission_articles_detail",
    ),
]
