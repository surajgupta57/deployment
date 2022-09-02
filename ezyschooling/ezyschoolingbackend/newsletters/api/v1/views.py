from django.db import transaction
from django.utils.timezone import now
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from newsletters.models import *
from newsletters.tasks import (subscribe_anonymous_user,
                               subscribe_registered_user, unsubscribe_user)
from parents.permissions import IsParent

from .serializers import *

from backend.logger import info_logger,error_logger

class PreferencesView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsParent]
    serializer_class = PreferenceSerializer
    queryset = Preference.objects.all()

    def perform_update(self, serializer):
        data = serializer.validated_data
        quiz = data.get("quiz", None)
        parenting = data.get("parenting", None)

        if quiz is not None:
            info_logger(f"{self.__class__.__name__} Updating Object for user {self.request.user.id} and quiz {quiz}")
            subscription, _ = Subscription.objects.get_or_create(
                preferences=self.request.user.mail_preferences, group=Subscription.QUIZ)
            subscription.active = quiz
            subscription.save()

        if parenting is not None:
            info_logger(f"{self.__class__.__name__} Updating Object for user {self.request.user.id} and parenting {parenting}")
            subscription, _ = Subscription.objects.get_or_create(
                preferences=self.request.user.mail_preferences, group=Subscription.PARENTING)
            if subscription.active == False:
                subscription.active = parenting
                subscription.save()
                transaction.on_commit(
                    lambda: subscribe_registered_user.delay(
                        subscription.get_email())
                )
            elif subscription.active == True:
                subscription.active = parenting
                subscription.save()
                transaction.on_commit(
                    lambda: unsubscribe_user.delay(subscription.get_email())
                )

        serializer.save()

    def get_object(self):
        return self.request.user.mail_preferences


class SubscriptionCreateView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

    def perform_create(self, serializer):
        data = serializer.validated_data
        group = data.get("group", None)
        email = data.get("email", None)
        if group == Subscription.PARENTING:
            if self.request.user.is_authenticated:
                serializer.save(
                    preferences=self.request.user.mail_preferences, active=True, subscribed_date=now())
                transaction.on_commit(
                    lambda: subscribe_registered_user.delay(self.request.user.email)
                )
            else:
                serializer.save(active=True, subscribed_date=now())
                transaction.on_commit(
                    lambda: subscribe_anonymous_user.delay(email)
                )
        else:
            serializer.save(active=True, subscribed_date=now())


class SubscriptionUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = SubscriptionUpdateSerializer
    queryset = Subscription.objects.all()
    lookup_field = "uuid"

    def perform_update(self, serializer):
        uuid = self.kwargs['uuid']
        subscription = Subscription.objects.get(uuid=uuid)
        data = serializer.validated_data
        active = data.get("active", None)
        unsubscribe_flag = 0
        if active == False:
            if subscription.group == Subscription.PARENTING:
                unsubscribe_flag = 1
        serializer.save()

        if unsubscribe_flag:
            transaction.on_commit(
                lambda: unsubscribe_user.delay(subscription.get_email())
            )
