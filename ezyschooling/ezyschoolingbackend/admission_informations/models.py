from django.db import models
from taggit.managers import TaggableManager

from core.utils import unique_slug_generator_using_title
from tags.models import Tagged

from .managers import (
            AdmissionInformationArticleQuerySet,
            AdmissionInformationArticleCommentQuerySet,
            AdmissionInformationUserVideoQuerySet,
            AdmissionInformationUserVideoCommentQuerySet
        )
from .utils import admission_information_article_upload_path, admission_information_news_thumbnail_upload_path


class AdmissionInformationArticle(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    title = models.CharField(max_length=255)
    mini_title = models.CharField(max_length=80, null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to=admission_information_article_upload_path, blank=True, null=True
    )
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="admission_articles"
    )
    sub_category = models.ForeignKey(
        "categories.SubCategory",
        on_delete=models.CASCADE,
        related_name="admission_articles",
    )
    created_by = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.CASCADE,
        related_name="admission_articles",
    )
    description = models.TextField(max_length=20000)
    likes = models.ManyToManyField(
        "accounts.User",
        db_index=True,
        related_name="user_liked_admission_articles",
        blank=True,
    )
    views = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    objects = AdmissionInformationArticleQuerySet.as_manager()
    tags = TaggableManager(through=Tagged)

    class Meta:
        verbose_name = "Admission Information Article"
        verbose_name_plural = "Admission Information Articles"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)


class AdmissionInformationArticleComment(models.Model):
    article = models.ForeignKey(
        "admission_informations.AdmissionInformationArticle",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="article_comments",
    )
    comment = models.TextField(max_length=10000)
    timestamp = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="parent_users_admission_article_comment",
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_users_admission_article_comment",
    )
    anonymous_user = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full Name for non logged in users",
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_admission_article_comment_childrens",
    )
    likes = models.ManyToManyField(
        "accounts.User",
        db_index=True,
        related_name="user_liked_admission_article_comments",
    )

    objects = AdmissionInformationArticleCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Admission Information Article Comment"
        verbose_name_plural = "Admission Information Article Comments"

    def __str__(self):
        return self.comment[:50]


class AdmissionInformationUserVideo(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.CASCADE,
        related_name="expert_user_admission_videos",
    )
    title = models.CharField(max_length=250)
    url = models.URLField(help_text="Please do not enter shortened links here.")
    category = models.ForeignKey(
        "categories.ExpertUserVideoCategory",
        on_delete=models.CASCADE,
        related_name="admission_videos",
        blank=True,
        null=True,
    )
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="board_admission_videos"
    )
    sub_category = models.ForeignKey(
        "categories.SubCategory",
        on_delete=models.CASCADE,
        related_name="sub_category_admission_vidoes",
    )
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=20000)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField()
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_admission_videos", blank=True
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    views = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager(through=Tagged)
    objects = AdmissionInformationUserVideoQuerySet.as_manager()

    class Meta:
        verbose_name = "Admission Information Expert User Video"
        verbose_name_plural = "Admission Information Expert User Videos"

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)


class AdmissionInformationVideoComment(models.Model):
    video = models.ForeignKey(
        "admission_informations.AdmissionInformationUserVideo",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="video_comments",
    )
    comment = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="parent_user_admission_video_comments",
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_user_admission_video_comments",
    )
    anonymous_user = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full Name for non logged in users",
    )

    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_admission_video_comment_childrens",
    )
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_admission_video_comments"
    )

    objects = AdmissionInformationUserVideoCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Admission Information Expert Video Comment"
        verbose_name_plural = "Admission Information Expert Video Comments"

    def __str__(self):
        return self.comment[:50]


class AdmissionInformationNews(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    title = models.CharField(max_length=250)
    mini_title = models.CharField(max_length=80, null=True, blank=True)
    slug = models.SlugField(max_length=250, blank=True, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=admission_information_news_thumbnail_upload_path, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    views = models.IntegerField(blank=True, default=0)
    status = models.CharField(
        max_length=15, choices=STATUS, default=DRAFT, null=True, blank=True
    )
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="board_admission_information_news"
    )
    tags = TaggableManager(through=Tagged)

    class Meta:
        verbose_name = "Admission Inforamtion News"
        verbose_name_plural = "Admission Inforamtion News"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)


class AdmissionInformationNewsHeadline(models.Model):
    title = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True)
    news = models.ForeignKey(
        "admission_informations.AdmissionInformationNews", on_delete=models.CASCADE, related_name="headlines"
    )

    class Meta:
        verbose_name = "Admission Inforamtion News Headline"
        verbose_name_plural = "Admission Inforamtion News Headlines"

    def __str__(self):
        return self.title
