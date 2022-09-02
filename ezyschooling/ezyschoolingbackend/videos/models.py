from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from taggit_selectize.managers import TaggableManager

from analatics.models import PageVisited
from core.utils import unique_slug_generator_using_title
from tags.models import Tagged

from .managers import ExpertUserVideoCommentQuerySet, ExpertUserVideoQuerySet


class ExpertUserVideo(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.CASCADE,
        related_name="expert_user_videos",
    )
    title = models.CharField(max_length=250)
    url = models.URLField(
        help_text="Please do not enter shortened links here.")
    category = models.ForeignKey(
        "categories.ExpertUserVideoCategory",
        on_delete=models.CASCADE,
        related_name="videos",
        blank=True,
        null=True,
    )
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="board_videos"
    )
    sub_category = models.ForeignKey(
        "categories.SubCategory",
        on_delete=models.CASCADE,
        related_name="sub_category_vidoes",
    )
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=20000)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField()
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_videos", blank=True
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    youtube_views = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager(through=Tagged)
    pinned = models.BooleanField(default=False)
    visits = GenericRelation(PageVisited)
    objects = ExpertUserVideoQuerySet.as_manager()
    last_views_update = models.DateField(null=True,blank=True)

    class Meta:
        verbose_name = "Expert User Video"
        verbose_name_plural = "Expert User Videos"
        ordering = [
            "-pinned",
        ]

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return "/parenting/video/" + self.slug


class ExpertVideoComment(models.Model):
    video = models.ForeignKey(
        "videos.ExpertUserVideo",
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
        related_name="parent_user_video_comments",
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_user_video_comments",
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
        related_name="user_expert_video_comment_childrens",
    )
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_video_comments"
    )

    objects = ExpertUserVideoCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Expert Video Comment"
        verbose_name_plural = "Expert Video Comments"

    def __str__(self):
        return self.comment[:50]
