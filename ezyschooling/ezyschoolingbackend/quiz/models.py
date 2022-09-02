from django.contrib.auth.models import User
from django.db import models

from core.utils import unique_slug_generator_using_name

from .managers import QuizQuerySet


class QuizCategoryPlace(models.Model):
    name = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Quizzes Category Places"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class QuizCategory(models.Model):
    name = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    image = models.FileField(upload_to="quiz-categroy/", null=True, blank=True)
    order = models.IntegerField(default=0)
    places = models.ManyToManyField("quiz.QuizCategoryPlace", blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Quizzes Category"
        ordering = [
            "order",
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class Quiz(models.Model):
    REGULAR = "R"
    PERSONALITY = "P"
    TYPE_CHOICES = (
        (REGULAR, "Regular"),
        (PERSONALITY, "Personality Assessment"),
    )

    category = models.ForeignKey(
        "quiz.QuizCategory", on_delete=models.SET_NULL, related_name="quizzes", blank=True, null=True)
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=REGULAR)
    board = models.ForeignKey("categories.Board", on_delete=models.SET_NULL,
                              related_name="quizzes", blank=True, null=True)
    image = models.ImageField(upload_to="quiz/", blank=True, null=True)
    name = models.CharField(max_length=1000)
    questions_count = models.IntegerField(default=0)
    description = models.CharField(max_length=70)
    meta_desc = models.TextField(blank=True, null=True, verbose_name="Meta Description")
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    roll_out = models.BooleanField(
        default=False, help_text="Only roll the quiz out after selecting board and category since mails will be sent. If you leave any of them out, mails won't be sent.")
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    quiz_time_limit = models.PositiveIntegerField(
        help_text="Enter time limits in seconds")

    objects = QuizQuerySet.as_manager()

    class Meta:
        ordering = [
            "created",
        ]
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return "/parenting/quiz/" + self.slug


class Question(models.Model):
    quiz = models.ForeignKey(
        "quiz.Quiz", on_delete=models.CASCADE, related_name="questions")
    label = models.CharField(max_length=1000)
    order = models.IntegerField(default=0)
    image = models.ImageField(
        upload_to="quiz/questions/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.label


class Answer(models.Model):
    question = models.ForeignKey(
        "quiz.Question", on_delete=models.CASCADE, related_name="answers")
    image = models.ImageField(upload_to="quiz/answers/", blank=True, null=True)
    personality = models.ForeignKey(
        "quiz.Personality", on_delete=models.SET_NULL, null=True, blank=True)
    text = models.CharField(max_length=1000)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class QuizTakers(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    quiz = models.ForeignKey("quiz.Quiz", on_delete=models.CASCADE)
    correct_answers = models.IntegerField(default=0)
    score = models.IntegerField(default=0, null=True)
    completed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Response(models.Model):
    quiztaker = models.ForeignKey(
        "quiz.QuizTakers", on_delete=models.CASCADE)
    question = models.ForeignKey("quiz.Question", on_delete=models.CASCADE)
    answer = models.ForeignKey(
        "quiz.Answer", on_delete=models.CASCADE, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question.label


class Personality(models.Model):
    name = models.CharField(max_length=255)
    photo = models.ImageField(blank=True, null=True)
    description = models.TextField()
    points = models.IntegerField()
    result_start = models.IntegerField(verbose_name="Result Range Start")
    result_end = models.IntegerField(verbose_name="Result Range End")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quiz Personality"
        verbose_name_plural = "Quiz Personalities"

    def __str__(self):
        return self.name
