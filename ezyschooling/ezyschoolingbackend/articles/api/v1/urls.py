from django.urls import path

from articles.api.v1.views import FeaturedTagArticles

from . import views

app_name = "articles"
urlpatterns = [
    path("expert-articles/", views.ExpertArticleView.as_view(), name="expert_articles"),
    path(
        "search/",
        views.ExpertArticleSearchView.as_view(),
        name="expert_articles_search",
    ),
    path("sitemap/", views.ExpertArticleSitemapData.as_view()),
    path("featured-articles/", views.FeaturedTagArticles.as_view()),
    path("all-articles/", views.AllArticleAPIView.as_view(), name="all_articles"),
    path(
        "comments/",
        views.ExpertArticleCommentView.as_view(),
        name="expert_articles_comments",
    ),
    path(
        "redirects/",
        views.ExpertArticleRedirectsView.as_view(),
        name="expert_articles_redirects",
    ),
    path(
        "<int:article_id>/comments/create/",
        views.ExpertArticleCommentCreateView.as_view(),
        name="expert_articles_comments_create",
    ),
    path(
        "comments/<int:comment_id>/like/",
        views.ExpertArticleCommentLikeApiView.as_view(),
        name="expert_article_comments_like_api_view",
    ),
    path(
        "comments/<int:comment_id>/thread/",
        views.ExpertArticleThreadCommentView.as_view(),
        name="expert_article_comments_thread_api_view",
    ),
    path(
        "<int:article_id>/comments/<int:comment_id>/thread/create/",
        views.ExpertArticleThreadCommentCreateView.as_view(),
        name="article_comments_thread_create_api_view",
    ),
    path(
        "<int:article_id>/like/",
        views.ExpertArticleLikeApiView.as_view(),
        name="article_like_api_view",
    ),
    path(
        "<slug:slug>/related-articles/",
        views.RelatedExpertArticleListView.as_view(),
        name="related_expert_articles_list",
    ),
    path(
        "<slug:slug>/",
        views.ExpertArticleDetailView.as_view(),
        name="expert_articles_detail",
    ),
]
