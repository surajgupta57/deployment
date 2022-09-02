import os
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Sum, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from rest_framework import generics, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from admission_forms.filters import (
    ChildSchoolCartFilter,
    ChildSchoolApplicationFilter,
    CommonRegistrationFormFilter,
)
from admission_forms.models import *
from admission_forms.utils import Render, evaluate_points, bucketPdfToImage
from childs.models import Child
from parents import permissions
from parents.models import ParentProfile
from schools.api.v1.serializers import AlumniSchoolSerializer
from schools.models import (
    SchoolProfile,
    SchoolAdmissionFormFee,
    AgeCriteria,
    AdmmissionOpenClasses, SchoolMultiClassRelation,SchoolEqnuirySource,SchoolClasses
)
from . import serializers
from django.http import HttpResponse
from django.shortcuts import render


class ChildSchoolCartView(generics.ListCreateAPIView):
    serializer_class = serializers.ChildSchoolCartIDSerializer
    # filterset_class = ChildSchoolCartFilter
    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        if "child" in self.request.GET and self.request.GET.get("child"):
            queryset = ChildSchoolCart.objects.filter(
                child=self.request.GET.get("child")
            )
        else:
            queryset = ChildSchoolCart.objects.filter(
                child=self.request.user.current_child
            )
        return queryset.order_by("id")

    def get_serializer_class(self):
        include_complete_data = self.request.GET.get("include_complete_data", None)
        if include_complete_data == "yes" or self.request.method == "POST":
            return serializers.ChildSchoolCartSerializer
        else:
            return serializers.ChildSchoolCartIDSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        school = data["school"]
        child = data["child"]
        session = data["session"]
        ad_source  = self.request.GET.get("ad_value",'')
        if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
            ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
        else:
            ad_source =''
        class_relation = child.class_applying_for.id
        child_class_obj = SchoolClasses.objects.get(id=child.class_applying_for.id)
        multi_cls_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=child_class_obj.id)
        multi_class_obj = None
        if len(list(multi_cls_obj)) > 0:
            multi_class_obj = multi_cls_obj[0]
        if multi_class_obj:
            multi_class = [cls.id for cls in multi_class_obj.multi_class_relation.all()]
            fee_obj = SchoolAdmissionFormFee.objects.filter(
                school_relation=school, class_relation__id__in=multi_class
            )
            form_price = fee_obj[0].form_price
        else:
            form_price = SchoolAdmissionFormFee.objects.filter(
                school_relation=school, class_relation__id=class_relation
            ).first().form_price
        if CommonRegistrationForm.objects.filter(
            user=self.request.user, child=data["child"]
        ).exists():
            childData = CommonRegistrationForm.objects.get(
                user=self.request.user, child=data["child"]
            )
            if childData.session == session:
                pass
            else:
                childData.session = session
                childData.save()
        gettingOrCreatingCommonForm = CommonRegistrationForm.objects.get_or_create(
            user=self.request.user, child=data["child"], session=session
        )
        form = CommonRegistrationForm.objects.get(
            user=self.request.user, child=data["child"], session=session
        )
        # if multi_class_obj:
        #     multi_class = [cls.id for cls in multi_class_obj.multi_class_relation.all()]
        #     fee_obj = SchoolAdmissionFormFee.objects.filter(
        #         school_relation=school, class_relation__id__in=multi_class
        #     )
        #     form_price = fee_obj[0].form_price
        # else:
        #     form_price = SchoolAdmissionFormFee.objects.get(
        #         school_relation=school, class_relation=class_relation
        #     ).form_price
        if self.request.user.ad_source and self.request.user.ad_source != "":
            ad_source = self.request.user.ad_source
        serializer.save(form=form, form_price=form_price, user=self.request.user,ad_source=ad_source)


class ChildSchoolCartDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = serializers.ChildSchoolCartSerializer
    permission_classes = [
        permissions.IsParent,
    ]
    lookup_fields = "pk"

    def get_queryset(self):
        queryset = ChildSchoolCart.objects.all().select_related("school")
        return queryset


