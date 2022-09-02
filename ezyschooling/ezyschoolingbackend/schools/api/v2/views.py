from schools.filters import DistrictRegionFilter, CityFilter, DistrictFilter
from rest_framework import generics, permissions, status
from django.db import transaction
from schools.models import DistrictRegion, City, SchoolClasses, AdmmissionOpenClasses, SchoolProfile, SchoolAdmissionFormFee, AgeCriteria, SchoolMultiClassRelation, District, SchoolEnquiry, SchoolEqnuirySource
from datetime import datetime, date
from childs.models import Child
from admission_forms.models import SchoolApplication, ChildSchoolCart
from rest_framework.views import APIView
from rest_framework.response import Response
from . import serializers
from django.db.models import Q
from schools.permissions import IsSchoolOrReadOnly
from schools.utils import send_verification_code , check_verification_code
class DistrictRegionViewModified(generics.ListAPIView):
    serializer_class = serializers.DistrictRegionSerializerModified
    queryset = DistrictRegion.objects.all().filter(params__Count__gt=0).order_by('-params__official_count')
    filterset_class = DistrictRegionFilter


class CityView(generics.ListAPIView):
    serializer_class = serializers.CitySerializer
    filterset_class = CityFilter

    def get_queryset(self):
        is_featured =self.request.GET.get("is_featured",None)
        if is_featured:
            return City.objects.all().filter(params__Count__gt=0,is_featured=is_featured).order_by('-params__Count')
        return City.objects.all().filter(params__Count__gt=0).order_by('-params__Count')

class SchoolClassesView(generics.ListAPIView):
    serializer_class = serializers.SchoolClassesSerializer
    queryset = SchoolClasses.objects.all().order_by("rank")


class SchoolBrowseSearchView(APIView):
    def get(self, request):
        school_name = self.request.GET.get('school_name',None)
        city = self.request.GET.get('city',None)
        result_data = []
        if school_name and city:
            query = Q()
            query = query | Q(name__icontains=school_name)
            school_list = SchoolProfile.objects.filter(school_city__slug=city).filter(query)
        elif school_name:
            query = Q()
            query = query | Q(name__icontains=school_name)
            school_list = SchoolProfile.objects.filter(query)
        else:
            school_list = SchoolProfile.objects.none()
        for school in school_list:
            result_data.append({
            'name' : school.name + ', ' + school.district_region.name,
            'slug' : school.slug,
            })
        result={}
        result['results'] = result_data
        return Response(result, status=status.HTTP_200_OK)

