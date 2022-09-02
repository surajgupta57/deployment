import json
import time
from datetime import datetime

import pytz
import razorpay,requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from admission_forms.models import (ChildSchoolCart, CommonRegistrationForm, CommonRegistrationFormAfterPayment,
                                    FormReceipt, SchoolApplication, ApplicationStatus, ApplicationStatusLog)
from childs.models import Child
from parents.models import ParentProfile
from parents.permissions import IsParent
from payments.models import FormOrder, FormTransaction, AdmissionGuidanceProgrammeFormOrder, AdmissionGuidanceProgrammeFormTransaction, AdmissionGuidanceFormOrder, AdmissionGuidanceFormTransaction,SchoolTransferDetail,SchoolSettlementAccounts
from schools.models import SchoolProfile, SchoolMultiClassRelation, SchoolAdmissionFormFee, Coupons
from miscs.models import AdmissionGuidanceProgrammePackage
from .serializers import CaptureTransactionSerializer, CaptureAdmissionGuidanceProgrammeTransactionSerializer, AdmissionGuidanceProgrammeOrderSerializer, CaptureAdmissionGuidanceTransactionSerializer
from miscs.tasks import add_admission_guidance_data, send_admission_guidance_mail
import os
import logging
logger = logging.getLogger('payment-logger')
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s %(asctime)s "
                              "%(thread)d %(message)s")

file_handler = logging.FileHandler(
    os.path.join(settings.BASE_DIR, 'payment_logger.log'))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def copy_the_form_data(form_id, reg_form_id):
    data = {}
    obj = CommonRegistrationForm.objects.get(id=form_id)
    list_common = ['short_address', 'street_address', 'city', 'state', 'pincode', 'country', 'last_school_name', 'last_school_board_id',
                   'last_school_address', 'last_school_class_id', 'transfer_certificate', 'single_parent_proof', 'reason_of_leaving', 'report_card',
                   'email', 'phone_no', 'single_child', 'first_child', 'single_parent', 'first_girl_child', 'staff_ward', 'sibling1_alumni_name', 'sibling1_alumni_school_name_id',
                   'sibling2_alumni_name', 'sibling2_alumni_school_name_id', 'sibling1_alumni_proof', 'sibling2_alumni_proof', 'family_photo',
                   'distance_affidavit', 'baptism_certificate', 'parent_signature_upload', 'mother_tongue', 'differently_abled_proof', 'caste_category_certificate',
                   'is_twins', 'second_born_child', 'third_born_child', 'lockstatus', 'transport_facility_required', 'session', 'father_staff_ward_school_name_id', 'father_staff_ward_department', 'father_type_of_staff_ward', 'father_staff_ward_tenure', 'mother_staff_ward_school_name_id', 'mother_staff_ward_department', 'mother_type_of_staff_ward', 'mother_staff_ward_tenure', 'guardian_staff_ward_school_name_id', 'guardian_staff_ward_department', 'guardian_type_of_staff_ward', 'guardian_staff_ward_tenure', ]

    list_parent = ['email', 'name', 'date_of_birth', 'gender', 'photo', 'companyname', 'aadhaar_number', 'transferable_job',
                   'special_ground', 'designation', 'profession', 'special_ground_proof', 'parent_aadhar_card', 'pan_card_proof', 'income',
                   'phone', 'bio', 'parent_type', 'street_address', 'city', 'state', 'pincode', 'country', 'education', 'occupation',
                   'office_address', 'office_number', 'alumni_school_name_id', 'alumni_year_of_passing', 'passing_class', 'alumni_proof', 'covid_vaccination_certificate', 'frontline_helper', 'college_name', 'course_name']

    list_child = ['name', 'photo', 'date_of_birth', 'gender', 'gender', 'religion', 'nationality', 'aadhaar_number', 'aadhaar_card_proof', 'blood_group',
                  'birth_certificate', 'address_proof', 'address_proof2', 'first_child_affidavit', 'vaccination_card', 'vaccination_card', 'minority_proof',
                  'is_christian', 'minority_points', 'student_with_special_needs_points', 'armed_force_points', 'armed_force_proof', 'orphan', 'no_school',
                  'class_applying_for_id', 'intre_state_transfer', 'illness']

    for i in list_common:
        data[i] = obj.__dict__[i]
    if obj.child:
        child = Child.objects.get(id=obj.child.id)
        for i in list_child:
            data['child_'+str(i)] = child.__dict__[i]
    if obj.father:
        father = ParentProfile.objects.get(id=obj.father.id)
        for i in list_parent:
            data['father_'+str(i)] = father.__dict__[i]
    if obj.mother:
        mother = ParentProfile.objects.get(id=obj.mother.id)
        for i in list_parent:
            data['mother_'+str(i)] = mother.__dict__[i]
    if obj.guardian:
        guardian = ParentProfile.objects.get(id=obj.guardian.id)
        for i in list_parent:
            data['guardian_'+str(i)] = guardian.__dict__[i]

    copy_obj = CommonRegistrationFormAfterPayment.objects.filter(
        id=reg_form_id)
    copy_obj.update(**data)
    return True


