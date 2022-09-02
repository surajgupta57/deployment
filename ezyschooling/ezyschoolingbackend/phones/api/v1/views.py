from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from parents.permissions import IsParent
from phones.utils import check_verification_code, send_verification_code
from notification.models import WhatsappSubscribers
from .serializers import *


class PhoneNumberView(APIView):
    permission_classes = [IsParent]

    def post(self, request, *args, **kwargs):
        serializer = PhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            number = data["number"]
            instance, created = PhoneNumber.objects.get_or_create(user=request.user, number=number)
            subscribe_obj, _ = WhatsappSubscribers.objects.get_or_create(user=self.request.user,phone_number=number)
            subscribe_obj.is_Subscriber = True
            subscribe_obj.save()
            if created == True or instance.verified == False:
                transaction.on_commit(
                    lambda: send_verification_code(instance.id)
                )
                return Response({"status": "success"}, status.HTTP_200_OK)
            else:
                return Response({"status": "Already Verified"}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class PhoneNumberVerify(APIView):
    permission_classes = [IsParent]

    def post(self, request, *args, **kwargs):
        serializer = PhoneNumberOTPSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            number = data["number"]
            code = data["code"]
            phone = PhoneNumber.objects.get(number=number, user=request.user)
            result = check_verification_code(phone.id, code)
            if result:
                phone.verified = True
                phone.save()
                return Response({"status": "verified"}, status.HTTP_200_OK)
            else:
                return Response({"status": "failed"}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
