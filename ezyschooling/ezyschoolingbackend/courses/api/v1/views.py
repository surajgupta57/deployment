import time
from datetime import datetime

import pytz
import razorpay
from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import *

from .serializers import *


class CourseEnrollmentView(generics.CreateAPIView):
    serializer_class = CourseEnrollmentSerializer
    queryset = CourseEnrollment.objects.all()


class CourseEnquiryView(generics.CreateAPIView):
    serializer_class = CourseEnquirySerializer
    queryset = CourseEnquiry.objects.all()


class CourseDemoClassView(generics.CreateAPIView):
    serializer_class = CourseDemoClassSerializer
    queryset = CourseDemoClassRegistration.objects.all()


class CourseOrderView(APIView):

    def post(self, request, format=None):
        serializer = CourseOrderCreateSerializer(data=request.data)
        if serializer.is_valid():

            data = serializer.validated_data
            client = razorpay.Client(
                auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))

            DATA = {
                "amount": data['amount']*100,
                "currency": "INR",
                "receipt": "ezy_receipt_" + str(time.time()),
                "payment_capture": 1
            }

            r_data = client.order.create(data=DATA)

            enrollment = CourseEnrollment.objects.filter(
                pk=data['enrollment_id'])
            if enrollment.exists():
                enrollment = enrollment.first()
                CourseOrder.objects.create(
                    enrollment=enrollment, amount=data['amount'], order_id=r_data["id"])
                return Response({"order_id": r_data["id"]}, status=status.HTTP_201_CREATED)
            else:
                raise serializers.ValidationError({
                    "enrollment": "No Course Enrollment with the given id exists."
                })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseTransactionView(APIView):

    def patch(self, request, *args, **kwargs):
        serializer = CourseTransactionSerializer(data=request.data)

        if serializer.is_valid():
            razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
            razorpay_order_id = serializer.validated_data["razorpay_order_id"]
            enrollment_id = serializer.validated_data["enrollment_id"]
            razorpay_signature = serializer.validated_data["razorpay_signature"]
            order = CourseOrder.objects.get(
                enrollment__pk=enrollment_id, order_id=razorpay_order_id)

            if order.order_id == razorpay_order_id:

                client = razorpay.Client(
                    auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                res = client.payment.fetch(razorpay_payment_id)

                local_tz = pytz.timezone("Asia/Kolkata")
                utc_dt = datetime.utcfromtimestamp(
                    res["created_at"]).replace(tzinfo=pytz.utc)
                local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

                transaction = CourseTransaction(payment_id=res["id"],
                                                status=res["status"],
                                                method=res["method"],
                                                amount=res["amount"],
                                                card_id=res["card_id"],
                                                bank=res["bank"],
                                                wallet=res["wallet"],
                                                order_id=res["order_id"],
                                                created_at=res["created_at"],
                                                timestamp=local_dt
                                                )
                transaction.save()
                order.payment = transaction
                order.signature = razorpay_signature
                order.save(update_fields=["signature", "payment"])

                if res["status"] == "captured":
                    enrollment = CourseEnrollment.objects.get(pk=enrollment_id)
                    enrollment.paid = True
                    enrollment.save()
                    return Response({"payment": "success"}, status.HTTP_200_OK)

                return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
            return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
