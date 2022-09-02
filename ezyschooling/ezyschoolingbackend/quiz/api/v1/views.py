from django.core.exceptions import ObjectDoesNotExist
from django.db.models import BooleanField, Case, Count, Prefetch, Value, When
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response as DRFResponse

from quiz.filters import QuizCategoryFilter, QuizFilter, QuizTakerFilter
from quiz.models import *

from . import serializers


class QuizView(generics.ListAPIView):
    filterset_class = QuizFilter

    def get_queryset(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = Quiz.objects.all()
        else:
            queryset = Quiz.objects.filter(roll_out=True)
        if self.request.user and self.request.user.is_authenticated:
            user_taken_quiz = self.request.user.quiztakers_set.values_list(
                "quiz__id", flat=True
            )
            queryset = queryset.annotate(
                quiz_taken_status=Case(
                    When(id__in=user_taken_quiz, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        return queryset.select_related("board")

    def get_serializer_class(self):
        include_question = self.request.GET.get("include_question", None)
        if include_question == "yes":
            return serializers.CompleteQuizSerializer
        else:
            return serializers.QuizSerializer


class QuizDetailView(generics.RetrieveAPIView):
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = Quiz.objects.all()
        else:
            queryset = Quiz.objects.filter(roll_out=True)
        if self.request.user and self.request.user.is_authenticated:
            user_taken_quiz = self.request.user.quiztakers_set.values_list(
                "quiz__id", flat=True
            )
            queryset = queryset.annotate(
                quiz_taken_status=Case(
                    When(id__in=user_taken_quiz, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        return queryset.select_related("board")

    def get_serializer_class(self):
        include_question = self.request.GET.get("include_question", None)
        if include_question == "yes":
            return serializers.CompleteQuizSerializer
        else:
            return serializers.QuizSerializer


class ResponseView(generics.ListCreateAPIView):
    serializer_class = serializers.ResponseSerializer
    filterset_fields = ("quiztaker",)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Response.objects.all().select_related("answer", "question")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ResponseSerializer
        elif self.request.method == "GET":
            return serializers.ResponseDetailSerializer


class QuizTakersView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = QuizTakerFilter

    def get_queryset(self):
        queryset = (
            QuizTakers.objects.filter(user=self.request.user)
            .select_related("quiz")
            .order_by("-timestamp")
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.QuizTakersSerializer
        elif self.request.method == "GET":
            return serializers.QuizTakersDetailSerializer


class QuizTakersDetailView(generics.RetrieveUpdateAPIView):
    lookup_field = "pk"
    queryset = QuizTakers.objects.all().select_related("quiz")

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.QuizTakersSerializer
        elif self.request.method == "GET":
            return serializers.QuizTakersDetailSerializer


class ResultQuizDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.QuizResultSerializer

    def get_queryset(self):
        queryset = Quiz.objects.all().select_related("board")
        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        quiztaker_id = self.kwargs.get("quiztaker_id", None)
        quiz_id = QuizTakers.objects.values_list(
            "quiz", flat=True).get(id=quiztaker_id)
        if quiztaker_id:
            try:
                instance = queryset.get_include_question().prefetch_related(
                    Prefetch(
                        "quiztakers_set",
                        queryset=QuizTakers.objects.filter(id=quiztaker_id).prefetch_related(
                            Prefetch(
                                "response_set",
                                queryset=Response.objects.all().select_related("question", "answer")
                            )
                        )
                    )
                ).get(id=quiz_id)
                return instance
            except ObjectDoesNotExist:
                raise Http404
        raise Http404


class PersonalityAssessmentDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.PersonalitySerializer
    queryset = Personality.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        quiztaker_id = self.kwargs.get("quiztaker_id", None)
        if quiztaker_id:
            try:
                quiz_id = QuizTakers.objects.values_list(
                    "quiz", flat=True).get(id=quiztaker_id)
                score = QuizTakers.objects.get(id=quiztaker_id).score
            except ObjectDoesNotExist:
                raise Http404
            personalities = Quiz.objects.get(pk=quiz_id).questions.values_list(
                "answers__personality", flat=True).distinct()
            instance = queryset.filter(pk__in=personalities).filter(
                result_start__lte=score, result_end__gte=score).first()
            return instance
        raise Http404


class RelatedQuizView(generics.ListAPIView):

    def get_queryset(self):
        slug = self.kwargs.get("slug", None)
        queryset = Quiz.objects.filter(roll_out=True)
        if self.request.user and self.request.user.is_authenticated:
            user_taken_quiz = self.request.user.quiztakers_set.values_list(
                "quiz__id", flat=True
            )
            queryset = queryset.annotate(
                quiz_taken_status=Case(
                    When(id__in=user_taken_quiz, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            ).exclude(quiz_taken_status=True)
        related_quiz_limit = self.request.GET.get("related_quiz_limit", 3)
        if slug:
            quiz = generics.get_object_or_404(Quiz, slug=slug)
            queryset = queryset.filter(roll_out=True).filter(
                category=quiz.category)[:int(related_quiz_limit)]
        return queryset

    def get_serializer_class(self):
        include_question = self.request.GET.get("include_question", None)
        if include_question == "yes":
            return serializers.CompleteQuizSerializer
        else:
            return serializers.QuizSerializer


class QuizCategoryView(generics.ListAPIView):
    serializer_class = serializers.QuizCategorySerializer
    filterset_class = QuizCategoryFilter

    def get_queryset(self):
        queryset = QuizCategory.objects.all()
        return queryset


class QuizCategoryDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.QuizCategorySerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = QuizCategory.objects.all()
        return queryset

class QuizSitemapData(APIView):
    def get(self, request, format=False):
        data = list(Quiz.objects.filter(roll_out=True).values_list("slug", flat=True))
        return DRFResponse(data, status=status.HTTP_200_OK)