class AdmmissionOpenClassesDetailView(APIView):

    def get(self, request, slug):
        session = self.request.query_params.get('session',None)
        child_id = self.request.query_params.get('child_id')
        class_id = self.request.query_params.get('class_id')
        if not child_id == '':
            child_id = int(child_id)
        else:
            child_id = None
        school = SchoolProfile.objects.get(slug=slug)
        if school.class_relation.filter(id=class_id).exists():
            class_obj = school.class_relation.get(id=class_id)
        else:
            if SchoolClasses.objects.filter(id=class_id).exists():
                class_obj = SchoolClasses.objects.get(id=class_id)
                multi_cls_obj = [multi_cls_obj.multi_class_relation.filter() for multi_cls_obj in SchoolMultiClassRelation.objects.filter(multi_class_relation__id=class_obj.id)]
                cls_obj = []
                if multi_cls_obj:
                    for cls in multi_cls_obj[0]:
                        if school.class_relation.filter(id=cls.id).exists():
                            cls_obj.append(cls)
                if len(cls_obj) > 0:
                    class_obj = cls_obj[0]
            else:
                data =[]
                if self.request.user.is_authenticated:
                    # for class_obj in all_class:
                    data.append({
                        'class_name' :"",
                        'class_id' :"class_obj.id",
                        'status' : "Close",
                        'form_fee' : 'NA',
                        'button_name' : 'Notify Me',
                        'action_name': 'showLoginModal()'
                    })
                else:
                    # for class_obj in all_class:
                    data.append({
                        'class_name' :"",
                        'class_id' :"",
                        'status' : "Close",
                        'form_fee' : 'NA',
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                })

                result = {}
                result['results'] = data
                return Response(result, status=status.HTTP_200_OK)
        data = []
        if self.request.user.is_authenticated:
            if child_id is not None:
                child_profile = Child.objects.get(id=child_id)
                # for class_obj in all_class:
                if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                    admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                    if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                        form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                        form_fee_obj = form_fee_obj1.form_price
                    else:
                        form_fee_obj = 'NA'
                    if child_profile.class_applying_for == class_obj:
                        if AgeCriteria.objects.filter(school=school,class_relation=class_obj,session=session).exists():
                            if admissionClassObject.admission_open == "CLOSE":
                                data.append({
                                    'class_name' :class_obj.name,
                                    'class_id' :class_obj.id,
                                    'status' : admissionClassObject.admission_open.capitalize(),
                                    'form_fee' : form_fee_obj,
                                    'button_name' : 'Notify Me',
                                    'action_name': 'showLoginModal()'
                                })

                            else:
                                class_age_citeria = AgeCriteria.objects.get(school=school,class_relation=class_obj,session=session)

                                if child_profile.date_of_birth <= class_age_citeria.end_date and class_age_citeria.start_date <= child_profile.date_of_birth:
                                    if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                        data.append({
                                            'class_name' :class_obj.name,
                                            'class_id' :class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Form Submitted',
                                            'action_name': 'showLoginModal()'
                                        })
                                    else:
                                        if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                            data.append({
                                                'class_name' :class_obj.name,
                                                'class_id' :class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'View Cart',
                                                'action_name': 'showLoginModal()'
                                            })
                                        else:
                                            data.append({
                                                'class_name' :class_obj.name,
                                                'class_id' :class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'Add to Cart',
                                                'action_name': 'showLoginModal()'
                                            })
                                else:
                                    data.append({
                                        'class_name' :class_obj.name,
                                        'class_id' :class_obj.id,
                                        'status' : admissionClassObject.admission_open.capitalize(),
                                        'form_fee' : form_fee_obj,
                                        'button_name' : 'Age Mismatch',
                                        'action_name': 'showLoginModal()'
                                    })
                        else:
                            if admissionClassObject.admission_open == "CLOSE":
                                data.append({
                                    'class_name' :class_obj.name,
                                    'class_id' :class_obj.id,
                                    'status' : admissionClassObject.admission_open.capitalize(),
                                    'form_fee' : form_fee_obj,
                                    'button_name' : 'Notify Me',
                                    'action_name': 'showLoginModal()'
                                })
                            else:
                                if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                    data.append({
                                        'class_name' :class_obj.name,
                                        'class_id' :class_obj.id,
                                        'status' : admissionClassObject.admission_open.capitalize(),
                                        'form_fee' : form_fee_obj,
                                        'button_name' : 'Form Submitted',
                                        'action_name': 'showLoginModal()'
                                    })
                                else:
                                    if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                        data.append({
                                            'class_name' :class_obj.name,
                                            'class_id' :class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'View Cart',
                                            'action_name': 'showLoginModal()'
                                        })
                                    else:
                                        data.append({
                                            'class_name' :class_obj.name,
                                            'class_id' :class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Add to Cart',
                                            'action_name': 'showLoginModal()'
                                        })
                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : admissionClassObject.admission_open.capitalize(),
                            'form_fee' : form_fee_obj,
                            'button_name' : 'Different Child?',
                            'action_name': 'showLoginModal()'
                        })

                else:
                    data.append({
                        'class_name' :class_obj.name,
                        'class_id' :class_obj.id,
                        'status' : "Close",
                        'form_fee' : "NA",
                        'button_name' : 'Notify Me',
                        'action_name': 'showLoginModal()'
                    })
            else:
                if Child.objects.filter(user=self.request.user).exists():
                    # for class_obj in all_class:
                    if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                        admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                        if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                            form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                            form_fee_obj =form_fee_obj1.form_price
                        else:
                            form_fee_obj = 'NA'
                        if admissionClassObject.admission_open.capitalize()=="Open":
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : form_fee_obj,
                                'button_name' : 'Select child',
                                'action_name': 'showLoginModal()'
                            })
                        else:
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : "NA",
                                'button_name' : 'Select child',
                                'action_name': 'showLoginModal()'
                            })

                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : "Close",
                            'form_fee' : "NA",
                            'button_name' : 'Select child',
                            'action_name': 'showLoginModal()'
                        })
                else:
                    # for class_obj in all_class:
                    if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                        admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                        if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                            form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                            form_fee_obj =form_fee_obj1.form_price
                        else:
                            form_fee_obj = 'NA'
                        if admissionClassObject.admission_open.capitalize() == "Open":
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : form_fee_obj,
                                'button_name' : 'Create Child',
                                'action_name': 'showLoginModal()'
                            })
                        else:
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : "NA",
                                'button_name' : 'Create Child',
                                'action_name': 'showLoginModal()'
                            })

                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : "Close",
                            'form_fee' : "NA",
                            'button_name' : 'Create Child',
                            'action_name': 'showLoginModal()'
                        })
        else:
            # for class_obj in all_class:
            if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                    form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                    form_fee_obj =form_fee_obj1.form_price
                else:
                    form_fee_obj = 'NA'
                if admissionClassObject.admission_open.capitalize() == "Open":
                    data.append({
                        'class_name' :class_obj.name,
                        'class_id' :class_obj.id,
                        'status' : admissionClassObject.admission_open.capitalize(),
                        'form_fee' : form_fee_obj,
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                    })
                else:
                    data.append({
                        'class_name' :class_obj.name,
                        'class_id' :class_obj.id,
                        'status' : admissionClassObject.admission_open.capitalize(),
                        'form_fee' : "NA",
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                    })

            else:
                data.append({
                    'class_name' :class_obj.name,
                    'class_id' :class_obj.id,
                    'status' : "Close",
                    'form_fee' : "NA",
                    'button_name' : 'Apply Now',
                    'action_name': 'showLoginModal()'
                })

        result = {}
        result['results'] = data
        return Response(result, status=status.HTTP_200_OK)


