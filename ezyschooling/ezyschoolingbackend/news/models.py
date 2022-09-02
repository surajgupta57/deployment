import re

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.template.defaultfilters import (striptags, truncatechars,
                                            truncatewords)
from taggit_selectize.managers import TaggableManager

from analatics.models import PageVisited
from core.utils import unique_slug_generator_using_title
from tags.models import Tagged
from schools.models import SchoolProfile
from .utils import news_thumbnail_upload_path


class News(models.Model):
    DRAFT = "D"
    PUBLISHED = "P"
    STATUS = (
        (DRAFT, ("Draft")),
        (PUBLISHED, ("Published")),
    )
    title = models.CharField(max_length=250)
    mini_title = models.CharField(max_length=80, null=True, blank=True)
    author = models.ForeignKey(
        "experts.ExpertUserProfile", on_delete=models.CASCADE, related_name="expert_news")
    slug = models.SlugField(max_length=250, blank=True, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=news_thumbnail_upload_path)
    thumb_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name="Thumbnail Alt Text")
    is_featured = models.BooleanField(default=False)
    for_home_page = models.BooleanField(default=False)
    views = models.IntegerField(blank=True, default=0)
    status = models.CharField(max_length=15, choices=STATUS,
                              default=DRAFT, null=True, blank=True)
    board = models.ForeignKey(
        "categories.Board", on_delete=models.CASCADE, related_name="board_news")
    tags = TaggableManager(through=Tagged)
    for_schools = models.ManyToManyField(
        SchoolProfile, blank=True)
    visits = GenericRelation(PageVisited)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"

    @property
    def big_overview(self):
        return truncatewords(striptags(re.sub(r'<p.*?</p>', '', self.content, count=1, flags=re.DOTALL)), 18)

    @property
    def overview(self):
        ov = truncatewords(striptags(
            re.sub(r'<p.+?</p>', '', self.content, count=1, flags=re.DOTALL)), 10)
        if len(ov) < 70:
            return truncatechars(striptags(re.sub(r'<p.+?</p>', '', self.content, count=1, flags=re.DOTALL)), 68)
        return ov

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return "/news/" + self.slug


class NewsHeadline(models.Model):
    title = models.CharField(max_length=150)
    timestamp = models.DateTimeField(auto_now_add=True)
    news = models.ForeignKey(
        "news.News", on_delete=models.CASCADE, related_name="headlines")

    class Meta:
        verbose_name = "News Headline"
        verbose_name_plural = "News Headlines"

    def __str__(self):
        return self.title
