from django.db import models

from core.utils import unique_slug_generator_using_title


class BrandProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="brand_profile"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brand"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug_generator_using_title(self)
        super().save(*args, **kwargs)


class BrandEnquiry(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    brand = models.ForeignKey(
        "brands.BrandProfile", on_delete=models.CASCADE, related_name="brand_enquiry"
    )

    class Meta:
        verbose_name = "Brand Enquiry"
        verbose_name_plural = "Brand Enquiries"

    def __str__(self):
        return self.name
