from rest_framework import serializers

from categories.api.v1.serializers import BoardSerializer
from quiz.models import *


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [
            "id",
            "question",
            "image",
            "text",
            "is_correct",
            "timestamp",
        ]


class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "image",
            "label",
            "timestamp",
        ]


class QuestionSerializer(QuestionListSerializer):

    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "quiz",
            "image",
            "label",
            "timestamp",
            "answers",
        ]


class QuizSerializer(serializers.ModelSerializer):

    quiz_completed_status = serializers.SerializerMethodField()
    board = BoardSerializer()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "board",
            "name",
            "type",
            "questions_count",
            "description",
            "meta_desc",
            "created",
            "image",
            "slug",
            "start_date",
            "end_date",
            "quiz_time_limit",
            "quiz_completed_status",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if (
            "request" in self.context
            and self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            if hasattr(instance, "quiz_taken_status"):
                response["quiz_taken_status"] = instance.quiz_taken_status
        return response

    def get_quiz_completed_status(self, instance):
        if self.context["request"].user.is_authenticated:
            return self.context["request"].user.quiztakers_set.filter(quiz_id=instance.id, completed=True).exists()
        else:
            return False


class CompleteQuizSerializer(QuizSerializer):

    questions = QuestionSerializer(many=True)
    board = BoardSerializer()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "name",
            "type",
            "board",
            "questions_count",
            "description",
            "image",
            "created",
            "slug",
            "start_date",
            "end_date",
            "quiz_time_limit",
            "questions",
        ]


class QuizCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = QuizCategory
        fields = [
            "id",
            "name",
            "slug",
            "image",
            "order",
        ]


class QuizTakersSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizTakers
        fields = [
            "id",
            "user",
            "quiz",
            "correct_answers",
            "completed",
            "timestamp",
        ]
        read_only_fields = ["correct_answers", "user"]


class QuizTakersDetailSerializer(QuizTakersSerializer):

    quiz = QuizSerializer()


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = [
            "id",
            "quiztaker",
            "question",
            "answer",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["answer"] = AnswerSerializer(instance.answer).data
        response["quiztaker"] = QuizTakersSerializer(instance.quiztaker).data
        return response


class ResponseDetailSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer()
    question = QuestionListSerializer()

    class Meta:
        model = Response
        fields = [
            "id",
            "quiztaker",
            "question",
            "answer",
        ]


class QuizTakersResultSerializer(serializers.ModelSerializer):

    response_set = ResponseDetailSerializer(many=True)

    class Meta:
        model = QuizTakers
        fields = [
            "id",
            "user",
            "quiz",
            "correct_answers",
            "completed",
            "timestamp",
            "response_set",
        ]
        read_only_fields = ["correct_answers", "user"]


class QuizResultSerializer(serializers.ModelSerializer):

    questions = QuestionSerializer(many=True)
    quiz_completed_status = serializers.SerializerMethodField()
    quiztakers_set = QuizTakersResultSerializer(many=True)
    board = BoardSerializer()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "board",
            "name",
            "type",
            "questions_count",
            "description",
            "created",
            "image",
            "slug",
            "start_date",
            "end_date",
            "quiz_time_limit",
            "quiz_completed_status",
            "quiztakers_set",
            "questions",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if (
            "request" in self.context
            and self.context["request"].user
            and self.context["request"].user.is_authenticated
        ):
            if hasattr(instance, "quiz_taken_status"):
                response["quiz_taken_status"] = instance.quiz_taken_status
        return response

    def get_quiz_completed_status(self, instance):
        if self.context["request"].user.is_authenticated:
            return self.context["request"].user.quiztakers_set.filter(quiz_id=instance.id, completed=True).exists()
        else:
            return False


class PersonalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Personality
        fields = [
            "name",
            "description",
            "photo"
        ]
