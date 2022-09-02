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
from videos.filters import ExpertUserVideoFilter, ExpertVideoCommentFilter
from videos.models import ExpertUserVideo, ExpertVideoComment
from videos.tasks import (video_comment_create_notification_create_task,
                          video_comment_notification_create_task,
                          video_comment_notification_delete_task,
                          video_comment_thread_create_notification_create_task,
                          video_notification_create_task,
                          video_notification_delete_task)

from .serializers import (ExpertUserVideoListSerializer,
                          ExpertUserVideoSerializer,
                          ExpertVideoCommentCreateSerializer,
                          ExpertVideoCommentSerializer,
                          ExpertVideoThreadCommentCreateSerializer)


class ExpertUserVideoView(generics.ListAPIView):
    serializer_class = ExpertUserVideoListSerializer
    filterset_class = ExpertUserVideoFilter

    def get_queryset(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = ExpertUserVideo.objects.get_staff_user_list_api_items()
        else:
            queryset = ExpertUserVideo.objects.get_list_api_items()
        return queryset


class ExpertUserVideoSearchView(APIView):
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
                index="prod-expert-videos",
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
        return Response(
            {"error": "No search term found"}, status=status.HTTP_400_BAD_REQUEST
        )


class ExpertUserVideoDetailView(generics.RetrieveAPIView):
    serializer_class = ExpertUserVideoSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = ExpertUserVideo.objects.get_staff_user_detail_api_items()
        else:
            queryset = ExpertUserVideo.objects.get_detail_api_items()
        queryset = queryset.prefetch_related(
            "tags",
        ).order_by("id")
        if self.request.user and self.request.user.is_authenticated:
            user_liked_videos = self.request.user.user_liked_videos.values_list(
                "id", flat=True
            )

            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=user_liked_videos, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
            if self.request.user.is_parent:
                try:
                    parent = ParentProfile.objects.get(
                        id=self.request.user.current_parent
                    )
                    parent_bookmarked_videos = parent.bookmarked_videos.values_list(
                        "id", flat=True
                    )
                    queryset = queryset.annotate(
                        bookmark_status=Case(
                            When(id__in=parent_bookmarked_videos,
                                 then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField(),
                        ),
                    )
                except ObjectDoesNotExist:
                    pass
        return queryset


class ExpertVideoCommentView(generics.ListAPIView):
    filterset_class = ExpertVideoCommentFilter
    serializer_class = ExpertVideoCommentSerializer

    def get_queryset(self):
        queryset = (
            ExpertVideoComment.objects.filter(parent_comment__isnull=True)
            .get_list_api_items()
            .order_by("-id")
        )
        if self.request.user and self.request.user.is_authenticated:
            video_comments_likes = self.request.user.user_liked_video_comments.values_list(
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


class ExpertVideoCommentCreateView(generics.CreateAPIView):
    filterset_class = ExpertVideoCommentFilter
    serializer_class = ExpertVideoCommentCreateSerializer

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
            transaction.on_commit(
                lambda: video_comment_create_notification_create_task.delay(
                    video_id, self.request.user.id, comment.id, user_type="parent"
                )
            )
        elif (
            self.request.user
            and self.request.user.is_authenticated
            and self.request.user.is_expert
        ):
            comment = serializer.save(
                expert=self.request.user.expert_user, video_id=video_id
            )
            transaction.on_commit(
                lambda: video_comment_create_notification_create_task.delay(
                    video_id, self.request.user.id, comment.id, user_type="expert"
                )
            )
        else:
            serializer.save(video_id=video_id)


class ExpertVideoThreadCommentView(generics.ListAPIView):
    serializer_class = ExpertVideoCommentSerializer

    def get_queryset(self):
        queryset = ExpertVideoComment.objects.get_list_api_items()
        comment_id = self.kwargs.get("comment_id", None)
        if comment_id is not None:
            queryset = queryset.filter(parent_comment_id=comment_id)
        if self.request.user and self.request.user.is_authenticated:
            video_comments_likes = self.request.user.user_liked_video_comments.values_list(
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


class ExpertVideoThreadCommentCreateView(generics.CreateAPIView):
    serializer_class = ExpertVideoThreadCommentCreateSerializer

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
            transaction.on_commit(
                lambda: video_comment_thread_create_notification_create_task.delay(
                    video_id,
                    self.request.user.id,
                    thread_comment.id,
                    parent_comment_id=comment_id,
                    user_type="parent",
                )
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
            transaction.on_commit(
                lambda: video_comment_thread_create_notification_create_task.delay(
                    video_id,
                    self.request.user.id,
                    thread_comment.id,
                    parent_comment_id=comment_id,
                    user_type="expert",
                )
            )
        else:
            serializer.save(video_id=video_id, parent_comment_id=comment_id)


class ExpertVideoLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        video_id = self.kwargs.get("video_id", None)
        video = generics.get_object_or_404(
            ExpertUserVideo, pk=video_id, status="P")
        if video.likes.filter(id=request.user.id).exists():
            video.likes.remove(request.user.id)
            transaction.on_commit(
                lambda: video_notification_delete_task.delay(
                    video_id, request.user.id)
            )

            return Response({"unliked": "Successfully Unliked!"})
        else:
            video.likes.add(request.user.id)
            transaction.on_commit(
                lambda: video_notification_create_task.delay(
                    video_id, request.user.id)
            )

            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class ExpertVideoCommentLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get("comment_id", None)
        video_comment = generics.get_object_or_404(
            ExpertVideoComment, pk=comment_id)
        if video_comment.likes.filter(id=request.user.id).exists():
            video_comment.likes.remove(request.user.id)
            transaction.on_commit(
                lambda: video_comment_notification_delete_task.delay(
                    comment_id, request.user.id
                )
            )

            return Response({"unliked": "Successfully Unliked!"})
        else:
            video_comment.likes.add(request.user.id)
            transaction.on_commit(
                lambda: video_comment_notification_create_task.delay(
                    comment_id, request.user.id
                )
            )

            return Response({"liked": "Successfully Liked!"})
        return Response({"liked": "Successfully Liked!"})


class RelatedExpertVideoListView(generics.ListAPIView):
    serializer_class = ExpertUserVideoListSerializer
    filterset_class = ExpertUserVideoFilter

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        try:
            video = (
                ExpertUserVideo.objects.get_published()
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
            ExpertUserVideo.objects.filter(tags__id__in=all_tags_id)
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
                    "board_videos",
                    queryset=ExpertUserVideo.objects.get_list_api_items().order_by(
                        "-id"
                    ),
                )
            )
            .order_by("min_age")
        ):
            queryset = board.board_videos.all()[: int(limit)]
            serializer = ExpertUserVideoListSerializer(queryset, many=True)
            response[board.slug] = serializer.data
        return Response(response, status=status.HTTP_200_OK)


class VideosSitemapData(APIView):
    def get(self, request, format=False):
        data = list(ExpertUserVideo.objects.get_published().values_list("slug", flat=True))
        return Response(data, status=status.HTTP_200_OK)
