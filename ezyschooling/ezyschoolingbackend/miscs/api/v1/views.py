import time
import razorpay
from django.db import transaction
from django.db.models import BooleanField, Case, Value, When
from rest_framework import generics, permissions, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from miscs.filters import *
from news.models import News
from news.api.v1.serializers import NewsSerializer
from miscs.models import *
from miscs.tasks import (send_admission_guidance_mail, send_admission_guidance_programme_mail,
                        add_admission_guidance_data,add_contact_us_data,send_sponser_mail,
                        webinar_registration_mail,inform_admin_via_mail)
from articles.models import ExpertArticle
from articles.api.v1.serializers import ExpertArticleListSerializer
from . import serializers
from payments.models import AdmissionGuidanceFormOrder
from django.db import transaction as db_transaction
from backend.logger import log


class ContactUsView(generics.CreateAPIView):
    serializer_class = serializers.ContactUsSerializer
    queryset = ContactUs.objects.all()
    def perform_create(self, serializer):
        log(f"{self.__class__.__name__} Creating ContactUs Object",False)
        data = serializer.validated_data
        instance = serializer.save()
        transaction.on_commit(
            lambda: add_contact_us_data.delay(instance.id)
        )



class CarouselCategoryView(generics.ListAPIView):
    serializer_class = serializers.CarouselCategorySerializer

    def get_queryset(self):
        queryset = CarouselCategory.objects.all().order_by("id")
        return queryset


class CarouselView(generics.ListAPIView):
    serializer_class = serializers.CarouselSerializer
    filterset_class = CarouselFilter

    def get_queryset(self):
        queryset = Carousel.objects.filter(active=True).select_related("category").order_by("order")
        return queryset


class ActivityView(generics.ListAPIView):
    serializer_class = serializers.EzyschoolingActivitySerializer

    def get_queryset(self):
        queryset = Activity.objects.all().order_by("order")
        return queryset


class EzySchoolingNewsArticleView(generics.ListAPIView):
    serializer_class = serializers.EzySchoolingNewsArticleSerializer

    def get_queryset(self):
        queryset = EzySchoolingNewsArticle.objects.all().order_by("order")
        return queryset


class CompetitionCarouselView(generics.ListAPIView):
    queryset = CompetitionCarousel.objects.all().select_related(
        "category").order_by("order", "id")
    serializer_class = serializers.CompetitionCarouselSerializer


class OnlineEventListView(generics.ListAPIView):
    queryset = OnlineEvent.objects.filter(active=True)
    serializer_class = serializers.OnlineEventSerializer
    filterset_class = OnlineEventFilter


class AchieverView(generics.CreateAPIView):
    serializer_class = serializers.AchieverSerializer
    queryset = Achiever.objects.all()


class CustomTalentHuntPagination(LimitOffsetPagination):
    default_limit = 50


class TalentHuntSubmissionsView(generics.ListCreateAPIView):
    pagination_class = CustomTalentHuntPagination
    serializer_class = serializers.TalentHuntSubmissionsSerializer
    queryset = TalentHuntSubmission.objects.order_by("-created_at")
    filterset_fields = ["is_winner"]


class TalentHuntSubmissionsDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.TalentHuntSubmissionsDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = TalentHuntSubmission.objects.all()
        if self.request.user and self.request.user.is_authenticated:
            user_liked_talenthunt_video = self.request.user.user_liked_talenthunt_video.values_list(
                "id", flat=True)
            queryset = queryset.annotate(
                like_status=Case(
                    When(id__in=user_liked_talenthunt_video, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
            )
        return queryset


class TalentHuntSubmissionsLikeApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug", None)
        talent_hunt_post = generics.get_object_or_404(
            TalentHuntSubmission, slug=slug)
        if talent_hunt_post.likes.filter(id=request.user.id).exists():
            log(f"{self.__class__.__name__} UnLiked by userID {request.user.id}",False)
            talent_hunt_post.likes.remove(request.user.id)
            return Response({"unliked": "Successfully Unliked!"})
        else:
            log(f"{self.__class__.__name__} Liked by userID {request.user.id}",False)
            talent_hunt_post.likes.add(request.user.id)
            return Response({"liked": "Successfully Liked!"})


class FaqQuestionView(generics.ListAPIView):
    serializer_class = serializers.FaqQuestionSerializer
    queryset = FaqQuestion.objects.all().filter(status="P").order_by("id")
    filterset_class = FaqQuestionFilter

class FaqNewQuestionView(generics.ListAPIView):
    serializer_class = serializers.FaqQuestionSerializer
    queryset = FaqQuestion.objects.all().filter(status="P").order_by("id")
    filterset_class = FaqQuestionFilter
    def list(self, request):
        school_board = self.request.query_params.get('school_board', '')
        school_type = self.request.query_params.get('school_type', '')
        district = self.request.query_params.get('district', '')
        popular_area = self.request.query_params.get('popular_area', '')
        grade = self.request.query_params.get('grade', '')
        co_ed_status = self.request.query_params.get('co_ed_status', '')
        city =self.request.query_params.get('city', '')
        is_popular=self.request.query_params.get('is_popular', '')
        if(is_popular):
            is_popular="Yes"
        else:
            is_popular="No"
        filter_school_board=FaqQuestion.objects.filter(board__slug__iexact=school_board)[:5]
        filter_school_type = FaqQuestion.objects.filter(school_type__slug__iexact=school_type)[:5]
        filter_district = FaqQuestion.objects.filter(district__slug__iexact=district)[:5]
        filter_popular_area = FaqQuestion.objects.filter(district_region__slug__iexact=popular_area)[:5]
        filter_grade = FaqQuestion.objects.filter(class_relation__slug__iexact=grade)[:5]
        filter_co_ed_status = FaqQuestion.objects.filter(school_category__iexact=co_ed_status)[:5]
        filter_city=FaqQuestion.objects.filter(city__slug__iexact=city)[:5]
        filter_is_popular=FaqQuestion.objects.filter(popular__iexact=is_popular)[:5]

        serialize={}
        if(filter_school_board.count()):
            serialize["school_board"]=serializers.FaqQuestionSerializer(filter_school_board,many=True).data
        if (filter_school_type.count()):
            serialize["school_type"] = serializers.FaqQuestionSerializer(filter_school_type, many=True).data
        if (filter_district.count()):
            serialize["district"] = serializers.FaqQuestionSerializer(filter_district, many=True).data
        if (filter_popular_area.count()):
            serialize["popular_area"] = serializers.FaqQuestionSerializer(filter_popular_area, many=True).data
        if (filter_grade.count()):
            serialize["grade"] = serializers.FaqQuestionSerializer(filter_grade, many=True).data
        if (filter_co_ed_status.count()):
            serialize["co_ed_status"] = serializers.FaqQuestionSerializer(filter_co_ed_status, many=True).data
        if(filter_city.count()):
            serialize["city"]=serializers.FaqQuestionSerializer(filter_city, many=True).data
        if (filter_is_popular.count()):
            serialize["is_popular"] = serializers.FaqQuestionSerializer(filter_is_popular, many=True).data

        if(len(serialize)):
            return Response({
                'result': serialize
            }, status=status.HTTP_200_OK)
        else:
            serialize["all"]=serializers.FaqQuestionSerializer(FaqQuestion.objects.all().filter(status="P").order_by("id")[:5],many=True).data
            return Response({
                'result': serialize
            }, status=status.HTTP_200_OK)

class AdmissionGuidanceSlotListView(generics.ListAPIView):
    queryset = AdmissionGuidanceSlot.objects.all()
    serializer_class = serializers.AdmissionGuidanceSlotSerializer


class AdmissionGuidanceCreateView(generics.CreateAPIView):
    queryset = AdmissionGuidance.objects.all()
    serializer_class = serializers.AdmissionGuidanceSerializer

    def create(self, request, *args, **kwargs):
        serializer = serializers.AdmissionGuidanceSerializer(data=request.data)
        if serializer.is_valid():
            log(f"{self.__class__.__name__} Serializer Valid Creating AdmissionGuidanceSlot",False)
            data = serializer.validated_data
            email = data["email"]
            instance = serializer.save()
            db_transaction.on_commit(
                lambda: add_admission_guidance_data.delay(instance.id)
            )
            db_transaction.on_commit(
                lambda: send_admission_guidance_mail.delay(instance.id)
            )
            return Response({"mail": "success"}, status.HTTP_200_OK)

            # try:
            #     amount = 200
            #     DATA = {
            #         "amount": amount*100,
            #         "currency": "INR",
            #         "receipt": "ezy_ag_receipt_" + str(time.time()),
            #         "payment_capture": 1
            #     }
            #     client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))
            #     data = client.order.create(data=DATA)

            #     AdmissionGuidanceFormOrder.objects.create(person=instance,
            #         amount=amount, order_id=data["id"])
            #     return Response({"order_id": data["id"]})
            # except:
            #     return Response(status=status.HTTP_404_NOT_FOUND)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdmissionAlertView(generics.CreateAPIView):
    serializer_class = serializers.AdmissionAlertSerializer

class AdmissionGuidanceProgrammeCreateView(generics.CreateAPIView):
    serializer_class = serializers.AdmissionGuidanceProgrammeSerializer

    def perform_create(self, serializer):
        log(f"{self.__class__.__name__} Creating Admission Guidance Programme",False)
        data = serializer.validated_data
        email = data["email"]
        name=data['name']
        instance = serializer.save()
        transaction.on_commit(
            lambda: send_admission_guidance_programme_mail.delay(instance.id,name)
        )

class SurveyListView(generics.ListAPIView):
    queryset = SurveyQuestions.objects.all()
    serializer_class = serializers.SurveyQuestionSerializer

class SurveyResponseCreateView(generics.CreateAPIView):
    serializer_class = serializers.SurveyCreateSerializer
    permission_classes=[permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            log(f"{self.__class__.__name__} Serializer valid Creating Survey Response For userid:{request.user.id}",False)
            taker,boolean = SurveyTaker.objects.get_or_create(user=self.request.user)
            serializer.save(taker=taker)
            return Response(status=status.HTTP_200_OK)
        log(f"{self.__class__.__name__} Serializer Invalid HTTP400 For userid:{request.user.id} ",True)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class CheckSurveyResponseView(APIView):
    permission_classes=[permissions.IsAuthenticated]

    def get(self,request,pk):
        has_taken_survey=SurveyResponses.objects.filter(question=pk,taker__user=self.request.user).exists()
        log(f"{self.__class__.__name__} Getting Survey Responses for userid:{request.user.id} data={has_taken_survey}",False)
        return Response({"has_taken_survey":has_taken_survey},status=status.HTTP_200_OK)



class WebinarRegistrationsView(generics.ListCreateAPIView):
    serializer_class = serializers.WebinarRegistrationSeralizer
    queryset = WebinarRegistrations.objects.all()



    def post(self, request, *args, **kwargs):
        serializer = serializers.WebinarRegistrationSeralizer(data=self.request.data)
        if serializer.is_valid():
            instance=serializer.save()
            transaction.on_commit(
            lambda: webinar_registration_mail.delay(instance.id)
            )
            transaction.on_commit(
            lambda: inform_admin_via_mail.delay(instance.id)
            )

        return Response({"message":"mail sent for webinar"},status=status.HTTP_200_OK)

class SponsorsRegistrationsView(generics.ListCreateAPIView):
    serializer_class = serializers.SponsorsRegistrationsSerializer
    queryset = SponsorsRegistrations.objects.all()
    def post(self, request, *args, **kwargs):
        serializer = serializers.SponsorsRegistrationsSerializer(data=self.request.data)
        if serializer.is_valid():
            instance=serializer.save()
            transaction.on_commit(
            lambda: send_sponser_mail.delay(instance.id)
            )
        return Response({"message":"mail sent for sponser registration"},status=status.HTTP_200_OK)

class PastAndCurrentImpactinarsView(generics.ListCreateAPIView):
    serializer_class = serializers.PastAndCurrentImpactinarsSerializer
    def get_queryset(self):
        is_current =self.request.GET.get("is_current",None)
        is_featured =self.request.GET.get("is_featured",None)
        is_latest =self.request.GET.get("is_latest",None)
        if is_current:
            return PastAndCurrentImpactinars.objects.all().filter(is_current=is_current,status="P")
        if is_featured:
            return PastAndCurrentImpactinars.objects.all().filter(is_featured=is_featured,status="P")
        if is_latest:
            return PastAndCurrentImpactinars.objects.all().filter(status="P").order_by('-id')[:5]
        return PastAndCurrentImpactinars.objects.all().filter(status="P")

class InvitedPrincipalsView(generics.ListCreateAPIView):
    serializer_class = serializers.InvitedPrincipalsSerializer
    queryset = InvitedPrincipals.objects.all()


class TestimonialView(generics.ListCreateAPIView):
    serializer_class = serializers.TestimonialsSerializer

    def get_queryset(self):
        is_school =self.request.GET.get("is_school",None)
        if is_school:
            return Testimonials.objects.all().filter(is_school=is_school)
        return Testimonials.objects.all()




class OurSponsers(generics.ListCreateAPIView):
    serializer_class = serializers.OurSponsersSerializer
    queryset = OurSponsers.objects.all()


class EzyschoolingEmployeeAPIview(generics.ListCreateAPIView):
    serializer_class = serializers.EzyschoolingEmployeeSerializer
    queryset = EzyschoolingEmployees.objects.all()

class UnsubscribeEmailView(generics.ListCreateAPIView):
   serializer_class= serializers.UnsubscribeEmailSerializer
   queryset=UnsubscribeEmail.objects.all()

class HomePageArticleNews(APIView):
   def get(self,request):
       news=News.objects.filter(for_home_page=True)
       article=ExpertArticle.objects.filter(for_home_page=True)
       news_serializer=NewsSerializer(news,many=True)
       article_serializer=ExpertArticleListSerializer(article, many=True)
       result={}
       result["results"]=[news_serializer.data,article_serializer.data]
       return Response(result,status=status.HTTP_200_OK)

# class DistrictRegionFAQS(APIView):
#     def get(self,request,**kwargs):
#         dr_slug =self.kwargs.get("slug")
#         obj = FaqAnswer.objects.filter(question__district_region__slug=dr_slug)
#         result = {}
#         for i in obj:
#             result ={
#                 "quest":i.question.title,
#                 "answwer":i.answer
#             }
#         return Response(result,status=status.HTTP_200_OK)
