from allauth.account import app_settings as allauth_settings
from django.db.models import Count
from django.http import Http404
from notifications.models import Notification
from rest_auth.registration.views import RegisterView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.v1.serializers import TokenSerializer
from admission_forms.api.v1.serializers import (
        ParentReceiptListSerializer, ParentSchoolApplicationListSerializer, ParentApplicationStatusLogSerializer)
from admission_forms.models import CommonRegistrationForm, SchoolApplication
from articles.api.v1.serializers import ExpertArticleListSerializer
from articles.filters import ExpertArticleFilter
from articles.models import ExpertArticle
from core.serializers import NotificationSerializer
from discussions.api.v1.serializers import DiscussionListSerializer
from discussions.filters import DiscussionFilter
from discussions.models import Discussion
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from parents.models import ParentProfile,ParentAddress
from parents.permissions import (IsParent, IsParentOrAuthenticatedReadOnly,
                                 IsParentOrReadOnly, ParentProfileModification)
from tags.api.v1.serializers import CustomTagSerializer
from tags.filters import TagsFilter
from tags.models import CustomTag
from videos.api.v1.serializers import ExpertUserVideoListSerializer
from videos.filters import ExpertUserVideoFilter
from videos.models import ExpertUserVideo
from rest_framework import generics,status
from rest_framework.exceptions import APIException
from .serializers import *
from django.utils.encoding import force_text
from django.dispatch import Signal, receiver
from parents.tasks import send_parent_regional_mail
from django.db import transaction

from accounts.api.v1.views import login_signal

from backend.logger import info_logger,error_logger
#
# class ParentMainPageView(APIView):
#     def get(self, request, format=False):
#         limit = 7   #limit the number of top/latest reads and videos to 7
#         response = {}   #dict where response will be send
#         order=("top_reads","latest_reads","top_videos","latest_videos")
#         for i in order:
#             #results={}    #creating a dict with key "results" where serializer data will be stored
#             if(i=="top_reads"):     #0 index represent Top reads after ordering them according to views,likes_count and comments_count and limiting them to 7
#                 queryset = ExpertArticle.objects.get_list_api_items().order_by("-views","-like_counts","-comment_counts")[: int(limit)]
#                 serializer = ExpertArticleListSerializer(queryset, many=True)
#             elif(i=="latest_reads"):    #1 index represent latest reads after ordering them according to the time of creation and limiting them to 7
#                 queryset = ExpertArticle.objects.get_list_api_items().order_by("-timestamp")[: int(limit)]
#                 serializer = ExpertArticleListSerializer(queryset, many=True)
#             elif(i=="top_videos"):    #2 index represent Top videos after ordering them according to views,likes_count and comments_count and limiting them to 7
#                 queryset = ExpertUserVideo.objects.get_list_api_items().order_by("-views","-likes_count","-comment_count")[: int(limit)]
#                 serializer = ExpertUserVideoListSerializer(queryset, many=True)
#             else:          #3 index represent latest videos after ordering them according to the time of creation and limiting them to 7
#                 queryset = ExpertUserVideo.objects.get_list_api_items().order_by("-timestamp")[: int(limit)]
#                 serializer = ExpertUserVideoListSerializer(queryset, many=True)
#             #results["results"] = serializer.data
#             response[i] = serializer.data
#         return Response(response, status=status.HTTP_200_OK)
#