# class SchoolProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = serializers.SchoolProfileSerializer
#     lookup_field = "slug"
#     queryset = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
#     return queryset
class SchoolProfileView(APIView):

    def get(self, request, slug):
        queryset = SchoolProfile.objects.get(slug=self.kwargs.get("slug"))
        serializer = serializers.SchoolProfileSerializer(queryset,context={'request': request})
        return Response(serializer.data)


class SchoolAdmmissionOpenClassesDetailView(APIView):

    def get(self, request, slug):
        session = self.request.query_params.get('session',None)
        child_id = self.request.query_params.get('child_id')
        class_id = self.request.query_params.get('class_id', None)
        school = SchoolProfile.objects.get(slug=slug)
        if child_id == '':
            child_id = None
        else:
            child_id = int(child_id)
            child_class= Child.objects.get(id=child_id).class_applying_for
        classFromMultiClass = False
        if not class_id == '0':
            if school.class_relation.filter(id=class_id).exists():
                class_obj = school.class_relation.get(id=class_id)
            else:
                if SchoolClasses.objects.filter(id=class_id).exists():
                    class_obj = SchoolClasses.objects.get(id=class_id)
                    multi_cls_obj = SchoolMultiClassRelation.objects.filter(multi_class_relation__id=class_obj.id)
                    if len(multi_cls_obj) > 0:
                        classFromMultiClass = True
                    else:
                        data = []
                        data.append({
                            'class_name' :"",
                            'class_id' :"",
                            'status' : "-",
                            'form_fee' : '-',
                            'button_name' : 'Different Child?',
                            'action_name': 'showLoginModal()'
                            })
                        result = {}
                        result['results'] = data
                        return Response(result, status=status.HTTP_200_OK)
                else:
                    data = []
                    data.append({
                        'class_name' :"",
                        'class_id' :"",
                        'status' : "--",
                        'form_fee' : '--',
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                        })
                    result = {}
                    result['results'] = data
                    return Response(result, status=status.HTTP_200_OK)
        else:
            data = []
            data.append({
                'class_name' :"",
                'class_id' :"",
                'status' : "--",
                'form_fee' : '--',
                'button_name' : 'Select Grade',
                'action_name': 'showLoginModal()'
                })
            result = {}
            result['results'] = data
            return Response(result, status=status.HTTP_200_OK)

        data = []
        if self.request.user.is_authenticated:
            if child_id is not None:
                if not classFromMultiClass:
                    child_profile = Child.objects.get(id=child_id)
                    # for class_obj in all_class:
                    if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                        admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                        if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                            form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                            form_fee_obj = form_fee_obj1.form_price
                        else:
                            form_fee_obj = 'NA'
                        if child_profile.class_applying_for == class_obj:
                            if AgeCriteria.objects.filter(school=school,class_relation=class_obj,session=session).exists():
                                if admissionClassObject.admission_open == "CLOSE":
                                    data.append({
                                        'class_name' :class_obj.name,
                                        'class_id' :class_obj.id,
                                        'status' : admissionClassObject.admission_open.capitalize(),
                                        'form_fee' : form_fee_obj,
                                        'button_name' : 'Notify Me',
                                        'action_name': 'showLoginModal()'
                                    })

                                else:
                                    class_age_citeria = AgeCriteria.objects.get(school=school,class_relation=class_obj,session=session)

                                    if child_profile.date_of_birth <= class_age_citeria.end_date and class_age_citeria.start_date <= child_profile.date_of_birth:
                                        if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                            data.append({
                                                'class_name' :class_obj.name,
                                                'class_id' :class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'Form Submitted',
                                                'action_name': 'showLoginModal()'
                                            })
                                        else:
                                            if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                                data.append({
                                                    'class_name' :class_obj.name,
                                                    'class_id' :class_obj.id,
                                                    'status' : admissionClassObject.admission_open.capitalize(),
                                                    'form_fee' : form_fee_obj,
                                                    'button_name' : 'View Cart',
                                                    'action_name': 'showLoginModal()'
                                                })
                                            else:
                                                data.append({
                                                    'class_name' :class_obj.name,
                                                    'class_id' :class_obj.id,
                                                    'status' : admissionClassObject.admission_open.capitalize(),
                                                    'form_fee' : form_fee_obj,
                                                    'button_name' : 'Add to Cart',
                                                    'action_name': 'showLoginModal()'
                                                })
                                    else:
                                        data.append({
                                            'class_name' :class_obj.name,
                                            'class_id' :class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Age Mismatch',
                                            'action_name': 'showLoginModal()'
                                        })
                            else:
                                if admissionClassObject.admission_open == "CLOSE":
                                    data.append({
                                        'class_name' :class_obj.name,
                                        'class_id' :class_obj.id,
                                        'status' : admissionClassObject.admission_open.capitalize(),
                                        'form_fee' : form_fee_obj,
                                        'button_name' : 'Notify Me',
                                        'action_name': 'showLoginModal()'
                                    })
                                else:
                                    if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                        data.append({
                                            'class_name' :class_obj.name,
                                            'class_id' :class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Form Submitted',
                                            'action_name': 'showLoginModal()'
                                        })
                                    else:
                                        if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                            data.append({
                                                'class_name' :class_obj.name,
                                                'class_id' :class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'View Cart',
                                                'action_name': 'showLoginModal()'
                                            })
                                        else:
                                            data.append({
                                                'class_name' :class_obj.name,
                                                'class_id' :class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'Add to Cart',
                                                'action_name': 'showLoginModal()'
                                            })
                        else:
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : form_fee_obj,
                                'button_name' : 'Different Child?',
                                'action_name': 'showLoginModal()'
                            })

                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : "Close",
                            'form_fee' : "NA",
                            'button_name' : 'Notify Me',
                            'action_name': 'showLoginModal()'
                        })
                elif classFromMultiClass:
                    child_profile = Child.objects.get(id=child_id)
                    class_result_found = False
                    for val in multi_cls_obj[0].multi_class_relation.all():
                        local_class_obj = val
                        if AdmmissionOpenClasses.objects.filter(school=school,class_relation=local_class_obj, session=session).exists():
                            class_result_found = True
                            admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=local_class_obj, session=session)
                            if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=local_class_obj).exists():
                                form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=local_class_obj).first()
                                form_fee_obj = form_fee_obj1.form_price
                            else:
                                form_fee_obj = 'NA'
                            if SchoolMultiClassRelation.objects.filter(multi_class_relation__id=local_class_obj.id)[0] == SchoolMultiClassRelation.objects.filter(multi_class_relation__id=child_class.id)[0]:
                                if AgeCriteria.objects.filter(school=school,class_relation=local_class_obj,session=session).exists():
                                    if admissionClassObject.admission_open == "CLOSE":
                                        data.append({
                                            'class_name' :local_class_obj.name,
                                            'class_id' :local_class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Notify Me',
                                            'action_name': 'showLoginModal()'
                                        })
                                        break
                                    else:
                                        class_age_citeria = AgeCriteria.objects.get(school=school,class_relation=local_class_obj,session=session)

                                        if child_profile.date_of_birth <= class_age_citeria.end_date and class_age_citeria.start_date <= child_profile.date_of_birth:
                                            if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                                data.append({
                                                    'class_name' :local_class_obj.name,
                                                    'class_id' :local_class_obj.id,
                                                    'status' : admissionClassObject.admission_open.capitalize(),
                                                    'form_fee' : form_fee_obj,
                                                    'button_name' : 'Form Submitted',
                                                    'action_name': 'showLoginModal()'
                                                })
                                                break
                                            else:
                                                if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                                    data.append({
                                                        'class_name' :local_class_obj.name,
                                                        'class_id' :local_class_obj.id,
                                                        'status' : admissionClassObject.admission_open.capitalize(),
                                                        'form_fee' : form_fee_obj,
                                                        'button_name' : 'View Cart',
                                                        'action_name': 'showLoginModal()'
                                                    })
                                                    break
                                                else:
                                                    data.append({
                                                        'class_name' :local_class_obj.name,
                                                        'class_id' :local_class_obj.id,
                                                        'status' : admissionClassObject.admission_open.capitalize(),
                                                        'form_fee' : form_fee_obj,
                                                        'button_name' : 'Add to Cart',
                                                        'action_name': 'showLoginModal()'
                                                    })
                                                    break
                                        else:
                                            data.append({
                                                'class_name' :local_class_obj.name,
                                                'class_id' :local_class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'Age Mismatch',
                                                'action_name': 'showLoginModal()'
                                            })
                                            break
                                else:
                                    if admissionClassObject.admission_open == "CLOSE":
                                        data.append({
                                            'class_name' :local_class_obj.name,
                                            'class_id' :local_class_obj.id,
                                            'status' : admissionClassObject.admission_open.capitalize(),
                                            'form_fee' : form_fee_obj,
                                            'button_name' : 'Notify Me',
                                            'action_name': 'showLoginModal()'
                                        })
                                        break
                                    else:
                                        if SchoolApplication.objects.filter(school=school,child=child_profile).exists():
                                            data.append({
                                                'class_name' :local_class_obj.name,
                                                'class_id' :local_class_obj.id,
                                                'status' : admissionClassObject.admission_open.capitalize(),
                                                'form_fee' : form_fee_obj,
                                                'button_name' : 'Form Submitted',
                                                'action_name': 'showLoginModal()'
                                            })
                                            break
                                        else:
                                            if ChildSchoolCart.objects.filter(school=school,child=child_profile).exists():
                                                data.append({
                                                    'class_name' :class_obj.name,
                                                    'class_id' :class_obj.id,
                                                    'status' : admissionClassObject.admission_open.capitalize(),
                                                    'form_fee' : form_fee_obj,
                                                    'button_name' : 'View Cart',
                                                    'action_name': 'showLoginModal()'
                                                })
                                                break
                                            else:
                                                data.append({
                                                    'class_name' :class_obj.name,
                                                    'class_id' :class_obj.id,
                                                    'status' : admissionClassObject.admission_open.capitalize(),
                                                    'form_fee' : form_fee_obj,
                                                    'button_name' : 'Add to Cart',
                                                    'action_name': 'showLoginModal()'
                                                })
                                                break
                            else:
                                pass
                                # data.append({
                                #     'class_name' :local_class_obj.name,
                                #     'class_id' :local_class_obj.id,
                                #     'status' : admissionClassObject.admission_open.capitalize(),
                                #     'form_fee' : form_fee_obj,
                                #     'button_name' : 'Different Child?',
                                #     'action_name': 'showLoginModal()'
                                # })
                    if not class_result_found:
                        data.append({
                            'class_name' :"",
                            'class_id' :"",
                            'status' : "-",
                            'form_fee' : "-",
                            'button_name' : 'Different Child?',
                            'action_name': 'showLoginModal()'
                        })
            else:
                if Child.objects.filter(user=self.request.user).exists():
                    # for class_obj in all_class:
                    if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                        admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                        if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                            form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                            form_fee_obj =form_fee_obj1.form_price
                        else:
                            form_fee_obj = 'NA'
                        if admissionClassObject.admission_open.capitalize()=="Open":
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : form_fee_obj,
                                'button_name' : 'Select child',
                                'action_name': 'showLoginModal()'
                            })
                        else:
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : "NA",
                                'button_name' : 'Select child',
                                'action_name': 'showLoginModal()'
                            })

                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : "Close",
                            'form_fee' : "NA",
                            'button_name' : 'Select child',
                            'action_name': 'showLoginModal()'
                        })
                else:
                    # for class_obj in all_class:
                    if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                        admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                        if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                            form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                            form_fee_obj =form_fee_obj1.form_price
                        else:
                            form_fee_obj = 'NA'
                        if admissionClassObject.admission_open.capitalize() == "Open":
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : form_fee_obj,
                                'button_name' : 'Create Child',
                                'action_name': 'showLoginModal()'
                            })
                        else:
                            data.append({
                                'class_name' :class_obj.name,
                                'class_id' :class_obj.id,
                                'status' : admissionClassObject.admission_open.capitalize(),
                                'form_fee' : "NA",
                                'button_name' : 'Create Child',
                                'action_name': 'showLoginModal()'
                            })

                    else:
                        data.append({
                            'class_name' :class_obj.name,
                            'class_id' :class_obj.id,
                            'status' : "Close",
                            'form_fee' : "NA",
                            'button_name' : 'Create Child',
                            'action_name': 'showLoginModal()'
                        })
        else:
            # for class_obj in all_class:
            if AdmmissionOpenClasses.objects.filter(school=school,class_relation=class_obj, session=session).exists():
                admissionClassObject = AdmmissionOpenClasses.objects.get(school=school,class_relation=class_obj, session=session)
                if SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).exists():
                    form_fee_obj1 = SchoolAdmissionFormFee.objects.filter(school_relation=school,class_relation=class_obj).first()
                    form_fee_obj =form_fee_obj1.form_price
                else:
                    form_fee_obj = 'NA'
                if admissionClassObject.admission_open.capitalize() == "Open":
                    data.append({
                        'class_name' :class_obj.name,
                        'class_id' :class_obj.id,
                        'status' : admissionClassObject.admission_open.capitalize(),
                        'form_fee' : form_fee_obj,
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                    })
                else:
                    data.append({
                        'class_name' :class_obj.name,
                        'class_id' :class_obj.id,
                        'status' : admissionClassObject.admission_open.capitalize(),
                        'form_fee' : "NA",
                        'button_name' : 'Apply Now',
                        'action_name': 'showLoginModal()'
                    })

            else:
                data.append({
                    'class_name' :class_obj.name,
                    'class_id' :class_obj.id,
                    'status' : "Close",
                    'form_fee' : "NA",
                    'button_name' : 'Apply Now',
                    'action_name': 'showLoginModal()'
                })

        result = {}
        result['results'] = data
        return Response(result, status=status.HTTP_200_OK)


