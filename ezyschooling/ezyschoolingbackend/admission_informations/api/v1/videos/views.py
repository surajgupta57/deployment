from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.http import Http404
from elasticsearch import Elasticsearch
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import Board
from experts.models import ExpertUserProfile
from parents.models import ParentProfile
from admission_informations.filters import AdmissionInformationUserVideoFilter, AdmissionInformationVideoCommentFilter
from admission_informations.models import AdmissionInformationUserVideo, AdmissionInformationVideoComment

from .serializers import (
            AdmissionInformationUserVideoListSerializer,
            AdmissionInformationUserVideoSerializer,
            AdmissionInformationVideoCommentCreateSerializer,
            AdmissionInformationVideoCommentSerializer,
            AdmissionInformationUserVideoNotificationSerializer,
            AdmissionInformationUserVideoCommentNotificationSerializer,
            AdmissionInformationVideoThreadCommentCreateSerializer,
        )

from backend.logger import info_logger,error_logger

class AdmissionInformationUserVideoView(generics.ListAPIView):
    serializer_class = AdmissionInformationUserVideoListSerializer
    filterset_class = AdmissionInformationUserVideoFilter

    def get_queryset(self):
        queryset = AdmissionInformationUserVideo.objects.get_list_api_items()
        return queryset


class AdmissionInformationUserVideoSearchView(APIView):
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
                index="ezyschooling-expert-video",
                size=page_size,
                from_=offset_size,
                _source=[
                    "title",
                    "description",
                    "timestamp",
                    "slug",
                    "url",
                    "views",
                    "board",
                    "sub_category",
                    "id",
                ],
                body=body,
            )
            return Response(res, status=status.HTTP_200_OK)
        error_logger(f"{self.__class__.__name__} No Search Term Found")
        return Response(
            {"error": "No search term found"}, status=status.HTTP_400_BAD_REQUEST
        )


class AdmissionInformationUserVideoDetailView(generics.RetrieveAPIView):
    serializer_class = AdmissionInformationUserVideoSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = (
            AdmissionInformationUserVideo.objects.get_detail_api_items()
            .prefetch_related("tags",)
            .order_by("id")
        )
        if self.request.user and self.request.user.is_authenticated:
            user_liked_admission_videos = self.request.user.user_liked_admission_videos.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=user_liked_admission_videos, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            if self.request.user.is_parent:
                try:
                    parent = ParentProfile.objects.get(
                        id=self.request.user.current_parent
                    )
                    parent_bookmarked_videos = parent.bookmarked_admission_videos.values_list(
                        "id", flat=True
                    )
                    queryset = queryset.annotate(
                        bookmark_status=Case(
                            When(id__in=parent_bookmarked_videos, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField(),
                        ),
                    )
                except ObjectDoesNotExist:
                    error_logger(f"{self.__class__.__name__} Parent Profile Object DoesNot Exist")
                    pass
        return queryset


class AdmissionInformationVideoCommentView(generics.ListAPIView):
    filterset_class = AdmissionInformationVideoCommentFilter
    serializer_class = AdmissionInformationVideoCommentSerializer

    def get_queryset(self):
        queryset = (
            AdmissionInformationVideoComment.objects.filter(parent_comment__isnull=True)
            .get_list_api_items()
            .order_by("-id")
        )
        if self.request.user and self.request.user.is_authenticated:
            video_comments_likes = self.request.user.user_liked_admission_video_comments.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=video_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class AdmissionInformationVideoCommentCreateView(generics.CreateAPIView):
    filterset_class = AdmissionInformationVideoCommentFilter
    serializer_class = AdmissionInformationVideoCommentCreateSerializer

    def perform_create(self, serializer):
        video_id = self.kwargs.get("video_id", None)
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_parent
        ):
            comment = serializer.save(
                parent_id=self.request.user.current_parent, video_id=video_id
            )
        elif (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_expert
        ):
            comment = serializer.save(
                expert=self.request.user.expert_user, video_id=video_id
            )
        else:
            serializer.save(video_id=video_id)


class AdmissionInformationVideoThreadCommentView(generics.ListAPIView):
    serializer_class = AdmissionInformationVideoCommentSerializer

    def get_queryset(self):
        queryset = AdmissionInformationVideoComment.objects.get_list_api_items()
        comment_id = self.kwargs.get("comment_id", None)
        if comment_id is not None:
            queryset = queryset.filter(parent_comment_id=comment_id)
        if self.request.user and self.request.user.is_authenticated:
            video_comments_likes = self.request.user.user_liked_admission_video_comments.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=video_comments_likes, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        return queryset


class AdmissionInformationVideoThreadCommentCreateView(generics.CreateAPIView):
    serializer_class = AdmissionInformationVideoThreadCommentCreateSerializer

    def perform_create(self, serializer):
        video_id = self.kwargs.get("video_id", None)
        comment_id = self.kwargs.get("comment_id", None)
        if (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_parent
        ):
            thread_comment = serializer.save(
                parent_id=self.request.user.current_parent,
                video_id=video_id,
                parent_comment_id=comment_id,
            )
        elif (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_expert
        ):
            thread_comment = serializer.save(
                expert=self.request.user.expert_user,
                video_id=video_id,
                parent_comment_id=comment_id,
            )
        else:
            serializer.save(video_id=video_id, parent_comment_id=comment_id)


class AdmissionInformationVideoLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        video_id = self.kwargs.get("video_id", None)
        video = generics.get_object_or_404(AdmissionInformationUserVideo, pk=video_id, status="P")
        if video.likes.filter(id=request.user.id).exists():
            video.likes.remove(request.user.id)
            
            return Response({"unliked": "Successfully Unliked!"})
        else:
            video.likes.add(request.user.id)
            
            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class AdmissionInformationVideoCommentLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get("comment_id", None)
        video_comment = generics.get_object_or_404(AdmissionInformationVideoComment, pk=comment_id)
        if video_comment.likes.filter(id=request.user.id).exists():
            video_comment.likes.remove(request.user.id)
            
            return Response({"unliked": "Successfully Unliked!"})
        else:
            video_comment.likes.add(request.user.id)
            
            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class RelatedAdmissionInformationVideoListView(generics.ListAPIView):
    serializer_class = AdmissionInformationUserVideoListSerializer
    filterset_class = AdmissionInformationUserVideoFilter

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        try:
            video = (
                AdmissionInformationUserVideo.objects.get_published()
                .only("id", "board", "sub_category", "board__id", "sub_category__id")
                .select_related("board", "sub_category")
                .get(slug=slug)
            )
        except ObjectDoesNotExist:
            raise Http404

        similar_tags_id = video.tags.values_list("similar_tag__id", flat=True)
        tags_id = video.tags.values_list("id", flat=True)
        all_tags_id = tags_id.union(similar_tags_id)

        queryset = (
            AdmissionInformationUserVideo.objects.filter(tags__id__in=all_tags_id)
            .get_list_api_items()
            .exclude(slug=slug)
        )
        return queryset


class AllVideoAPIView(APIView):
    def get(self, request, format=False):
        limit = request.GET.get("limit", 8)
        response = {}
        for board in (
            Board.objects.filter(active=True)
            .prefetch_related(
                Prefetch(
                    "board_admission_videos",
                    queryset=AdmissionInformationUserVideo.objects.get_list_api_items().order_by(
                        "-id"
                    ),
                )
            )
            .order_by("min_age")
        ):
            queryset = board.board_admission_videos.all()[: int(limit)]
            serializer = AdmissionInformationUserVideoListSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)