class ChildSchoolCartTotalAmountView(APIView):
    permission_classes = [
        permissions.IsParent,
    ]

    def get(self, request, format=False):
        try:
            if "child" in request.GET and request.GET.get("child"):
                cart_items = ChildSchoolCart.objects.filter(
                    child=request.GET["child"]
                ).select_related("school")
            else:
                cart_items = ChildSchoolCart.objects.filter(
                    child=request.user.current_child
                ).select_related("school")

            total_form_fee = cart_items.aggregate(
                total_form_price=Sum("form_price")
            ).get("total_form_price", 0)
            total_convenience_fee = cart_items.aggregate(
                total_conv_fee=Sum("school__convenience_fee")
            ).get("total_conv_fee", 0)

            total_discount_amount = cart_items.aggregate(
                total_disc_amount=Sum("discount")
            ).get("total_disc_amount", 0)
            total_amount = total_form_fee + total_convenience_fee - total_discount_amount

            response = {
                "no_of_schools": cart_items.count(),
                "form_fee": total_form_fee,
                "conv_fee": total_convenience_fee,
                "discount" :total_discount_amount,
                "total": total_amount,
            }
            return Response(response, status=status.HTTP_200_OK)
        except:
            return Response("Details not found", status=status.HTTP_200_OK)


class ChildSchoolCartRequiredFieldsView(APIView):
    permission_classes = [
        permissions.IsParent,
    ]

    def get(self, request, format=False):
        if "child" in request.GET and request.GET.get("child"):
            # print(request.GET['child'])
            queryset = ChildSchoolCart.objects.filter(
                child=request.GET["child"]
            ).values_list("school", flat=True)
        else:
            # print(request.GET['child'])
            queryset = ChildSchoolCart.objects.filter(
                child=request.user.current_child
            ).values_list("school", flat=True)
        school_ids = list(queryset)
        schools = SchoolProfile.objects.only(
            "required_admission_form_fields",
            "required_child_fields",
            "required_father_fields",
            "required_mother_fields",
            "required_guardian_fields",
        ).filter(pk__in=school_ids)
        # print(schools)
        # print(schools.__dict__)
        required_admission_form_fields = {}
        required_child_fields = {}
        required_father_fields = {}
        required_guardian_fields = {}
        required_mother_fields = {}

        for i in schools:
            required_admission_form_fields.update(i.required_admission_form_fields)
            required_child_fields.update(i.required_child_fields)
            required_father_fields.update(i.required_father_fields)
            required_guardian_fields.update(i.required_guardian_fields)
            required_mother_fields.update(i.required_mother_fields)

        response = {
            "required_admission_form_fields": required_admission_form_fields,
            "required_child_fields": required_child_fields,
            "required_father_fields": required_father_fields,
            "required_guardian_fields": required_guardian_fields,
            "required_mother_fields": required_mother_fields,
        }

        return Response(response, status=status.HTTP_200_OK)


