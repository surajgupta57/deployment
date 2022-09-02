import requests
from allauth.socialaccount.providers.facebook.views import \
    FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from rest_auth.registration.views import (SocialConnectView, SocialLoginView,
                                          VerifyEmailView)
from rest_auth.views import LoginView, LogoutView
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import ExpiringTokenAuthentication
from accounts.models import Token, User
from newsletters.models import Preference, Subscription
from newsletters.tasks import subscribe_registered_user
from parents.models import ParentProfile
from parents.tasks import *
from schools.models import SchoolEqnuirySource
from .serializers import CustomSocialLoginSerializer, UserSerializer
from requests.exceptions import HTTPError
import json
import logging
from django.dispatch import Signal, receiver
from backend.logger import info_logger,error_logger

logger = logging.getLogger('oauth-logger')
logger.setLevel(logging.ERROR)

formatter = logging.Formatter("%(levelname)s %(asctime)s "
"%(thread)d %(message)s")

file_handler = logging.FileHandler(os.path.join(settings.BASE_DIR,'google-oauth.log'))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

login_signal = Signal(providing_args=["context"])

class Logout(LogoutView):
    def logout(self, request):
        try:
            request.auth.delete()
        except (AttributeError, ObjectDoesNotExist):
            pass
        if getattr(settings, "REST_SESSION_LOGIN", True):
            django_logout(request)

        response = Response(
            {"detail": _("Successfully logged out.")}, status=status.HTTP_200_OK
        )
        if getattr(settings, "REST_USE_JWT", False):
            from rest_framework_jwt.settings import api_settings as jwt_settings

            if jwt_settings.JWT_AUTH_COOKIE:
                response.delete_cookie(jwt_settings.JWT_AUTH_COOKIE)
        return response


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


class CustomGoogleLogin(generics.GenericAPIView):
    serializer_class = CustomSocialLoginSerializer

    def post(self, request, *args, **kwargs):
        self.serializer = self.get_serializer(data=self.request.data,
                                              context={'request': request})
        if self.serializer.is_valid():
            email = self.request.data["email"]
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                token = Token.objects.create(user=user)
                login_signal.send(sender=self.__class__, PING=True,user=user)
                return Response({"key": token.key,"is_uniform_app":user.is_uniform_app,"is_facebook_user":user.is_facebook_user})
            else:
                user_email = self.request.data["email"]
                first_name = self.request.data["first_name"]
                last_name = self.request.data["last_name"]
                ad_source = self.request.GET.get('ad_source','')
                if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
                    ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
                else:
                    ad_source =''
                full_name = first_name + ' ' + last_name
                username_decide = user_email+last_name
                user_new = User.objects.create(email=user_email,name=full_name,username=username_decide,ad_source=ad_source)
                token = Token.objects.create(user=user_new)
                parent_profile = ParentProfile.objects.create(user=user_new, name=full_name, email=user_email)
                login_signal.send(sender=self.__class__, PING=True,user=user_new)
                transaction.on_commit(
                    lambda: add_parent_to_google_sheets.delay(parent_profile.id)
                )
                newsletter_pref = Preference.objects.create(user=user_new)
                subs = Subscription.objects.create(
                    preferences=newsletter_pref,
                    group=Subscription.PARENTING,
                    active=True,
                    subscribed_date=now())
                transaction.on_commit(
                    lambda: subscribe_registered_user.delay(subs.get_email())
                )
                user_new.current_parent = parent_profile.id
                user_new.is_parent = True
                user_new.save(update_fields=["current_parent", "is_parent"])
                if "is_uniform_app" in self.request.data:
                    user_new.is_uniform_app=True
                    user_new.save(update_fields=["is_uniform_app"])

                if "is_facebook_user" in self.request.data:
                    user_new.is_facebook_user=True
                    user_new.save(update_fields=["is_facebook_user"])

                transaction.on_commit(
                    lambda: send_parent_welcome_mail.delay(parent_profile.id)
                )
                return Response({"key": token.key,"is_uniform_app":user_new.is_uniform_app,"is_facebook_user":user_new.is_facebook_user})

            data = {
                "access_token": self.request.data["access_token"],
                "code": self.request.data["code"]
            }
            try:
                response = requests.post(request.build_absolute_uri(reverse("accounts:google_rest_login")), data=data)
                response.raise_for_status()
            except HTTPError as http_err:
                error_logger(f'{self.__class__.__name__} HTTP error occurred: {http_err}')
                logger.error(f'HTTP error occurred: {http_err}')
            except Exception as err:
                error_logger(f'{self.__class__.__name__} Normal err: {err}')
                logger.error(f'Normal error occurred: {err}')

            try:
                user = User.objects.get(email=email)
                if not user.current_parent == -1:
                    return Response(response.json())
                name = user.first_name + " " + user.last_name
                parent_profile = ParentProfile.objects.create(
                    user=user, name=name, email=email
                )
                login_signal.send(sender=self.__class__, PING=True,user=user)
                transaction.on_commit(
                    lambda: add_parent_to_google_sheets.delay(parent_profile.id)
                )
                newsletter_pref = Preference.objects.create(user=user)
                subs = Subscription.objects.create(
                    preferences=newsletter_pref,
                    group=Subscription.PARENTING,
                    active=True,
                    subscribed_date=now())
                transaction.on_commit(
                    lambda: subscribe_registered_user.delay(subs.get_email())
                )
                user.current_parent = parent_profile.id
                user.is_parent = True
                user.save(update_fields=["current_parent", "is_parent"])
                if "is_uniform_app" in self.request.data:
                    user.is_uniform_app=True
                    user.save(update_fields=["is_uniform_app"])

                if "is_facebook_user" in self.request.data:
                    user.is_facebook_user=True
                    user.save(update_fields=["is_facebook_user"])

                transaction.on_commit(
                    lambda: send_parent_welcome_mail.delay(parent_profile.id)
                )
                return Response(response.json())
            except Exception as e:
                error_logger(f'{self.__class__.__name__} Error: {e}')
                logger.error(f'Unknown error: {e}')
                return Response({"error":"Unknown error"})
        return Response(self.serializer.errors)


class CustomVerifyEmailView(VerifyEmailView):
    pass


class CustomLoginView(LoginView):
    def get_response(self):
        orginal_response = super().get_response()
        mydata = {
            "is_parent": self.request.user.is_parent,
            "is_expert": self.request.user.is_expert,
            "is_brand": self.request.user.is_brand,
            "is_school": self.request.user.is_school,
            "is_uniform_app":self.request.user.is_uniform_app,
            "is_facebook_user":self.request.user.is_facebook_user,
        }
        orginal_response.data.update(mydata)
        login_signal.send(sender=self.__class__, PING=True,user=self.request.user)
        return orginal_response


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, ]

    def get_object(self):
        queryset = self.get_queryset()
        self.check_object_permissions(self.request, self.request.user)
        return self.request.user


class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter


class GoogleConnect(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
