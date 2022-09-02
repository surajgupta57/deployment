from django.db import models
from taggit.models import GenericTaggedItemBase, TagBase


class CustomTag(TagBase):
    similar_tag = models.ManyToManyField("self", blank=True)
    featured = models.BooleanField(default=False)


class Tagged(GenericTaggedItemBase):
    tag = models.ForeignKey(
        CustomTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.SET_NULL,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)


class CustomSkillTag(TagBase):
    similar_tag = models.ManyToManyField("self", blank=True)
    featured = models.BooleanField(default=False)


class SkillTagged(GenericTaggedItemBase):
    tag = models.ForeignKey(
        CustomSkillTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.SET_NULL,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

class CustomMustSkillTag(TagBase):
    similar_tag = models.ManyToManyField("self", blank=True)
    featured = models.BooleanField(default=False)


class MustSkillTagged(GenericTaggedItemBase):
    tag = models.ForeignKey(
        CustomMustSkillTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.SET_NULL,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
