from rest_framework import serializers

from accounts.api.v1.serializers import UserSerializer
from articles.api.v1.serializers import (
    ExpertArticleCommentNotificationSerializer,
    ExpertArticleNotificationSerializer)
from articles.models import ExpertArticle, ExpertArticleComment
from discussions.api.v1.serializers import (
    DiscussionCommentNotificationSerializer, DiscussionNotificationSerializer)
from discussions.models import Discussion, DiscussionComment
from experts.api.v1.serializers import ExperUserBasicProfileSerializer
from experts.models import ExpertUserProfile
from parents.api.v1.serializers import ParentArticleProfileSerializer
from parents.models import ParentProfile
from videos.api.v1.serializers import (
    ExpertUserVideoCommentNotificationSerializer,
    ExpertUserVideoNotificationSerializer)
from videos.models import ExpertUserVideo, ExpertVideoComment


class GenericNotificationRelatedField(serializers.RelatedField):
    def to_representation(self, instance):
        if isinstance(instance, ExpertArticle):
            serializer = ExpertArticleNotificationSerializer(instance)
        if isinstance(instance, ParentProfile):
            serializer = ParentArticleProfileSerializer(instance)
        if isinstance(instance, ExpertUserProfile):
            serializer = ExperUserBasicProfileSerializer(instance)
        if isinstance(instance, Discussion):
            serializer = DiscussionNotificationSerializer(instance)
        if isinstance(instance, ExpertUserVideo):
            serializer = ExpertUserVideoNotificationSerializer(instance)
        if isinstance(instance, ExpertArticleComment):
            serializer = ExpertArticleCommentNotificationSerializer(instance)
        if isinstance(instance, DiscussionComment):
            serializer = DiscussionCommentNotificationSerializer(instance)
        if isinstance(instance, ExpertVideoComment):
            serializer = ExpertUserVideoCommentNotificationSerializer(instance)
        return serializer.data
