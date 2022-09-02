from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import NotificationSerializer
from experts.api.v1.serializers import ExpertUserSerializer
from experts.models import ExpertUserProfile
from experts.permissions import IsExpert
from videos.api.v1.serializers import ExpertUserVideoListSerializer
from videos.models import ExpertUserVideo


class ExpertNotificationView(generics.ListAPIView):
    permission_classes = [
        IsExpert,
    ]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return (
            self.request.user.notifications.all()
            .prefetch_related("actor")
            .prefetch_related("target")
        )


class ExpertPanelUserList(generics.ListAPIView):
    serializer_class = ExpertUserSerializer
    queryset = ExpertUserProfile.objects.filter(is_expert_panel=True).order_by("-id")


class ExpertUserDetails(generics.RetrieveAPIView):
    serializer_class = ExpertUserSerializer
    queryset = ExpertUserProfile.objects.filter(is_expert_panel=True)
    lookup_field = "slug"


class ExpertRelatedVideos(generics.ListAPIView):
    serializer_class = ExpertUserVideoListSerializer

    def get_queryset(self):
        slug = self.kwargs["slug"]
        expert = generics.get_object_or_404(
            ExpertUserProfile, slug=slug, is_expert_panel=True
        )
        tags_id = expert.expert_user_videos.values_list("tags__id", flat=True)
        related_videos = (
            ExpertUserVideo.objects.get_list_api_items()
            .filter(tags__id__in=tags_id)
            .exclude(expert=expert)
            .order_by("-id")[:3]
        )
        return related_videos


class ExpertProfileSitemapData(APIView):
    def get(self, request, format=False):
        data = list(ExpertUserProfile.objects.filter(is_expert_panel=True).values_list("slug", flat=True))
        return Response(data, status=status.HTTP_200_OK)