class ChildSchoolCartRequiredFieldsStatusView(APIView):
    permission_classes = [
        permissions.IsParent,
    ]

    def get(self, request, format=False):
        if "child" in request.GET and request.GET.get("child"):
            queryset = ChildSchoolCart.objects.filter(child=request.GET["child"])
        else:
            queryset = ChildSchoolCart.objects.filter(child=request.user.current_child)

        cartlist = []
        schoolcart = {}
        count = 0
        for i in queryset:
            data = {}
            required_admission_form_fields = {}
            required_child_fields = {}
            required_father_fields = {}
            required_guardian_fields = {}
            required_mother_fields = {}
            for k in i.school.required_admission_form_fields:
                if k in i.form.__dict__:
                    if (
                        i.form.__dict__[k] == None
                        or i.form.__dict__[k] == ""
                        or i.form.__dict__[k] == "null"
                    ):
                        required_admission_form_fields[k] = i.form.__dict__[k]
                else:
                    if k in [
                        "last_school_board",
                        "last_school_class",
                        "sibling1_alumni_school_name",
                        "sibling2_alumni_school_name",
                    ]:
                        key = k + "_id"
                        if (
                            i.form.__dict__[key] == None
                            or i.form.__dict__[key] == ""
                            or i.form.__dict__[key] == "null"
                        ):
                            required_admission_form_fields[k] = i.form.__dict__[key]
                    elif k == "transport_facility":
                        key = "transport_facility_required"
                        required_admission_form_fields[k] = i.form.__dict__[key]

            for k in i.school.required_child_fields:
                if k in i.child.__dict__:
                    if (
                        i.child.__dict__[k] == None
                        or i.child.__dict__[k] == ""
                        or i.child.__dict__[k] == "null"
                    ):
                        required_child_fields[k] = i.child.__dict__[k]
                else:
                    if k == "aadhaar_number":
                        key = "aadhaar_card_number"
                        required_child_fields[k] = i.child.__dict__[key]
                    else:
                        print("kkk", k)

            if i.form.child.orphan:
                for k in i.school.required_guardian_fields:
                    if i.form.guardian:
                        if k in i.form.guardian.__dict__:
                            if (
                                i.form.guardian.__dict__[k] == None
                                or i.form.guardian.__dict__[k] == ""
                                or i.form.guardian.__dict__[k] == "null"
                            ):
                                required_guardian_fields[k] = i.form.guardian.__dict__[
                                    k
                                ]
                        else:
                            if k == "aadhaar_card_number":
                                key = "aadhaar_number"

                                required_guardian_fields[k] = i.form.guardian.__dict__[
                                    key
                                ]
                            elif k == "company_name":
                                key = "companyname"

                                required_guardian_fields[k] = i.form.guardian.__dict__[
                                    key
                                ]
                            elif k == "alumni_school_name":
                                key = "alumni_school_name_id"

                                required_guardian_fields[k] = i.form.guardian.__dict__[
                                    key
                                ]
                            else:
                                pass
            else:
                for k in i.school.required_father_fields:
                    if i.form.father:
                        if k in i.form.father.__dict__:
                            if (
                                i.form.father.__dict__[k] == None
                                or i.form.father.__dict__[k] == ""
                                or i.form.father.__dict__[k] == "null"
                            ):

                                required_father_fields[k] = i.form.father.__dict__[k]
                        else:
                            if k == "aadhaar_card_number":
                                key = "aadhaar_number"

                                required_father_fields[k] = i.form.father.__dict__[key]
                            elif k == "company_name":
                                key = "companyname"

                                required_father_fields[k] = i.form.father.__dict__[key]
                            elif k == "alumni_school_name":
                                key = "alumni_school_name_id"

                                required_father_fields[k] = i.form.father.__dict__[key]
                            else:
                                pass

                for k in i.school.required_mother_fields:
                    if i.form.mother:
                        if k in i.form.mother.__dict__:
                            if (
                                i.form.mother.__dict__[k] == None
                                or i.form.mother.__dict__[k] == ""
                                or i.form.mother.__dict__[k] == "null"
                            ):
                                required_mother_fields[k] = i.form.mother.__dict__[k]
                        else:
                            if k == "aadhaar_card_number":
                                key = "aadhaar_number"

                                required_mother_fields[k] = i.form.mother.__dict__[key]
                            elif k == "company_name":
                                key = "companyname"

                            elif k == "alumni_school_name":
                                key = "alumni_school_name_id"

                            else:
                                pass
            data["school"] = i.school.name
            try:
                required_admission_form_fields_percentage = len(
                    required_admission_form_fields
                ) / len(i.school.required_admission_form_fields)
            except ZeroDivisionError:
                required_admission_form_fields_percentage = 0
            try:
                required_child_fields_percentage = len(required_child_fields) / len(
                    i.school.required_child_fields
                )
            except ZeroDivisionError:
                required_child_fields_percentage = 0
            if i.form.child.orphan:
                try:
                    required_guardian_fields_percentage = len(
                        required_guardian_fields
                    ) / len(i.school.required_guardian_fields)
                except ZeroDivisionError:
                    required_guardian_fields_percentage = 0
            else:
                try:
                    required_father_fields_percentage = len(
                        required_father_fields
                    ) / len(i.school.required_father_fields)
                except ZeroDivisionError:
                    required_father_fields_percentage = 0
                try:
                    required_mother_fields_percentage = len(
                        required_mother_fields
                    ) / len(i.school.required_mother_fields)
                except ZeroDivisionError:
                    required_mother_fields_percentage = 0

            data["required_admission_form_fields%"] = (
                (1 - required_admission_form_fields_percentage) * 100
                if required_admission_form_fields_percentage != 0
                else 0.0
            )
            data["required_child_fields%"] = (
                (1 - required_child_fields_percentage) * 100
                if required_child_fields_percentage != 0
                else 0.0
            )
            if i.form.child.orphan:
                data["required_guardian_fields%"] = (
                    (1 - required_guardian_fields_percentage) * 100
                    if required_guardian_fields_percentage != 0
                    else 0.0
                )
            else:
                data["required_father_fields%"] = (
                    (1 - required_father_fields_percentage) * 100
                    if required_father_fields_percentage != 0
                    else 0.0
                )
                data["required_mother_fields%"] = (
                    (1 - required_mother_fields_percentage) * 100
                    if required_mother_fields_percentage != 0
                    else 0.0
                )

            schoolcart[count] = data
            count = count + 1

        return Response(schoolcart, status=status.HTTP_200_OK)


