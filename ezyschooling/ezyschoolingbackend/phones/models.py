from django.db import models


class PhoneNumber(models.Model):
    user = models.ForeignKey(
        "accounts.user",
        on_delete=models.CASCADE
    )
    number = models.CharField(max_length=10)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Phone Number"
        verbose_name_plural = "Phone Numbers"

    def __str__(self):
        return self.number

