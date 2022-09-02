from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _


class PageVisited(models.Model):
    OBJECT_TYPE = (
        ("news", ("news")),
        ("experts", ("experts")),
        ("videos", ("videos")),
        ("discussions", ("discussions")),
    )

    path = models.CharField(max_length=1000, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True
    )
    client_ip = models.CharField(max_length=200, null=True, blank=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    is_mobile = models.BooleanField(default=False, blank=True, null=True)
    is_tablet = models.BooleanField(default=False, blank=True, null=True)
    is_touch_capable = models.BooleanField(default=False, blank=True, null=True)
    is_pc = models.BooleanField(default=False, blank=True, null=True)
    is_bot = models.BooleanField(default=False, blank=True, null=True)

    browser_family = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=100, blank=True, null=True)
    browser_version_string = models.CharField(max_length=100, blank=True, null=True)

    os_family = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=100, blank=True, null=True)
    os_version_string = models.CharField(max_length=100, blank=True, null=True)

    device_family = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Page Visit"
        verbose_name_plural = "Pages Visits"


ADDITION = 1
CHANGE = 2
DELETION = 3
READ = 4

ACTION_FLAG_CHOICES = (
    (ADDITION, _('Addition')),
    (CHANGE, _('Change')),
    (DELETION, _('Deletion')),
    (READ, _('Read')),
)

class ClickLogEntry(models.Model):
    action_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        verbose_name=_('user'),
        blank=True, null=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name=_('content type'),
        blank=True, null=True,
    )
    object_id = models.TextField(_('object id'), blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    action_flag = models.PositiveSmallIntegerField(_('action flag'), choices=ACTION_FLAG_CHOICES)
    path = models.CharField(max_length=1000, blank=True, null=True)
    next_page_path = models.CharField(max_length=1000, blank=True, null=True)
    
    client_ip = models.CharField(max_length=200, null=True, blank=True)
    
    is_mobile = models.BooleanField(default=False, blank=True, null=True)
    is_tablet = models.BooleanField(default=False, blank=True, null=True)
    is_touch_capable = models.BooleanField(default=False, blank=True, null=True)
    is_pc = models.BooleanField(default=False, blank=True, null=True)
    is_bot = models.BooleanField(default=False, blank=True, null=True)

    browser_family = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=100, blank=True, null=True)
    browser_version_string = models.CharField(max_length=100, blank=True, null=True)

    os_family = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=100, blank=True, null=True)
    os_version_string = models.CharField(max_length=100, blank=True, null=True)

    device_family = models.CharField(max_length=100, blank=True, null=True)
    
    action_message = models.TextField(_('action message'), blank=True)

    class Meta:
        ordering = ['-action_time']
        
    def is_addition(self):
        return self.action_flag == ADDITION

    def is_change(self):
        return self.action_flag == CHANGE

    def is_deletion(self):
        return self.action_flag == DELETION

    def is_read(self):
        return self.action_flag == READ