class CommonRegistrationFormView(generics.ListCreateAPIView):
    serializer_class = serializers.CommonRegistrationFormSerializer
    filterset_class = CommonRegistrationFormFilter

    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        if "child" in self.request.GET and self.request.GET["child"]:
            queryset = CommonRegistrationForm.objects.filter(
                child=self.request.GET["child"]
            ).order_by("id")
        else:
            queryset = CommonRegistrationForm.objects.filter(
                child=self.request.user.current_child
            ).order_by("id")
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommonRegistrationFormDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CommonRegistrationFormSerializer
    lookup_fields = "pk"
    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        queryset = CommonRegistrationForm.objects.all().order_by("id")
        return queryset

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class SchoolApplyView(APIView):
    serializer_class = serializers.ChildSchoolApplySerializer

    def post(self, request, *args, **kwargs):
        serializer = serializers.ChildSchoolCartSerializer(data=request.data)
        if serializer.is_valid():
            response = {}
            school_id = request.data["school"]
            school = SchoolProfile.objects.get(id=school_id)

            def generate_form_id(school_value):
                if school_value.id == 1697:
                    start_value_form = SchoolApplication.objects.filter(
                        school=school_value
                    ).count()
                    base_start_value = 2001
                    current_value = base_start_value + start_value_form
                    new_id = "N" + str(current_value) + "-22"
                    return new_id
                else:
                    cval = (
                        SchoolApplication.objects.filter(school=school_value).count()
                        + school_value.count_start
                    )
                    new_id = "ezy_" + str(school_value.short_name) + "_" + str(cval)
                    return new_id

            if school.form_price == 0:
                child_id = request.data["child"]
                child = Child.objects.get(id=child_id)
                if (
                    child.name
                    and child.date_of_birth
                    and child.photo
                    and child.gender
                    and child.class_applying_for
                    and child.religion
                    and child.nationality
                ):
                    if (
                        child.child_admission_forms.street_address
                        and child.child_admission_forms.city
                        and child.child_admission_forms.state
                        and child.child_admission_forms.pincode
                        and child.child_admission_forms.country
                    ):
                        if not child.orphan:
                            if (
                                child.child_admission_forms.father.name
                                and child.child_admission_forms.father.email
                                and child.child_admission_forms.father.phone
                            ):
                                if (
                                    child.child_admission_forms.mother.name
                                    and child.child_admission_forms.mother.email
                                    and child.child_admission_forms.mother.phone
                                ):
                                    for (
                                        key,
                                        value,
                                    ) in school.required_child_fields.items():
                                        if value:
                                            if not child.__getattribute__(key):
                                                response["direct_apply"] = False
                                    for (
                                        key,
                                        value,
                                    ) in school.required_father_fields.items():
                                        if value:
                                            if not child.child_admission_forms.father.__getattribute__(
                                                key
                                            ):
                                                response["direct_apply"] = False
                                    for (
                                        key,
                                        value,
                                    ) in school.required_mother_fields.items():
                                        if value:
                                            if not child.child_admission_forms.mother.__getattribute__(
                                                key
                                            ):
                                                response["direct_apply"] = False
                                    for (
                                        key,
                                        value,
                                    ) in school.required_admission_form_fields.items():
                                        if value:
                                            if not child.child_admission_forms.__getattribute__(
                                                key
                                            ):
                                                response["direct_apply"] = False
                                    form_id_new = generate_form_id(school)
                                    SchoolApplication.objects.create(
                                        user=request.user,
                                        child=child,
                                        school=school,
                                        form=child.child_admission_forms,
                                        apply_for_id=request.data.get("apply_for"),
                                        uid=form_id_new,
                                    )
                                    return Response(
                                        {"direct_apply": True},
                                        status=status.HTTP_200_OK,
                                    )

                                else:
                                    response["direct_apply"] = False

                        elif child.orphan:
                            if (
                                child.child_admission_forms.guardian.name
                                and child.child_admission_forms.guardian.email
                                and child.child_admission_forms.guardian.phone
                            ):
                                for (
                                    key,
                                    value,
                                ) in school.required_guardian_fields.items():
                                    if value:
                                        if not child.child_admission_forms.guardian.__getattribute__(
                                            key
                                        ):
                                            response["direct_apply"] = False

                                form_id_new = generate_form_id(school)
                                SchoolApplication.objects.create(
                                    user=request.user,
                                    child=child,
                                    school=school,
                                    form=child.child_admission_forms,
                                    apply_for=request.data.get("apply_for"),
                                    uid=form_id_new,
                                )
                                return Response(
                                    {"direct_apply": True}, status=status.HTTP_200_OK
                                )

                            else:
                                response["direct_apply"] = False
                        else:
                            response["direct_apply"] = False
                    else:
                        response["direct_apply"] = False
                else:
                    response["direct_apply"] = False
            else:
                response["direct_apply"] = False
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChildSchoolApplicationIView(generics.ListAPIView):
    serializer_class = serializers.ChildSchoolApplicationIDSerializer
    filterset_class = ChildSchoolApplicationFilter

    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        try:
            queryset = SchoolApplication.objects.filter(
                user=self.request.user, child=self.request.GET["child"]
            ).values("school_id")
        except:
            queryset = SchoolApplication.objects.filter(
                child=self.request.user.current_child
            ).values("school_id")
        return queryset


