from django.db import models

from core.utils import unique_slug_generator_using_name

from .utils import expert_user_profile_picture_upload_path


class ExpertUserProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="expert_user"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, blank=True, null=True, unique=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    quote = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=expert_user_profile_picture_upload_path, blank=True, null=True
    )
    bio = models.TextField(blank=True, null=True)
    is_expert_panel = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Expert User Profile"
        verbose_name_plural = "Expert User Profiles"

    def __str__(self):
        return str(self.name) if self.name else self.user.username

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_name(self)
        super().save(*args, **kwargs)