#creating a new api for rendering articles according to age category
class ParentMainPageView(APIView):
    def get(self, request, format=False):
        limit = 7   #limit the number of top/latest reads and videos to 7
        response = {}   #dict where response will be send
        order=("top_reads","latest_reads","top_videos","latest_videos")
        age_range=self.request.query_params.get('age', '')  #getting age category from query params
        sub_category=self.request.query_params.get('sub_category', '') #getting age category from query params
        if(len(sub_category)==0 and len(age_range)==0):
            for i in order:
                if (i == "top_reads"):  # 0 index represent Top reads after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().order_by("-views", "-like_counts","-comment_counts")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif (i == "latest_reads"):  # 1 index represent latest reads after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().order_by("-timestamp")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif (i == "top_videos"):  # 2 index represent Top videos after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().order_by("-views", "-likes_count","-comment_count")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                else:  # 3 index represent latest videos after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().order_by("-timestamp")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                response[i] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        elif(len(sub_category)!= 0 and len(age_range)!=0):
            for i in order:
                if (i == "top_reads"):  # 0 index represent Top reads after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(board__slug__iexact=age_range).filter(sub_category__slug__iexact=sub_category).order_by("-views", "-like_counts", "-comment_counts")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif (i == "latest_reads"):  # 1 index represent latest reads after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(board__slug__iexact=age_range).filter(sub_category__slug__iexact=sub_category).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif (i == "top_videos"):  # 2 index represent Top videos after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(board__slug__iexact=age_range).filter(sub_category__slug__iexact=sub_category).order_by("-views", "-likes_count", "-comment_count")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                else:  # 3 index represent latest videos after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(board__slug__iexact=age_range).filter(sub_category__slug__iexact=sub_category).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                response[i] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        elif(len(sub_category)==0):
            for i in order:
                if(i=="top_reads"):     #0 index represent Top reads after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(board__slug__iexact=age_range).order_by("-views","-like_counts","-comment_counts")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif(i=="latest_reads"):    #1 index represent latest reads after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(board__slug__iexact=age_range).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif(i=="top_videos"):    #2 index represent Top videos after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(board__slug__iexact=age_range).order_by("-views","-likes_count","-comment_count")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                else:          #3 index represent latest videos after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(board__slug__iexact=age_range).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                response[i] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        elif(len(age_range)==0):
            for i in order:
                if(i=="top_reads"):     #0 index represent Top reads after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(sub_category__slug__iexact=sub_category).order_by("-views","-like_counts","-comment_counts")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif(i=="latest_reads"):    #1 index represent latest reads after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertArticle.objects.get_list_api_items().filter(sub_category__slug__iexact=sub_category).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertArticleListSerializer(queryset, many=True)
                elif(i=="top_videos"):    #2 index represent Top videos after ordering them according to views,likes_count and comments_count and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(sub_category__slug__iexact=sub_category).order_by("-views","-likes_count","-comment_count")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                else:          #3 index represent latest videos after ordering them according to the time of creation and limiting them to 7
                    queryset = ExpertUserVideo.objects.get_list_api_items().filter(sub_category__slug__iexact=sub_category).order_by("-timestamp")[: int(limit)]
                    serializer = ExpertUserVideoListSerializer(queryset, many=True)
                response[i] = serializer.data
            return Response(response, status=status.HTTP_200_OK)

# address_update = Signal(providing_args=["context"])

class ParentRegisterView(RegisterView):
    serializer_class = ParentRegisterSerializer

    def get_response_data(self, user):
        if (
            allauth_settings.EMAIL_VERIFICATION
            == allauth_settings.EmailVerificationMethod.MANDATORY
        ):
            return {"detail": _("Verification e-mail sent.")}

        if getattr(settings, "REST_USE_JWT", False):
            data = {"user": user, "token": self.token}
            return JWTSerializer(data).data
        else:
            return TokenSerializer(user.auth_token.first()).data