class FetchMultiSchoolClassesView(APIView):
    # permission_classes = [permissions.AllowAny]

    def get(self, request):
        multi_obj=[multi_obj.id for obj in SchoolMultiClassRelation.objects.filter() for multi_obj in obj.multi_class_relation.filter()]
        return Response(multi_obj, status=status.HTTP_200_OK)


class FetchAllMultiSchoolClassesView(APIView):
    def get(self, request):
        return Response([[obj.name for obj in cls.multi_class_relation.filter() if not obj.name.startswith('Nursery')] for cls in SchoolMultiClassRelation.objects.filter()], status=status.HTTP_200_OK)

class DistrictView(generics.ListAPIView):
    serializer_class = serializers.DistrictSerializerWithoutStateCountry
    filterset_class = DistrictFilter

    def get_queryset(self):
        is_featured =self.request.GET.get("is_featured",None)
        if is_featured:
            return District.objects.all().filter(params__Count__gt=0,is_featured=is_featured).order_by('-params__Count')
        return District.objects.all().filter(params__Count__gt=0).order_by('-params__Count')

class SchoolEnquiryView(APIView):

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug", None)
        if request.data:
            source = self.request.GET.get("source",'General').lower()
            from_value = self.request.GET.get("from_value",'button').lower()
            ad_source  = self.request.GET.get("ad_value",'')
            if ad_source != 'undefined' and SchoolEqnuirySource.objects.filter(related_id=ad_source).exists():
                ad_source = SchoolEqnuirySource.objects.get(related_id=ad_source).source_name.title()
            else:
                ad_source =''
            school = generics.get_object_or_404(SchoolProfile, slug=slug)
            class_relation = SchoolClasses.objects.get(id=request.data["class_relation"])
            if self.request.user.is_authenticated:
                if self.request.user.ad_source and self.request.user.ad_source != "":
                    ad_source = self.request.user.ad_source
                instance = SchoolEnquiry.objects.create(user=self.request.user, school=school,source=source, ad_source=ad_source,class_relation=class_relation,email=request.data['email'], parent_name=request.data['parent_name'],phone_no=request.data['phone_no'],second_number=request.data['phone_no'],query=request.data['query'])
            else:
                instance = SchoolEnquiry.objects.create(school=school,source=source,ad_source=ad_source,class_relation=class_relation,email=request.data['email'], parent_name=request.data['parent_name'],phone_no=request.data['phone_no'],second_number=request.data['phone_no'],query=request.data['query'])
            if from_value and from_value == "tick":
                transaction.on_commit(lambda: send_verification_code(instance.id))
                instance.interested_for_visit_but_no_data_provided = True
                instance.save()
            return Response({"id":instance.id}, status=status.HTTP_200_OK)
        return Response("Request didn't have any data", status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug", None)
        if request.data and self.request.GET.get("id",None):
            id = self.request.GET.get("id",None)
            instance = SchoolEnquiry.objects.get(school__slug=slug,id=id)
            result = False
            try:
                instance.second_number = request.data['second_number']
                instance.save()
                send_verification_code(instance.id)
                result = {"result":"OTP Sent Successfully", "status":True}
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                pass
            try:
                if request.data['resend_otp'] == True or request.data['resend_otp'] == "true":
                    send_verification_code(instance.id)
                    result = {"result":"OTP Sent Successfully", "status":True}
                    return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                pass
            try:
                if request.data["otp"]:
                    result = check_verification_code(instance.id, request.data["otp"])
                    if result:
                        instance.second_number_verified = True
                        instance.save()
                        result = {"result":"OTP Verified Successfully", "status":True}
                        return Response(result, status=status.HTTP_200_OK)
                    else:
                        result = {"result":"OTP is not Valid or Expired", "status":False}
                        return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                pass
            try:
                instance.child_name = request.data['child_name']
                date_ = datetime.strptime(request.data['tentative_date_of_visit'],'%Y-%m-%d')
                instance.tentative_date_of_visit = datetime.strptime(request.data['tentative_date_of_visit'],'%Y-%m-%d')
                if instance.second_number_verified:
                    instance.interested_for_visit_but_no_data_provided = False
                    instance.interested_for_visit = True
                    instance.save()
                    result = {"result":"Visit Scheduled Successfully", "status":True}
                else:
                    result = {"result":"Mobile Number Not Verified", "status":False}
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                pass
        return Response("Request didn't have any data", status=status.HTTP_400_BAD_REQUEST)
