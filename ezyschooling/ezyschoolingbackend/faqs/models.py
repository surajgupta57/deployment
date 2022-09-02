from django.db import models

# Create your models here.

#City+District+Is Popular Model

class CityDistrictFaq(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    STATUS = (("Draft", "Draft Faq"), ("Published", "Published Faq"))
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    city = models.ForeignKey("schools.City",on_delete=models.SET_NULL,null=True,blank=True)
    district = models.ForeignKey("schools.District",on_delete=models.SET_NULL,null=True,blank=True)
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    faq_answer = models.TextField(null=True,blank=True)
    title=models.CharField(max_length=100,null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.district} - {self.is_popular}"

    class Meta:
        verbose_name = "City / District - FAQ"
        verbose_name_plural = "City / District - FAQs"

#City+District+Board+Is Popular Model

class CityDistrictBoardFaq(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    STATUS = (("Draft", "Draft Faq"), ("Published", "Published Faq"))
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    city = models.ForeignKey("schools.City",on_delete=models.SET_NULL,null=True,blank=True)
    district = models.ForeignKey("schools.District",on_delete=models.SET_NULL,null=True,blank=True)
    school_board = models.ForeignKey("schools.SchoolBoard", on_delete=models.SET_NULL, null=True, blank=True)
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    faq_answer = models.TextField(null=True,blank=True)
    title=models.CharField(max_length=100,null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.district} - {self.is_popular} - {self.school_board}"

    class Meta:
        verbose_name = "City / District - Board FAQ"
        verbose_name_plural = "City / District - Board FAQs"

#City+District+School Type+Is Popular Model

class CityDistrictSchoolTypeFaq(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    STATUS = (("Draft", "Draft Faq"), ("Published", "Published Faq"))
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    city = models.ForeignKey("schools.City",on_delete=models.SET_NULL,null=True,blank=True)
    district = models.ForeignKey("schools.District",on_delete=models.SET_NULL,null=True,blank=True)
    school_type = models.ForeignKey("schools.SchoolType", on_delete=models.SET_NULL, null=True, blank=True)
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    faq_answer = models.TextField(null=True,blank=True)
    title=models.CharField(max_length=100,null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.district} - {self.is_popular}- {self.school_type}"

    class Meta:
        verbose_name = "City / District - School Type FAQ"
        verbose_name_plural = "City / District - School Type FAQs"

#City+District+Co-ed+Is Popular Model

class CityDistrictCoedFaq(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    STATUS = (("Draft", "Draft Faq"), ("Published", "Published Faq"))
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    SCHOOL_CATEGORY = (("Girls", "Girls"), ("Boys", "Boys"), ("Coed", "Coed"))
    city = models.ForeignKey("schools.City",on_delete=models.SET_NULL,null=True,blank=True)
    district = models.ForeignKey("schools.District",on_delete=models.SET_NULL,null=True,blank=True)
    school_category = models.CharField(max_length=10,choices=SCHOOL_CATEGORY,null=True,blank=True,default="Coed")
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    faq_answer = models.TextField(null=True,blank=True)
    title=models.CharField(max_length=100,null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.district} - {self.is_popular} -{self.school_category}"

    class Meta:
        verbose_name = "City / District - Coed FAQ"
        verbose_name_plural = "City / District - Coed FAQs"

#City+District+Grade+Is Popular Model

class CityDistrictGradeFaq(models.Model):
    OPTIONS = (("Yes", "Yes"), ("No", "No"))
    STATUS = (("Draft", "Draft Faq"), ("Published", "Published Faq"))
    status = models.CharField(max_length=15, choices=STATUS, null=True, blank=True, default="Draft")
    city = models.ForeignKey("schools.City",on_delete=models.SET_NULL,null=True,blank=True)
    district = models.ForeignKey("schools.District",on_delete=models.SET_NULL,null=True,blank=True)
    grade = models.ForeignKey("schools.SchoolClasses", on_delete=models.SET_NULL,null=True,blank=True)
    is_popular = models.CharField(max_length=15, choices=OPTIONS, null=True, blank=True, default="No")
    faq_answer = models.TextField(null=True,blank=True)
    title=models.CharField(max_length=100,null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.district} - {self.is_popular}- {self.grade}"

    class Meta:
        verbose_name = "City / District - Grade FAQ"
        verbose_name_plural = "City / District - Grade FAQs"