class ParentRegisterAddressView(generics.GenericAPIView):
    serializer_class = ParentAddressSerializer
    permission_classes = [
        IsParent,
    ]
    def get(self, request,*args,**kwargs):
        try:
            try:
                self.parent=ParentProfile.objects.filter(user=request.user).first()
            except ParentProfile.DoesNotExist:
                error_logger(f"{self.__class__.__name__} Parent Doesn't Exist id {self.request.user.id}")
                self.parent=None
            if self.parent is None:
                error_logger(f"{self.__class__.__name__} Data for given id doesn't exist id {self.request.user.id}")
                raise CustomValidation('Data For Given id do not exist', 'data', status_code=status.HTTP_404_NOT_FOUND)
            else:
                self.data = ParentAddress.objects.filter(parent=self.parent).first()
                self.serializer = self.get_serializer(self.data)
        except ParentAddress.DoesNotExist:
             raise CustomValidation('Data For Given id do not exist', 'data', status_code=status.HTTP_404_NOT_FOUND)
        return Response({
            "data": self.serializer.data,
            "status": status.HTTP_200_OK
        })

    def post(self, request, *args, **kwargs):
        try:
             self.serializer = self.get_serializer(data=request.data)
             self.parent=ParentProfile.objects.filter(user=request.user).first()
             try:
                self.instance=ParentAddress.objects.filter(parent=self.parent).first()
                self.serializer = self.get_serializer(self.instance, data=request.data)
                self.serializer.is_valid(raise_exception=True)
                address=self.serializer.save(parent=self.parent,user = request.user)
                if address.region and address.region.id in [3,4,12]:
                    transaction.on_commit(
                        lambda: send_parent_regional_mail.delay(self.parent.id,address.region.id)
                    )
                login_signal.send(sender=self.__class__, PING=True,user=request.user)
             except ParentAddress.DoesNotExist:
                 error_logger(f"{self.__class__.__name__} ParentAddress for given id doesn't exist id {self.request.user.id}")
                 self.serializer.is_valid(raise_exception=True)
                 address=self.serializer.save(parent=self.parent,user = request.user)
                 login_signal.send(sender=self.__class__, PING=True,user=request.user)
                 return Response({
                        "status": status.HTTP_201_CREATED
                    })
        except ParentProfile.DoesNotExist:
             raise CustomValidation('parentprofile does not exist ', 'data', status_code=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": status.HTTP_202_ACCEPTED,
            "Message":"Data Updated"
        })



