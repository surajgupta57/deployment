from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.http import Http404
from elasticsearch import Elasticsearch
from notifications.models import Notification
from notifications.signals import notify
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admission_informations.filters import AdmissionInformationArticleCommentFilter, AdmissionInformationArticleFilter
from admission_informations.models import AdmissionInformationArticle, AdmissionInformationArticleComment
from categories.models import Board
from experts.models import ExpertUserProfile
from parents.models import ParentProfile

from .serializers import (AdmissionInformationArticleCommentCreateSerializer,
                          AdmissionInformationArticleCommentSerializer,
                          AdmissionInformationArticleListSerializer, AdmissionInformationArticleSerializer,
                          AdmissionInformationArticleThreadCommentCreateSerializer)

from backend.logger import info_logger,error_logger

class AdmissionInformationArticleView(generics.ListAPIView):
    serializer_class = AdmissionInformationArticleListSerializer
    filterset_class = AdmissionInformationArticleFilter

    def get_queryset(self):
        queryset = AdmissionInformationArticle.objects.get_list_api_items()
        return queryset


class AdmissionInformationArticleSearchView(APIView):
    def get(self, request, format=False):
        elastic_host = "http://localhost:9200"
        if hasattr(settings, "ELASTICSEARCH_DSL"):
            elastic_host = settings.ELASTICSEARCH_DSL["default"]["hosts"]
        es = Elasticsearch([f"http://{elastic_host}"])
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
                            "fields": ["tags.name^3", "title^3", "description^2",],
                        }
                    },
                    {"match": {"status": "P",}},
                ]
            )
            body["highlight"] = {
                "pre_tags": ["<b>"],
                "post_tags": ["</b>"],
                "fields": {"title": {}, "description": {}, "tags.name": {}},
            }

            if board_id:
                body["query"]["bool"]["must"].append({"match": {"board.id": board_id,}})

            if sub_category_id:
                body["query"]["bool"]["must"].append(
                    {"match": {"sub_category.id": sub_category_id,}}
                )

            res = es.search(
                index="ezyschooling-admission-articles",
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
        error_logger(f"{self.__class__.__name__} Search Term Not Found")
        return Response(
            {"error": "No search term found"}, status=status.HTTP_400_BAD_REQUEST
        )


class AdmissionInformationArticleDetailView(generics.RetrieveAPIView):
    serializer_class = AdmissionInformationArticleSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = AdmissionInformationArticle.objects.get_detail_api_items().prefetch_related(
            "tags",
        )
        if self.request.user and self.request.user.is_authenticated:
            user_liked_articles = self.request.user.user_liked_admission_articles.values_list(
                "id", flat=True
            )

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
                    parent_bookmarked_articles = parent.bookmarked_admission_articles.values_list(
                        "id", flat=True
                    )
                    queryset = queryset.annotate(
                        bookmark_status=Case(
                            When(id__in=parent_bookmarked_articles, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField(),
                        ),
                    )
                except ObjectDoesNotExist:
                    error_logger(f"{self.__class__.__name__} ParentObject Doesn't Exist")
                    pass
        return queryset


class AdmissionInformationArticleCommentView(generics.ListAPIView):
    filterset_class = AdmissionInformationArticleCommentFilter
    serializer_class = AdmissionInformationArticleCommentSerializer

    def get_queryset(self):
        queryset = AdmissionInformationArticleComment.objects.filter(
            parent_comment__isnull=True
        ).get_list_api_items()
        if self.request.user and self.request.user.is_authenticated:
            article_comments_likes = self.request.user.user_liked_admission_article_comments.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=article_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class AdmissionInformationArticleCommentCreateView(generics.CreateAPIView):
    serializer_class = AdmissionInformationArticleCommentCreateSerializer

    def perform_create(self, serializer):
        article_id = self.kwargs.get("article_id", None)
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_parent
        ):
            comment = serializer.save(
                parent_id=self.request.user.current_parent, article_id=article_id
            )
        elif (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_expert
        ):
            comment = serializer.save(
                expert=self.request.user.expert_user, article_id=article_id
            )
        else:
            serializer.save(article_id=article_id)


class AdmissionInformationArticleThreadCommentView(generics.ListAPIView):
    serializer_class = AdmissionInformationArticleCommentSerializer

    def get_queryset(self):
        queryset = AdmissionInformationArticleComment.objects.get_list_api_items()
        comment_id = self.kwargs.get("comment_id", None)
        if comment_id is not None:
            queryset = queryset.filter(parent_comment_id=comment_id)
        if self.request.user and self.request.user.is_authenticated:
            article_comments_likes = self.request.user.user_liked_admission_article_comments.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=article_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class AdmissionInformationArticleThreadCommentCreateView(generics.CreateAPIView):
    serializer_class = AdmissionInformationArticleThreadCommentCreateSerializer

    def perform_create(self, serializer):
        article_id = self.kwargs.get("article_id", None)
        comment_id = self.kwargs.get("comment_id", None)
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_parent
        ):
            thread_comment = serializer.save(
                parent_id=self.request.user.current_parent,
                article_id=article_id,
                parent_comment_id=comment_id,
            )
        elif (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_expert
        ):
            thread_comment = serializer.save(
                expert=self.request.user.expert_user,
                article_id=article_id,
                parent_comment_id=comment_id,
            )
        else:
            serializer.save(article_id=article_id, parent_comment_id=comment_id)


class AdmissionInformationArticleLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        article_id = self.kwargs.get("article_id", None)
        article = generics.get_object_or_404(AdmissionInformationArticle, pk=article_id, status="P")
        if article.likes.filter(id=request.user.id).exists():
            article.likes.remove(request.user.id)
            return Response({"unliked": "Successfully Unliked!"})
        else:

            article.likes.add(request.user.id)
            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class AdmissionInformationArticleCommentLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get("comment_id", None)
        article_comment = generics.get_object_or_404(
            AdmissionInformationArticleComment, pk=comment_id
        )
        if article_comment.likes.filter(id=request.user.id).exists():
            article_comment.likes.remove(request.user.id)

            return Response({"unliked": "Successfully Unliked!"})
        else:
            article_comment.likes.add(request.user.id)

            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class RelatedAdmissionInformationArticleListView(generics.ListAPIView):
    serializer_class = AdmissionInformationArticleListSerializer
    filterset_class = AdmissionInformationArticleFilter

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        try:
            article = (
                AdmissionInformationArticle.objects.get_published()
                .only("id", "board", "sub_category", "board__id", "sub_category__id")
                .select_related("board", "sub_category")
                .get(slug=slug)
            )
        except ObjectDoesNotExist:
            raise Http404
        similar_tags_id = article.tags.values_list("similar_tag__id", flat=True)
        tags_id = article.tags.values_list("id", flat=True)
        all_tags_id = tags_id.union(similar_tags_id)
        queryset = (
            AdmissionInformationArticle.objects.filter(tags__id__in=all_tags_id)
            .get_list_api_items()
            .exclude(slug=slug)
        )
        return queryset


class AllArticleAPIView(APIView):
    def get(self, request, format=False):
        limit = request.GET.get("limit", 8)
        response = {}
        for board in (
            Board.objects.filter(active=True)
            .prefetch_related(
                Prefetch(
                    "admission_articles",
                    queryset=AdmissionInformationArticle.objects.get_list_api_items().order_by("-id"),
                )
            )
            .order_by("min_age")
        ):
            queryset = board.admission_articles.all()[: int(limit)]
            serializer = AdmissionInformationArticleListSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)