class CreateOrderView(APIView):
    permission_classes = (IsParent,)

    def get(self, request, *args, **kwargs):
        child_id = kwargs["child_id"]
        cart_items = ChildSchoolCart.objects.filter(
            child_id=child_id).select_related("school")

        total_form_fee = cart_items.aggregate(total_form_price=Sum(
            "form_price")).get("total_form_price", 0)
        total_conv_fee = cart_items.aggregate(total_conv=Sum(
            "school__convenience_fee")).get("total_conv", 0)
        total_discount_amount = cart_items.aggregate(
            total_disc_amount=Sum("discount")).get("total_disc_amount", 0)
        amount = total_form_fee + total_conv_fee - total_discount_amount

        if(cart_items.count() >= 10):
            amount -= 50
        elif(cart_items.count() >= 5):
            amount -= 25

        DATA = {
            "amount": amount*100,
            "currency": "INR",
            "receipt": "ezy_receipt_" + str(time.time()),
            "payment_capture": 1
        }

        logger.info(f"order created with Data:{DATA}")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
        data = client.order.create(data=DATA)
        FormOrder.objects.create(
            child_id=child_id, amount=amount, order_id=data["id"])
        return Response({"order_id": data["id"]})


class CaptureTransactionView(APIView):
    permission_classes = (IsParent,)
    serializer_class = CaptureTransactionSerializer

    def patch(self, request, *args, **kwargs):
        child_id = kwargs["child_id"]
        serializer = CaptureTransactionSerializer(data=request.data)
        if serializer.is_valid():
            razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
            razorpay_order_id = serializer.validated_data["razorpay_order_id"]
            form_id = serializer.validated_data["form_id"]
            razorpay_signature = serializer.validated_data["razorpay_signature"]
            order = FormOrder.objects.get(child_id=child_id, order_id=razorpay_order_id)
          #  obj=CommonRegistrationForm.objects.get(id=form_id)
          #  copy_obj = CommonRegistrationFormAfterPayment.objects.create(user_id=obj.user)
            if order.order_id == razorpay_order_id:

                client = razorpay.Client(
                    auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                res = client.payment.fetch(razorpay_payment_id)
                local_tz = pytz.timezone("Asia/Kolkata")
                utc_dt = datetime.utcfromtimestamp(
                    res["created_at"]).replace(tzinfo=pytz.utc)
                local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

                logger.info(f"Data sent from  razorpay :{res}")

                transaction = FormTransaction(payment_id=res["id"],
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
                order.payment_id = transaction
                order.signature = razorpay_signature
                order.save(update_fields=["signature", "payment_id"])

                logger.info(
                    f"Form order Data :{order.payment_id}:{order.signature}")

                if res["status"] == "captured":
                    logger.info("payment captured")
                    child_id = serializer.validated_data["child_id"]
                    child = Child.objects.get(pk=child_id)
                    obj = CommonRegistrationForm.objects.get(id=form_id)
                    copy_obj = CommonRegistrationFormAfterPayment.objects.create(
                        user=obj.user)
                    copy_the_form_data(obj.id, copy_obj.id)
                    carts_list = list(ChildSchoolCart.objects.filter(
                        child_id=child_id, timestamp__lt=order.timestamp).select_related("school"))

                    for cart in carts_list:
                        if cart.ad_source:
                            ad_source=cart.ad_source
                        else:
                            ad_source=''

                        school_obj = SchoolProfile.objects.filter(
                            id=cart.school.id).first()

                        def generate_form_id(school_value, session):
                            if school_value.id == 1697:
                                start_value_form = SchoolApplication.objects.filter(
                                    school=school_value).count()
                                base_start_value = 2001
                                current_value = base_start_value + start_value_form
                                new_id = "N" + str(current_value) + "-22"
                                return new_id
                            else:
                                cval = SchoolApplication.objects.filter(
                                    school=school_value).count() + school_value.count_start
                                session_for_id = f"{session.split('-')[0][2:]}{session.split('-')[1][2:]}"
                                new_id = f"EZY/{school_value.id}/{session_for_id}/{cval}"
                                return new_id
                        form_id_new = generate_form_id(school_obj, CommonRegistrationForm.objects.get(id=form_id).session)
                        form = SchoolAdmissionFormFee.objects.get(school_relation=school_obj, class_relation__id=child.class_applying_for.id)
                        ezyschool_commision_per = school_obj.commission_percentage
                        commision = 0
                        ezyschool_total_amount = 0
                        convenience_fee = school_obj.convenience_fee
                        result = {}
                        if cart.coupon_code:
                            if(Coupons.objects.filter(school=school_obj, school_code=cart.coupon_code)).exists():  # 10
                                coupon_obj = Coupons.objects.get(
                                    school_code=cart.coupon_code)
                                formFee_after_using_coupon = form.form_price - cart.discount
                                commision = form.form_price * school_obj.commission_percentage / 100
                                ezyschool_total_amount = school_obj.convenience_fee + commision
                                school_settlement_amount = formFee_after_using_coupon - commision
                                result['msg'] = "Coupon Applied on school form "
                                result['discount'] = cart.discount
                                result['code'] = coupon_obj.school_code
                            elif (Coupons.objects.filter(school=school_obj, ezyschool_code=cart.coupon_code)).exists():
                                coupon_obj = Coupons.objects.get(
                                    ezyschool_code=cart.coupon_code)
                                if(school_obj.convenience_fee > 0):
                                    convenienceFee_after_using_coupon = school_obj.convenience_fee - cart.discount
                                    commision = form.form_price * school_obj.commission_percentage / 100
                                    ezyschool_total_amount = convenienceFee_after_using_coupon + commision
                                    school_settlement_amount = form.form_price - commision
                                    result['msg'] = "Coupon Applied on Conveniences fee"
                                    result['discount'] = cart.discount
                                    result['code'] = coupon_obj.ezyschool_code
                                else:
                                    commision = form.form_price * school_obj.commission_percentage / 100
                                    ezyschool_total_amount = commision - cart.discount
                                    school_settlement_amount = form.form_price - commision
                                    result['msg'] = "Coupon Applied on Ezyschool Commission"
                                    result['discount'] = cart.discount
                                    result['code'] = coupon_obj.ezyschool_code
                        else:
                            school_settlement_amount = form.form_price - (form.form_price*((school_obj.commission_percentage/100) if school_obj.commission_percentage else 1))
                            result['msg'] = "No Coupon Applied"
                            result['discount'] = 0
                            result['code'] = "NA"
                        child_class = child.class_applying_for.id
                        sch_cls = [
                            school_class.id for school_class in school_obj.class_relation.filter()]
                        application = None
                        if child_class in sch_cls and SchoolMultiClassRelation.objects.filter(multi_class_relation__id__in=[child_class]).exists():
                            # multi_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id__in=[child_class]).first()
                            application = SchoolApplication.objects.create(
                                child=child, school=school_obj, form_id=form_id, registration_data=copy_obj, user=request.user,
                                apply_for=child.class_applying_for, uid=form_id_new, ezyschool_commission_percentage=ezyschool_commision_per,
                                school_settlement_amount=school_settlement_amount,ezyschool_commission=commision,
                                ezyschool_total_amount=ezyschool_total_amount, coupon_code=result['code'],
                                coupon_discount=result['discount'], coupon_applied_on=result['msg'],convenience_fee=convenience_fee,payment_id=res["id"],
                                order_id=res["order_id"],form_fee=form.form_price)
                        elif child_class in sch_cls and not SchoolMultiClassRelation.objects.filter(multi_class_relation__id__in=[child_class]).exists():
                            application = SchoolApplication.objects.create(
                                child=child, school=school_obj, form_id=form_id, registration_data=copy_obj,
                                user=request.user, apply_for=child.class_applying_for, uid=form_id_new, ezyschool_commission_percentage=ezyschool_commision_per,
                                school_settlement_amount=school_settlement_amount,ezyschool_commission=commision,
                                ezyschool_total_amount=ezyschool_total_amount, coupon_code=result['code'],
                                coupon_discount=result['discount'], coupon_applied_on=result['msg'],convenience_fee=convenience_fee,payment_id=res["id"],
                                order_id=res["order_id"],form_fee=form.form_price)
                        elif not child_class in sch_cls and SchoolMultiClassRelation.objects.filter(multi_class_relation__id__in=[child_class]).exists():
                            application = SchoolApplication.objects.create(
                                child=child, school=school_obj, form_id=form_id, registration_data=copy_obj,
                                user=request.user, apply_for=child.class_applying_for, uid=form_id_new, ezyschool_commission_percentage=ezyschool_commision_per,
                                school_settlement_amount=school_settlement_amount,ezyschool_commission=commision,
                                ezyschool_total_amount=ezyschool_total_amount, coupon_code=result['code'],
                                coupon_discount=result['discount'], coupon_applied_on=result['msg'],convenience_fee=convenience_fee,payment_id=res["id"],
                                order_id=res["order_id"],form_fee=form.form_price)

                        # application = SchoolApplication.objects.create(
                        #     child=child, school=school_obj, form_id=form_id,registration_data=copy_obj,user=request.user, apply_for=child.class_applying_for)
                        if SchoolSettlementAccounts.objects.filter(school=application.school).exists():
                            settel_account= SchoolSettlementAccounts.objects.get(school=application.school)
                            transfer_amount = int(application.school_settlement_amount * 100)
                            data={
                                "transfers": [
                                        {
                                            "account": settel_account.razorpay_account_id,
                                            "amount": transfer_amount,
                                            "currency": "INR",
                                            "notes": {
                                                "From": "Ezyschooling",
                                                "For Application UID": application.uid
                                            },
                                            "on_hold": 0,
                                        }
                                    ]
                                }
                            res = requests.post(f'https://api.razorpay.com/v1/payments/{razorpay_payment_id}/transfers',data=json.dumps(data),headers={'Content-Type': 'application/json'},auth=HTTPBasicAuth(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                            print(res.text,"-----------------------------here",type(res))
                            if res.status_code == 200:
                                res=json.loads(res.text)
                                transfer_obj = SchoolTransferDetail.objects.create(school=application.school,transfer_id =res['items'][0]['id'],recipient=res['items'][0]['recipient'],notes=res['items'][0]['notes'],amount=res['items'][0]['amount'])
                                transfer_obj.save()
                        ChildSchoolCart.objects.filter(
                            form__pk=form_id, school=school_obj).delete()

                        FormReceipt.objects.create(
                            school_applied=application, form_fee=cart.form_price, receipt_id=application.uid)

                        # setting status for the school application
                        if school_obj.collab:
                            app_status, created = ApplicationStatus.objects.get_or_create(
                                rank=1, type="C", name="Form Submitted")
                            logger.info("application created for collab")
                        else:
                            app_status, created = ApplicationStatus.objects.get_or_create(
                                rank=1, type="N", name="Application received by Ezyschooling")
                            logger.info("application created for noncollab")
                        ApplicationStatusLog.objects.create(
                            application=application, status=app_status)

                        logger.info(f"Success for cartitem: {cart}")

                    return Response({"payment": "success"}, status.HTTP_200_OK)
                logger.info("payment failed 1")
                return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
            logger.info("no razor pay id returned 2")
            return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class CreateAdmissionGuidanceProgrammeOrderView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = AdmissionGuidanceProgrammeOrderSerializer

    def post(self, request, *args, **kwargs):
        serializer = AdmissionGuidanceProgrammeOrderSerializer(
            data=request.data)
        if serializer.is_valid():
            try:
                valid_data = serializer.validated_data
                package = AdmissionGuidanceProgrammePackage.objects.get(
                    name=str(valid_data['package_name']))
                amount = package.amount
                DATA = {
                    "amount": amount*100,
                    "currency": "INR",
                    "receipt": "ezy_agp_receipt_" + str(time.time()),
                    "payment_capture": 1
                }
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                data = client.order.create(data=DATA)

                AdmissionGuidanceProgrammeFormOrder.objects.create(name=valid_data['name'], email=valid_data['email'],
                                                                   amount=amount, order_id=data["id"])
                return Response({"order_id": data["id"]})
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class CaptureAdmissionGuidanceProgrammeTransactionView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = CaptureAdmissionGuidanceProgrammeTransactionSerializer

    def patch(self, request, *args, **kwargs):
        serializer = CaptureAdmissionGuidanceProgrammeTransactionSerializer(
            data=request.data)
        if serializer.is_valid():
            razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
            razorpay_order_id = serializer.validated_data["razorpay_order_id"]
            razorpay_signature = serializer.validated_data["razorpay_signature"]
            order = AdmissionGuidanceProgrammeFormOrder.objects.get(
                order_id=razorpay_order_id)

            if order.order_id == razorpay_order_id:

                client = razorpay.Client(
                    auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                res = client.payment.fetch(razorpay_payment_id)

                local_tz = pytz.timezone("Asia/Kolkata")
                utc_dt = datetime.utcfromtimestamp(
                    res["created_at"]).replace(tzinfo=pytz.utc)
                local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

                transaction = AdmissionGuidanceProgrammeFormTransaction(payment_id=res["id"],
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
                order.payment_id = transaction
                order.signature = razorpay_signature
                order.save(update_fields=["signature", "payment_id"])

                if res["status"] == "captured":

                    return Response({"payment": "success"}, status.HTTP_200_OK)

                return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
            return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class CaptureAdmissionGuidanceTransactionView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = CaptureAdmissionGuidanceTransactionSerializer

    def patch(self, request, *args, **kwargs):
        serializer = CaptureAdmissionGuidanceTransactionSerializer(
            data=request.data)
        if serializer.is_valid():
            razorpay_payment_id = serializer.validated_data["razorpay_payment_id"]
            razorpay_order_id = serializer.validated_data["razorpay_order_id"]
            razorpay_signature = serializer.validated_data["razorpay_signature"]
            order = AdmissionGuidanceFormOrder.objects.get(
                order_id=razorpay_order_id)

            if order.order_id == razorpay_order_id:

                client = razorpay.Client(
                    auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
                res = client.payment.fetch(razorpay_payment_id)

                local_tz = pytz.timezone("Asia/Kolkata")
                utc_dt = datetime.utcfromtimestamp(
                    res["created_at"]).replace(tzinfo=pytz.utc)
                local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

                transaction = AdmissionGuidanceFormTransaction(payment_id=res["id"],
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
                order.payment_id = transaction
                order.signature = razorpay_signature
                order.save(update_fields=["signature", "payment_id"])

                if res["status"] == "captured":
                    db_transaction.on_commit(
                        lambda: add_admission_guidance_data.delay(
                            order.person.id)
                    )
                    db_transaction.on_commit(
                        lambda: send_admission_guidance_mail.delay(
                            order.person.id)
                    )
                    return Response({"payment": "success"}, status.HTTP_200_OK)

                return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
            return Response({"payment": "failure"}, status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
