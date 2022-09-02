from django.db import models

# Create your models here.
class Operator(models.Model):
    name = models.CharField(max_length=250)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    school = models.ManyToManyField("schools.SchoolProfile")
    credit = models.DecimalField(default=0,max_digits=9,decimal_places=3)

    def __str__(self):
        return self.name