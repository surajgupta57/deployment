from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from taggit_selectize.managers import TaggableManager

from analatics.models import PageVisited
from core.utils import unique_slug_generator_using_title
from tags.models import Tagged

from .managers import DiscussionCommentQuerySet, DiscussionQuerySet


class Discussion(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    title = models.CharField(max_length=255)
    anonymous_user = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full Name for non logged in users",
    )
    parent = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="parent_user_discussions",
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="expert_user_discussion",
    )
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="board_discussion"
    )
    sub_category = models.ForeignKey(
        "categories.SubCategory",
        on_delete=models.CASCADE,
        related_name="sub_category_discussion",
    )
    description = models.TextField(max_length=20000, blank=True, null=True)
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="discussion_likes", blank=True
    )
    views = models.PositiveIntegerField(default=0)
    visits = GenericRelation(PageVisited)
    status = models.CharField(
        max_length=15,
        choices=STATUS,
        default=DRAFT,
        null=True,
        blank=True,
        db_index=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager(through=Tagged)

    objects = DiscussionQuerySet.as_manager()

    class Meta:
        verbose_name = "Discussion"
        verbose_name_plural = "Discussions"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return "/parenting/parent/" + self.slug


class DiscussionComment(models.Model):
    discussion = models.ForeignKey(
        "discussions.Discussion",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="discussion_comments",
    )
    comment = models.TextField(max_length=10000)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_discussion_comment_childrens",
    )
    parent = models.ForeignKey(
        "parents.ParentProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="parent_user_discussion_comment",
    )
    expert = models.ForeignKey(
        "experts.ExpertUserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expert_user_discussion_comments",
    )
    anonymous_user = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Full Name for non logged in users",
    )
    likes = models.ManyToManyField(
        "accounts.User", db_index=True, related_name="user_liked_discussion_comments", blank=True
    )

    objects = DiscussionCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Discussion Comment"
        verbose_name_plural = "Discussion Comments"

    def __str__(self):
        return self.comment[:50]
