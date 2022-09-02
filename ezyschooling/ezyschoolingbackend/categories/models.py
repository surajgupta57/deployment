from django.db import models

from core.utils import unique_slug_generator_using_name

from .util import (board_thumbnail_upload_path,
                   sub_category_thumbnail_upload_path,popup_category_thumbnail_upload_path)


class Board(models.Model):
    name = models.CharField(max_length=30, unique=True)
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=0)
    description = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    thumbnail = models.ImageField(
        upload_to=board_thumbnail_upload_path, blank=True, null=True
    )
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class SubCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(blank=True, unique=True)
    description = models.CharField(max_length=100)
    thumbnail = models.ImageField(
        upload_to=sub_category_thumbnail_upload_path, blank=True, null=True
    )
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Sub Category"
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)


class ExpertUserVideoCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(blank=True, unique=True)
    active = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Expert User Video Category"
        verbose_name_plural = "Expert User Video Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)

class PopupCategory(models.Model):
    name = models.CharField(max_length=75)
    image = models.ImageField(help_text="image size should be 1180x720 pixels",upload_to=popup_category_thumbnail_upload_path)
    link = models.CharField(max_length=250)

    class Meta:
        verbose_name = "Popup Category"
        verbose_name_plural = "Popup Category"

    def __str__(self):
        return self.name