class SchoolApplicationFormPDFDetailView(generics.ListAPIView):
    """
    this function uses browser to generate pdf.
    """

    def get(self, request, **kwargs):
        app = generics.get_object_or_404(SchoolApplication, id=self.kwargs["app_id"])
        ser = serializers.SchoolApplicationNewPDFSerializer(app)
        for cls in app.school.class_relation.filter():
            if SchoolMultiClassRelation.objects.filter(multi_class_relation__in=[cls]).exists():
                multi_obj = SchoolMultiClassRelation.objects.get(multi_class_relation__in=[cls])
                if app.apply_for in multi_obj.multi_class_relation.filter():
                    app.apply_for = cls
                    break
        app = bucketPdfToImage(app)
        resp = Render.render(
            "admission_forms/new_form_pdf_copy.html",
            {"app": ser.data, "child": app.child, "app1": app, "child_class": app.child.class_applying_for.name},
        )
        png_list = [
            f for f in os.listdir(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}/') if f.endswith(".png")
        ]
        pdf_list = [
            f for f in os.listdir(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}/') if f.endswith(".pdf")
        ]
        for f in png_list:
            os.remove(os.path.join(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}/', f))
        for f in pdf_list:
            os.remove(os.path.join(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}/', f))
        return resp


class AlumniSchoolPagination(LimitOffsetPagination):
    default_limit = 50


class AlumniSchoolListView(generics.ListAPIView):
    serializer_class = AlumniSchoolSerializer
    pagination_class = AlumniSchoolPagination
    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        cart_items = ChildSchoolCart.objects.filter(
            child=self.request.user.current_child
        ).values_list("school__pk", flat=True)
        if "child" in self.request.GET and self.request.GET["child"]:
            cart_items = ChildSchoolCart.objects.filter(
                child=self.request.GET["child"]
            ).values_list("school__pk", flat=True)
        queryset = SchoolProfile.objects.filter(id__in=cart_items)
        return queryset


class SchoolReceiptPDFView(View):
    def get(self, request, **kwargs):
        app = generics.get_object_or_404(
            FormReceipt, school_applied__id=kwargs["app_id"]
        )
        if app.school_applied.coupon_applied_on == "Coupon Applied on school form ":
            form_fee = app.form_fee  - app.school_applied.coupon_discount
        else:
            form_fee = app.form_fee

        for cls in app.school_applied.school.class_relation.filter():
            if SchoolMultiClassRelation.objects.filter(multi_class_relation__in=[cls]).exists():
                multi_obj = SchoolMultiClassRelation.objects.get(multi_class_relation__in=[cls])
                if app.school_applied.apply_for in multi_obj.multi_class_relation.filter():
                    app.school_applied.apply_for = cls
                    break
        return Render.render("admission_forms/receipt_pdf.html", {"app": app,"form_fee":form_fee, "child_class": app.school_applied.form.child.class_applying_for.name})


class ChildPointsPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.ChildPointsPreferenceSerializer
    permission_classes = [
        permissions.IsParent,
    ]

    def get_queryset(self):
        return ChildPointsPreference.objects.filter(child=self.request.user)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        pref_object, _ = ChildPointsPreference.objects.get_or_create(
            child=self.request.user
        )
        return pref_object


class ChildPointsEvaluateView(APIView):
    permission_classes = [
        permissions.IsParent,
    ]

    def get(self, request, **kwargs):
        slug = self.kwargs.get("slug", None)
        school = generics.get_object_or_404(SchoolProfile, slug=slug)
        pref = generics.get_object_or_404(
            ChildPointsPreference, child=self.request.user
        )
        points = evaluate_points(pref, school)

        ChildPointsPreferenceSchoolWise.objects.create(
            pref_id=pref.id,
            school_id=school.id,
            total_points=points["total_points"],
            children_of_armed_force_points=points["children_of_armed_force_points"],
            single_child_points=points["single_child_points"],
            siblings_points=points["siblings_points"],
            parent_alumni_points=points["parent_alumni_points"],
            staff_ward_points=points["staff_ward_points"],
            first_born_child_points=points["first_born_child_points"],
            first_girl_child_points=points["first_girl_child_points"],
            single_girl_child_points=points["single_girl_child_points"],
            is_christian_points=points["is_christian_points"],
            girl_child_points=points["girl_child_points"],
            minority_points=points["minority_points"],
            student_with_special_needs_points=points[
                "student_with_special_needs_points"
            ],
            transport_facility_points=points["transport_facility_points"],
            distance_points=points["distance_points"],
        )

        return Response(points, status=status.HTTP_200_OK)


def satisfies_age_criteria_admission_open_status(school, child, session):
    class_relation = child.class_applying_for.id
    multi_class_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=class_relation).first()
    if multi_class_obj:
        multi_class = [cls.id for cls in multi_class_obj.multi_class_relation.filter()]
        age_criterias = AgeCriteria.objects.filter(
            school=school, class_relation__id__in=multi_class, session=session
        )
    else:
        age_criterias = AgeCriteria.objects.filter(
            school=school, class_relation=class_relation, session=session
        )
    date_of_birth = child.date_of_birth
    for age_criterion in age_criterias:
        if (
            age_criterion.start_date > date_of_birth
            or age_criterion.end_date < date_of_birth
        ):
            return False
    return True


class CartUpdateView(APIView):
    permission_classes = [
        permissions.IsParent,
    ]

    def get(self, request, format=False):
        if "child" in request.GET and request.GET.get("child"):
            cart_items = ChildSchoolCart.objects.filter(
                child=request.GET["child"]
            ).select_related("school")
        else:
            cart_items = ChildSchoolCart.objects.filter(
                child=request.user.current_child
            ).select_related("school")

        schools = []
        for cart in cart_items:
            multi_class_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=cart.child.class_applying_for.id).first()
            if multi_class_obj:
                multi_class = [cls.id for cls in multi_class_obj.multi_class_relation.filter()]
                if not satisfies_age_criteria_admission_open_status(
                        cart.school, cart.child, cart.session
                ):
                    schools.append(cart.school.name)
                    cart.delete()
                if not AdmmissionOpenClasses.objects.filter(
                        class_relation__id__in=multi_class, school=cart.school
                ).exists():
                    schools.append(cart.school.name)
                    cart.delete()
            else:
                if not satisfies_age_criteria_admission_open_status(
                        cart.school, cart.child, cart.session
                ):
                    schools.append(cart.school.name)
                    cart.delete()
                elif not AdmmissionOpenClasses.objects.filter(
                        class_relation=cart.child.class_applying_for, school=cart.school
                ).exists():
                    schools.append(cart.school.name)
                    cart.delete()

        return Response(schools, status=status.HTTP_200_OK)
