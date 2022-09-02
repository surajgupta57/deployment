from django.db import models

from articles.managers import ExpertArticleQuerySet, ExpertArticleCommentQuerySet
from videos.managers import ExpertUserVideoCommentQuerySet, ExpertUserVideoQuerySet


class AdmissionInformationArticleQuerySet(ExpertArticleQuerySet):
    """Personalized queryset created to improve model usability"""
    pass


class AdmissionInformationArticleCommentQuerySet(ExpertArticleCommentQuerySet):
    """Personalized queryset created to improve model usability"""

    def like_comment_count(self):
        return self.annotate(
            likes_count=models.Count("likes", distinct=True),
            children_comment_count=models.Count(
                "user_admission_article_comment_childrens", distinct=True
            ),
        )


class AdmissionInformationUserVideoQuerySet(ExpertUserVideoQuerySet):
    """Personalized queryset created to improve model usability"""
    pass


class AdmissionInformationUserVideoCommentQuerySet(ExpertUserVideoCommentQuerySet):
    """Personalized queryset created to improve model usability"""

    def like_comment_count(self):
        return self.annotate(
            likes_count=models.Count("likes", distinct=True),
            children_comment_count=models.Count(
                "user_admission_video_comment_childrens", distinct=True
            ),
        )
