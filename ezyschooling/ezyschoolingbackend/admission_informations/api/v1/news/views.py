from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.http import Http404
from elasticsearch import Elasticsearch
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import Board
from admission_informations.filters import AdmissionInformationNewsFilter
from admission_informations.models import AdmissionInformationNews, AdmissionInformationNewsHeadline

from .serializers import AdmissionInformationNewsSerializer, AdmissionInformationNewsDetailSerializer
from backend.logger import info_logger,error_logger

class AdmissionInformationNewsListAPIView(generics.ListAPIView):
    serializer_class = AdmissionInformationNewsSerializer
    filterset_class = AdmissionInformationNewsFilter

    def get_queryset(self):
        queryset = (
            AdmissionInformationNews.objects.filter(status="P")
            .select_related("board")
            .prefetch_related("tags",)
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
            )
        )
        return queryset


class AdmissionInformationNewsDetailAPIView(generics.RetrieveAPIView):
    serializer_class = AdmissionInformationNewsDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            AdmissionInformationNews.objects.filter(status="P")
            .select_related("board")
            .prefetch_related("tags", "headlines")
            .only(
                "id",
                "title",
                "slug",
                "image",
                "content",
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
            )
        )
        return queryset


class AllNewsAPIView(APIView):
    def get(self, request, format=False):
        limit = request.GET.get("limit", 8)
        response = {}
        for board in (
            Board.objects.filter(active=True)
            .prefetch_related(
                Prefetch(
                    "board_admission_information_news",
                    queryset=AdmissionInformationNews.objects.filter(status="P")
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
                    )
                    .prefetch_related("tags")
                    .select_related("board")
                    .order_by("-views"),
                )
            )
            .order_by("min_age")
        ):
            queryset = board.board_admission_information_news.all().order_by("-id")[: int(limit)]
            serializer = AdmissionInformationNewsSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)


class AdmissionInformationNewsSearchView(APIView):
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
                    {"match": {"status": "P",}},
                ]
            )
            body["highlight"] = {
                "pre_tags": ["<b>"],
                "post_tags": ["</b>"],
                "fields": {"title": {}, "content": {}, "tags.name": {}},
            }

            if board_id:
                body["query"]["bool"]["must"].append({"match": {"board.id": board_id,}})

            res = es.search(
                index="local-ezyschooling-admission-news",
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
        error_logger(f"{self.__class__.__name__} No Search Term Found")
        return Response(
            {"error": "No search term found"}, status=status.HTTP_400_BAD_REQUEST
        )
