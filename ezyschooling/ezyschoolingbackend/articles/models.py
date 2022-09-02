from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from taggit_selectize.managers import TaggableManager

from analatics.models import PageVisited
from core.utils import unique_slug_generator_using_title
from tags.models import Tagged
from schools.models import SchoolProfile
from .managers import ExpertArticleCommentQuerySet, ExpertArticleQuerySet
from .utils import expert_article_upload_path,expert_article_audio_upload_path


class ExpertArticle(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    title = models.CharField(max_length=255)
    mini_title = models.CharField(max_length=80, null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to=expert_article_upload_path, blank=True, null=True
    )
    thumb_desc = models.CharField(max_length=255, blank=True, null=True, verbose_name="Thumbnail Alt Text")
    meta_desc = models.TextField(blank=True, null=True, verbose_name="Meta Description")
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="expert_articles")
    sub_category = models.ForeignKey(
        "categories.SubCategory", on_delete=models.CASCADE, related_name="expert_articles")
    popup_category = models.ForeignKey("categories.PopupCategory", blank=True, null=True,
        on_delete=models.CASCADE,related_name="expert_articles_popup_details")
    created_by = models.ForeignKey(
        "experts.ExpertUserProfile", on_delete=models.CASCADE, related_name="expert_articles")
    description = models.TextField(max_length=20000)
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_expert_articles", blank=True)
    views = models.PositiveIntegerField(default=0)
    for_home_page = models.BooleanField(default=False)
    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    audio_file = models.FileField(upload_to=expert_article_audio_upload_path,blank=True,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
    tags = TaggableManager(through=Tagged)
    for_schools = models.ManyToManyField(
        SchoolProfile, blank=True)
    comment_counts = models.PositiveIntegerField(default=0)
    like_counts = models.PositiveIntegerField(default=0)
    visits = GenericRelation(PageVisited)
    objects = ExpertArticleQuerySet.as_manager()

    class Meta:
        verbose_name = "Expert Article"
        verbose_name_plural = "Expert Articles"
        ordering = [
            "-pinned",
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return "/parenting/expert/" + self.slug


class ExpertArticleComment(models.Model):
    article = models.ForeignKey("articles.ExpertArticle",
                                on_delete=models.SET_NULL, blank=True, null=True, related_name="article_comments")
    comment = models.TextField(max_length=10000)
    timestamp = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey("parents.ParentProfile", on_delete=models.SET_NULL,
                               blank=True, null=True, related_name="parent_users_expert_article_comment")
    expert = models.ForeignKey("experts.ExpertUserProfile", on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="expert_users_expert_article_comment")

    parent_comment = models.ForeignKey("self", on_delete=models.SET_NULL,
                                       blank=True, null=True, related_name="user_expert_article_comment_childrens")
    anonymous_user = models.CharField(
        max_length=255, blank=True, null=True, help_text="Full Name for non logged in users")
    likes = models.ManyToManyField("accounts.User", db_index=True,
                                   related_name="user_liked_expert_article_comments", blank=True)

    objects = ExpertArticleCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Expert Article Comment"
        verbose_name_plural = "Expert Article Comments"

    def __str__(self):
        return self.comment[:50]
