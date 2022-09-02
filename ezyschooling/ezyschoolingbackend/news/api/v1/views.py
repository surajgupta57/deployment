from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.http import Http404
from elasticsearch import Elasticsearch
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date, timedelta
from categories.models import Board
from news.filters import NewsFilter
from news.models import News, NewsHeadline

from .serializers import NewsDetailSerializer, NewsSerializer
from backend.logger import log

class NewsListAPIView(generics.ListAPIView):
    serializer_class = NewsSerializer
    filterset_class = NewsFilter

    def get_queryset(self):
        queryset = News.objects.select_related(
            "board",
            "author"
        ).prefetch_related(
            "tags",
        ).only(
            "id",
            "title",
            "slug",
            "image",
            "views",
            "timestamp",
            "tags",
            "author",
            "author__id",
            "author__name",
            "author__profile_picture",
            "board",
            "board__id",
            "board__name",
            "board__min_age",
            "board__max_age",
            "board__slug",
            "board__thumbnail",
        )

        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return queryset
        else:
            queryset = queryset.filter(status="P")
            return queryset


class NewsDetailAPIView(generics.RetrieveAPIView):
    serializer_class = NewsDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = News.objects.select_related(
            "board",
            "author",
        ).prefetch_related(
            "tags",
            "headlines"
        ).only(
            "id",
            "title",
            "slug",
            "image",
            "content",
            "views",
            "timestamp",
            "tags",
            "author",
            "author__id",
            "author__name",
            "author__profile_picture",
            "board",
            "board__id",
            "board__name",
            "board__min_age",
            "board__max_age",
            "board__slug",
            "board__thumbnail",
        )
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return queryset
        else:
            queryset = queryset.filter(status="P")
            return queryset


class AllNewsAPIView(APIView):
    def get(self, request, format=False):
        limit = request.GET.get("limit", 8)
        response = {}
        for board in (
            Board.objects.filter(active=True)
            .prefetch_related(
                Prefetch(
                    "board_news",
                    queryset=News.objects.filter(status="P")
                    .only(
                        "id",
                        "title",
                        "slug",
                        "image",
                        "views",
                        "timestamp",
                        "tags",
                        "board",
                        "board__id",
                        "board__name",
                        "board__min_age",
                        "board__max_age",
                        "board__slug",
                        "board__thumbnail",
                        "author",
                        "author__id",
                        "author__name",
                        "author__profile_picture",
                    )
                    .prefetch_related("tags")
                    .select_related("board", "author")
                    .order_by("-views"),
                )
            )
            .order_by("min_age")
        ):
            queryset = board.board_news.all().order_by("-id")[: int(limit)]
            serializer = NewsSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)


class NewsSearchView(APIView):
    def get(self, request, format=False):
        elastic_host = "http://localhost:9200"

        if hasattr(settings, "ELASTICSEARCH_DSL"):
            elastic_host = settings.ELASTICSEARCH_DSL["default"]["hosts"]
            http_auth = settings.ELASTICSEARCH_DSL["default"]["http_auth"]
        es = Elasticsearch([f"http://{elastic_host}"], http_auth=http_auth)
        search_term = self.request.GET.get("search_term", None)
        if search_term:
            log(f"{self.__class__.__name__} Searching for term {search_term}",False)
            page_size = self.request.GET.get("page_size", 10)
            offset_size = self.request.GET.get("offset_size", 0)
            board_id = self.request.GET.get("board_id", None)

            body = {}

            body["query"] = {}
            body["query"]["bool"] = {}
            body["query"]["bool"]["must"] = []
            body["query"]["bool"]["must"].append(
                [
                    {
                        "simple_query_string": {
                            "query": search_term,
                            "fields": ["tags.name^3", "title^3", "content^2"],
                        }
                    },
                    {"match": {"status": "P", }},
                ]
            )
            body["highlight"] = {
                "pre_tags": ["<b>"],
                "post_tags": ["</b>"],
                "fields": {"title": {}, "content": {}, "tags.name": {}},
            }

            if board_id:
                body["query"]["bool"]["must"].append(
                    {"match": {"board.id": board_id, }})

            res = es.search(
                index="prod-news",
                _source=[
                    "title",
                    "timestamp",
                    "slug",
                    "content",
                    "image",
                    "views",
                    "board",
                    "id",
                ],
                body=body,
            )
            return Response(res, status=status.HTTP_200_OK)
        log(f"{self.__class__.__name__} Search Term Not Found.",True)
        return Response(
            {"error": "No search term found"}, status=status.HTTP_400_BAD_REQUEST
        )

class NewsSitemapData(APIView):
    def get(self, request, format=False):
        from_date = date.today() - timedelta(days=30)
        to_date =  date.today()
        data = list(News.objects.filter(status="P",timestamp__date__range=(from_date, to_date)).values_list("slug", flat=True))
        log(f"{self.__class__.__name__} DATA={data[:2]}",False)
        return Response(data, status=status.HTTP_200_OK)
