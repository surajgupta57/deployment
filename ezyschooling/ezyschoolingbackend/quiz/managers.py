from django.db import models
from . import models as quiz_models 


class QuizQuerySet(models.QuerySet):

    def get_include_question(self):
    	return self.prefetch_related(
                models.Prefetch(
                    "questions",
                    queryset=quiz_models.Question.objects.all().prefetch_related(
                        models.Prefetch(
                                "answers",
                                queryset=quiz_models.Answer.objects.all().order_by("id")
                            )
                        ).order_by("order")
                )
            )