class ParentProfileDetailView(APIView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.is_parent:
            try:
                parent = ParentProfile.objects.only(
                    "id",
                    "name",
                    "email",
                    "photo",
                    "parent_type",
                    "slug",
                    "bio",
                    "gender",
                    "user",
                ).get(id=self.request.user.current_parent)
                serializer = ParentProfileDetailSerializer(parent)
                return Response(serializer.data)
            except ObjectDoesNotExist:
                error_logger(f"{self.__class__.__name__} ProfileData for given id doesn't exist id {self.request.user.id}")
                return Response(status=status.HTTP_404_NOT_FOUND)
        error_logger(f"{self.__class__.__name__} FORBIDDEN 403")
        return Response(status=status.HTTP_403_FORBIDDEN)


class ParentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParentProfileDetailSerializer
    lookup_field = "slug"
    permission_classes = [
        ParentProfileModification,
    ]

    def get_queryset(self):
        return ParentProfile.objects.only(
            "id",
            "name",
            "email",
            "photo",
            "parent_type",
            "slug",
            "bio",
            "gender",
            "user",
        ).all()

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ParentAddView(generics.ListCreateAPIView):
    serializer_class = ParentProfileAddSerializer
    permission_classes = [
        IsParentOrAuthenticatedReadOnly,
    ]

    def get_queryset(self):
        return ParentProfile.objects.filter(user=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ParentProfileDetailSerializer
        if self.request.method == "POST":
            return ParentProfileAddSerializer


class ParentBookmarkedArticle(generics.ListAPIView):
    filterset_class = ExpertArticleFilter
    permission_classes = [
        IsParent,
    ]
    serializer_class = ExpertArticleListSerializer

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        return (
            parent.bookmarked_articles.filter(status="P")
            .select_related("board", "sub_category", "created_by")
            .annotate(
                likes_count=Count("likes"), comment_count=Count("article_comments"),
            )
        )


class ParentBookmarkedVideo(generics.ListAPIView):
    serializer_class = ExpertUserVideoListSerializer
    filterset_class = ExpertUserVideoFilter
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        return (
            parent.bookmarked_videos.filter(status="P")
            .select_related("board", "sub_category", "expert")
            .annotate(likes_count=Count("likes"), comment_count=Count("video_comments"))
        )


class ParentBookmarkedDiscussion(generics.ListAPIView):
    filterset_class = DiscussionFilter
    serializer_class = DiscussionListSerializer
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        return (
            parent.bookmarked_discussions.filter(status="P")
            .select_related("board", "sub_category", "parent", "expert",)
            .annotate(
                likes_count=Count("likes"), comment_count=Count("discussion_comments")
            )
        )


class ParentLikedArticle(generics.ListAPIView):
    filterset_class = ExpertArticleFilter
    permission_classes = [
        IsParent,
    ]
    serializer_class = ExpertArticleListSerializer

    def get_queryset(self):
        return (
            self.request.user.user_liked_expert_articles.get_published()
            .get_list_items()
            .get_foreignkey_select_related()
        )


class ParentLikedVideo(generics.ListAPIView):
    serializer_class = ExpertUserVideoListSerializer
    filterset_class = ExpertUserVideoFilter
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        return (
            self.request.user.user_liked_videos.get_published()
            .get_list_items()
            .get_foreignkey_select_related()
            .like_comment_count()
        )


class ParentLikedDiscussion(generics.ListAPIView):
    filterset_class = DiscussionFilter
    serializer_class = DiscussionListSerializer
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        return (
            self.request.user.discussion_likes.get_published()
            .get_list_items()
            .get_foreignkey_select_related()
            .like_comment_count()
        )


class ParentArticleBookmarkAPIView(APIView):
    permission_classes = (IsParent,)

    def post(self, request, *args, **kwargs):
        article_id = self.kwargs.get("article_id", None)
        parent = generics.get_object_or_404(
            ParentProfile, id=request.user.current_parent
        )
        try:
            article = generics.get_object_or_404(ExpertArticle, id=article_id)
            if parent.bookmarked_articles.filter(id=article_id).exists():
                parent.bookmarked_articles.remove(article)
                return Response({"unbookmarked": "Successfully UnBookmarked!"})
            else:
                parent.bookmarked_articles.add(article)
                return Response({"bookmarked": "Successfully Bookmarked!"})
            return Response({"bookmarked": "Successfully Bookmarked!"})
        except ObjectDoesNotExist:
            error_logger(f"{self.__class__.__name__} Article Doesn't Exist id {article_id}")
            raise Http404


class ParentBookmarkVideoAPIView(APIView):
    permission_classes = (IsParent,)

    def post(self, request, *args, **kwargs):
        video_id = self.kwargs.get("video_id", None)
        parent = generics.get_object_or_404(
            ParentProfile, id=request.user.current_parent
        )
        try:
            video = generics.get_object_or_404(ExpertUserVideo, id=video_id)
            if parent.bookmarked_videos.filter(id=video_id).exists():
                parent.bookmarked_videos.remove(video)
                return Response({"unbookmarked": "Successfully UnBookmarked!"})
            else:
                parent.bookmarked_videos.add(video)
                return Response({"bookmarked": "Successfully Bookmarked!"})
            return Response({"bookmarked": "Successfully Bookmarked!"})
        except ObjectDoesNotExist:
            error_logger(f"{self.__class__.__name__} Video Doesn't Exist id {video_id}")
            raise Http404


class ParentBookmarkDiscussionAPIView(APIView):
    permission_classes = (IsParent,)

    def post(self, request, *args, **kwargs):
        discussion_id = self.kwargs.get("discussion_id", None)
        parent = generics.get_object_or_404(
            ParentProfile, id=request.user.current_parent
        )
        try:
            discussion = generics.get_object_or_404(
                Discussion, id=discussion_id)
            if parent.bookmarked_discussions.filter(id=discussion_id).exists():
                parent.bookmarked_discussions.remove(discussion)
                return Response(
                    {"unbookmarked": "Successfully UnBookmarked!"},
                    status=status.HTTP_200_OK,
                )
            else:
                parent.bookmarked_discussions.add(discussion)
                return Response(
                    {"bookmarked": "Successfully Bookmarked!"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"bookmarked": "Successfully Bookmarked!"}, status=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            error_logger(f"{self.__class__.__name__} ParentDiscussion Doesn't Exist id {discussion_id}")
            raise Http404


class ParentFollowTagListAPIView(generics.ListAPIView):
    serializer_class = CustomTagSerializer
    permission_classes = [
        IsParent,
    ]
    filterset_class = TagsFilter

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        return (
            parent.follow_tags.all()
            .annotate(parent_following_count=Count("followers"))
            .order_by("-parent_following_count")
        )


class AllTagExpertParentTagListAPIView(generics.ListAPIView):
    serializer_class = CustomTagSerializer
    permission_classes = [
        IsParent,
    ]
    filterset_class = TagsFilter

    def get_queryset(self):
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        parent_tags_id = parent.follow_tags.values_list("id", flat=True)
        queryset = (
            CustomTag.objects.exclude(id__in=parent_tags_id)
            .annotate(parent_following_count=Count("followers"))
            .order_by("-parent_following_count")
        )
        return queryset


class ParentFollowTagAPIView(APIView):
    permission_classes = [
        IsParent,
    ]

    def post(self, request, *args, **kwargs):
        tag_slug = self.kwargs.get("tag_slug", None)
        parent = generics.get_object_or_404(
            ParentProfile, id=request.user.current_parent
        )
        try:
            tag = generics.get_object_or_404(CustomTag, slug=tag_slug)
            if parent.follow_tags.filter(slug=tag_slug).exists():
                parent.follow_tags.remove(tag)
                return Response(
                    {"unfollowed": "Successfully UnFollowed this tag!"},
                    status=status.HTTP_200_OK,
                )
            else:
                parent.follow_tags.add(tag)
                return Response(
                    {"followed": "Successfully Followed this tag"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"followed": "Successfully Followed this tag"},
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            error_logger(f"{self.__class__.__name__} Tag Doesn't Exist id {tag_slug}")
            raise Http404


class ParentNotificationView(generics.ListAPIView):
    permission_classes = [
        IsParent,
    ]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return (
            self.request.user.notifications.all()
            .prefetch_related("actor")
            .prefetch_related("target", "action_object")
        )


class ParentUnreadNotificationView(generics.ListAPIView):
    permission_classes = [
        IsParent,
    ]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return (
            self.request.user.notifications.unread()
            .prefetch_related("actor")
            .prefetch_related("target", "action_object")
        )


class ParentNotificationMarkReadView(APIView):
    permission_classes = [
        IsParent,
    ]

    def post(self, request, *args, **kwargs):
        notification_id = self.kwargs.get("notification_id", None)
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()
            return Response(
                {"success": "Successfully marked notification as Read"},
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            error_logger(f"{self.__class__.__name__} Notification Doesn't Exist id {notification_id}")
            raise Http404


class ParentFollowTagStats(APIView):
    permission_classes = [
        IsParent,
    ]

    def get(self, *args, **kwargs):
        tag_name = self.kwargs["tag_name"]
        parent = generics.get_object_or_404(
            ParentProfile, id=self.request.user.current_parent
        )
        tag_status = parent.follow_tags.filter(name=tag_name).exists()
        return Response({"tag_status": tag_status}, status=status.HTTP_200_OK)


class ParentReceiptListView(generics.ListAPIView):
    serializer_class = ParentReceiptListSerializer
    filterset_fields = ["child", "child__slug"]
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        return SchoolApplication.objects.select_related("child", "school", "receipt").filter(user=self.request.user)

class ParentApplicationStatusLogView(generics.RetrieveAPIView):
    serializer_class = ParentApplicationStatusLogSerializer
    permission_classes = [IsParent,]

    def get_queryset(self):
        return SchoolApplication.objects.filter(user=self.request.user)

class SchoolsAppliedView(generics.ListAPIView):
    serializer_class = ParentSchoolApplicationListSerializer
    filterset_fields = ["child", "child__slug"]
    permission_classes = [
        IsParent,
    ]

    def get_queryset(self):
        return SchoolApplication.objects.select_related("child", "school").filter(user=self.request.user)


class CustomValidation(APIException):
    """
     To rise custom validation errors
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, detail, field, status_code):
        if status_code is not None:self.status_code = status_code
        if detail is not None:
            self.detail = {field: force_text(detail)}
        else: self.detail = {'detail': force_text(self.default_detail)}
