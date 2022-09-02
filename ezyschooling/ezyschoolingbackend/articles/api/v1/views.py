import json
import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import (BooleanField, Case, Count, F, Prefetch, Value,
                              When)
from django.http import Http404
from elasticsearch import Elasticsearch
from notifications.models import Notification
from notifications.signals import notify
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.filters import ExpertArticleCommentFilter, ExpertArticleFilter
from articles.models import ExpertArticle, ExpertArticleComment
from articles.tasks import (
    article_comment_create_notification_create_task,
    article_comment_notification_create_task,
    article_comment_notification_delete_task,
    article_comment_thread_create_notification_create_task,
    article_notification_create_task, article_notification_delete_task)
from categories.models import Board
from experts.models import ExpertUserProfile
from parents.models import ParentProfile
from tags.models import CustomTag

from .serializers import *

from backend.logger import info_logger,error_logger

class ExpertArticleView(generics.ListAPIView):
    serializer_class = ExpertArticleListSerializer
    filterset_class = ExpertArticleFilter

    def get_queryset(self):
        if self.request.user.is_authenticated and (
                self.request.user.is_staff or self.request.user.is_superuser):
            queryset = ExpertArticle.objects.get_staff_user_list_api_items()
        else:
            queryset = ExpertArticle.objects.get_list_api_items()
        return queryset


class ExpertArticleSearchView(APIView):
    def get(self, request, format=False):
        elastic_host = "http://localhost:9200"
        if hasattr(settings, "ELASTICSEARCH_DSL"):
            elastic_host = settings.ELASTICSEARCH_DSL["default"]["hosts"]
            http_auth = settings.ELASTICSEARCH_DSL["default"]["http_auth"]
        es = Elasticsearch([f"http://{elastic_host}"], http_auth=http_auth)
        search_term = self.request.GET.get("search_term", None)
        if search_term:
            page_size = self.request.GET.get("page_size", 10)
            offset_size = self.request.GET.get("offset_size", 0)
            board_id = self.request.GET.get("board_id", None)
            sub_category_id = self.request.GET.get("sub_category_id", None)

            body = {}

            body["query"] = {}
            body["query"]["bool"] = {}
            body["query"]["bool"]["must"] = []
            body["query"]["bool"]["must"].append(
                [
                    {
                        "simple_query_string": {
                            "query": search_term,
                            "fields": ["tags.name^3", "title^3", "description^2", ],
                        }
                    },
                    {"match": {"status": "P", }},
                ]
            )
            body["highlight"] = {
                "pre_tags": ["<b>"],
                "post_tags": ["</b>"],
                "fields": {"title": {}, "description": {}, "tags.name": {}},
            }

            if board_id:
                body["query"]["bool"]["must"].append(
                    {"match": {"board.id": board_id, }})

            if sub_category_id:
                body["query"]["bool"]["must"].append(
                    {"match": {"sub_category.id": sub_category_id, }}
                )

            res = es.search(
                index="prod-expert-articles",
                size=page_size,
                from_=offset_size,
                _source=[
                    "title",
                    "description",
                    "timestamp",
                    "slug",
                    "thumbnail",
                    "views",
                    "board",
                    "sub_category",
                    "id",
                ],
                body=body,
            )
            return Response(res, status=status.HTTP_200_OK)
        error_logger(f"{self.__class__.__name__} No Search Term Found")
        return Response({"error": "No search term found"},
                        status=status.HTTP_400_BAD_REQUEST)


class ExpertArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ExpertArticleSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_authenticated and (
                self.request.user.is_staff or self.request.user.is_superuser):
            queryset = ExpertArticle.objects.get_staff_user_detail_api_items()
        else:
            queryset = ExpertArticle.objects.get_detail_api_items()
        queryset = queryset.prefetch_related(
            "tags",
        )
        if self.request.user and self.request.user.is_authenticated:
            user_liked_articles = self.request.user.user_liked_expert_articles.values_list(
                "id", flat=True)

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=user_liked_articles, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            if self.request.user.is_parent:
                try:
                    parent = ParentProfile.objects.get(
                        id=self.request.user.current_parent
                    )
                    parent_bookmarked_articles = parent.bookmarked_articles.values_list(
                        "id", flat=True)
                    queryset = queryset.annotate(
                        bookmark_status=Case(
                            When(id__in=parent_bookmarked_articles,
                                 then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField(),
                        ),
                    )
                except ObjectDoesNotExist:
                    error_logger(f"{self.__class__.__name__} Parent BookMark articles Object DoesNot Exist")
                    pass
        return queryset


class ExpertArticleCommentView(generics.ListAPIView):
    filterset_class = ExpertArticleCommentFilter
    serializer_class = ExpertArticleCommentSerializer

    def get_queryset(self):
        queryset = ExpertArticleComment.objects.filter(
            parent_comment__isnull=True
        ).get_list_api_items()
        if self.request.user and self.request.user.is_authenticated:
            article_comments_likes = self.request.user.user_liked_expert_article_comments.values_list(
                "id", flat=True)

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=article_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class ExpertArticleCommentCreateView(generics.CreateAPIView):
    serializer_class = ExpertArticleCommentCreateSerializer

    def perform_create(self, serializer):
        article_id = self.kwargs.get("article_id", None)
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_parent:
            comment = serializer.save(
                parent_id=self.request.user.current_parent,
                article_id=article_id)
            transaction.on_commit(
                lambda: article_comment_create_notification_create_task.delay(
                    article_id,
                    self.request.user.id,
                    comment.id,
                    user_type="parent"))
        elif self.request.user and self.request.user.is_authenticated and self.request.user.is_expert:
            comment = serializer.save(
                expert=self.request.user.expert_user, article_id=article_id
            )
            transaction.on_commit(
                lambda: article_comment_create_notification_create_task.delay(
                    article_id,
                    self.request.user.id,
                    comment.id,
                    user_type="expert"))
        else:
            serializer.save(article_id=article_id)


class ExpertArticleThreadCommentView(generics.ListAPIView):
    serializer_class = ExpertArticleCommentSerializer

    def get_queryset(self):
        queryset = ExpertArticleComment.objects.get_list_api_items()
        comment_id = self.kwargs.get("comment_id", None)
        if comment_id is not None:
            queryset = queryset.filter(parent_comment_id=comment_id)
        if self.request.user and self.request.user.is_authenticated:
            article_comments_likes = self.request.user.user_liked_expert_article_comments.values_list(
                "id", flat=True)

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=article_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class ExpertArticleThreadCommentCreateView(generics.CreateAPIView):
    serializer_class = ExpertArticleThreadCommentCreateSerializer

    def perform_create(self, serializer):
        article_id = self.kwargs.get("article_id", None)
        comment_id = self.kwargs.get("comment_id", None)
        if self.request.user and self.request.user.is_authenticated and self.request.user.is_parent:
            thread_comment = serializer.save(
                parent_id=self.request.user.current_parent,
                article_id=article_id,
                parent_comment_id=comment_id,
            )
            transaction.on_commit(
                lambda: article_comment_thread_create_notification_create_task.delay(
                    article_id,
                    self.request.user.id,
                    thread_comment.id,
                    parent_comment_id=comment_id,
                    user_type="parent",
                ))
        elif self.request.user and self.request.user.is_authenticated and self.request.user.is_expert:
            thread_comment = serializer.save(
                expert=self.request.user.expert_user,
                article_id=article_id,
                parent_comment_id=comment_id,
            )
            transaction.on_commit(
                lambda: article_comment_thread_create_notification_create_task.delay(
                    article_id,
                    self.request.user.id,
                    thread_comment.id,
                    parent_comment_id=comment_id,
                    user_type="expert",
                ))
        else:
            serializer.save(article_id=article_id,
                            parent_comment_id=comment_id)


class ExpertArticleLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        article_id = self.kwargs.get("article_id", None)
        article = generics.get_object_or_404(
            ExpertArticle, pk=article_id, status="P")
        if article.likes.filter(id=request.user.id).exists():
            article.likes.remove(request.user.id)
            transaction.on_commit(
                lambda: article_notification_delete_task.delay(
                    article_id, request.user.id
                )
            )

            return Response({"unliked": "Successfully Unliked!"})
        else:

            article.likes.add(request.user.id)
            transaction.on_commit(
                lambda: article_notification_create_task.delay(
                    article_id, request.user.id
                )
            )

            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class ExpertArticleCommentLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get("comment_id", None)
        article_comment = generics.get_object_or_404(
            ExpertArticleComment, pk=comment_id
        )
        if article_comment.likes.filter(id=request.user.id).exists():
            article_comment.likes.remove(request.user.id)

            transaction.on_commit(
                lambda: article_comment_notification_delete_task.delay(
                    comment_id, request.user.id
                )
            )

            return Response({"unliked": "Successfully Unliked!"})
        else:
            article_comment.likes.add(request.user.id)

            transaction.on_commit(
                lambda: article_comment_notification_create_task.delay(
                    comment_id, request.user.id
                )
            )

            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class RelatedExpertArticleListView(generics.ListAPIView):
    serializer_class = ExpertArticleListSerializer
    filterset_class = ExpertArticleFilter

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        try:
            article = (
                ExpertArticle.objects.get_published() .only(
                    "id",
                    "board",
                    "sub_category",
                    "board__id",
                    "sub_category__id") .select_related(
                    "board",
                    "sub_category") .get(
                    slug=slug))
        except ObjectDoesNotExist:
            raise Http404
        similar_tags_id = article.tags.values_list(
            "similar_tag__id", flat=True)
        tags_id = article.tags.values_list("id", flat=True)
        all_tags_id = tags_id.union(similar_tags_id)
        queryset = ExpertArticle.objects.filter(
            tags__id__in=all_tags_id
        ).get_list_api_items().exclude(slug=slug).order_by("-id").distinct("id")
        return queryset


class AllArticleAPIView(APIView):
    def get(self, request, format=False):
        limit = request.GET.get("limit", 8)
        response = {}
        for board in (
                Board.objects.filter(
                    active=True) .prefetch_related(
                    Prefetch(
                        "expert_articles",
                        queryset=ExpertArticle.objects.get_list_api_items().order_by("-id"),
                    )) .order_by("min_age")):
            queryset = board.expert_articles.all()[: int(limit)]
            serializer = ExpertArticleListSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)


class FeaturedTagArticles(generics.ListAPIView):
    serializer_class = FeaturedExpertArticleListSerializer

    def get_queryset(self):
        tags = CustomTag.objects.filter(
            featured=True).values_list(
            "slug", flat=True)
        articles = ExpertArticle.objects.none()

        for tag in tags:
            article = ExpertArticle.objects.get_list_api_items().filter(
                tags__slug=tag,pinned=True)
            articles = articles.union(article)

        return articles


class ExpertArticleSitemapData(APIView):
    def get(self, request, format=False):
        data = list(
            ExpertArticle.objects.get_published().values_list(
                "slug", flat=True))
        return Response(data, status=status.HTTP_200_OK)


class ExpertArticleRedirectsView(APIView):
    def get(self, request, format=False):
        redirects_file = os.path.join(settings.BASE_DIR, "article-redirects.json")
        with open(redirects_file) as json_file:
            data = json.load(json_file)
        
        return Response(data, status=status.HTTP_200_OK)
