from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Question, Quiz, Response


@receiver(post_save, sender=Quiz)
def set_default_quiz(sender, instance, created, **kwargs):
    quiz = Quiz.objects.filter(id=instance.id)
    quiz.update(questions_count=instance.questions.filter(
        quiz=instance.pk).count())


@receiver(post_save, sender=Question)
def set_default(sender, instance, created, **kwargs):
    quiz = Quiz.objects.filter(id=instance.quiz.id)
    quiz.update(
        questions_count=instance.quiz.questions.filter(
            quiz=instance.quiz.pk).count()
    )


@receiver(post_save, sender=Response)
@receiver(post_delete, sender=Response)
def update_correct_answers_count(sender, instance, **kwargs):
    responses = Response.objects.filter(quiztaker=instance.quiztaker)
    if instance.quiztaker.quiz.type == Quiz.PERSONALITY:
        instance.quiztaker.score = responses.aggregate(
            score=Sum("answer__personality__points"))["score"]
    else:
        instance.quiztaker.correct_answers = responses.filter(
            answer__is_correct=True).count()
    instance.quiztaker.save()
