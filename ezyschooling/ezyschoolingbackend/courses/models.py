from django.db import models


class CourseEnquiry(models.Model):
    parent_name = models.CharField(max_length=200)
    child_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=30)
    query = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Enquiry"
        verbose_name_plural = "Course Enquiries"

    def __str__(self):
        return self.child_name


class CourseEnrollment(models.Model):
    parent_name = models.CharField(max_length=200)
    child_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    address = models.TextField()
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"

    def __str__(self):
        return f"{self.child_name} - {self.course_name} - {self.class_name}"


class CourseTransaction(models.Model):
    payment_id = models.CharField(max_length=50, primary_key=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    method = models.CharField(max_length=50, blank=True, null=True)
    amount = models.IntegerField()
    card_id = models.CharField(max_length=50, blank=True, null=True)
    bank = models.CharField(max_length=50, blank=True, null=True)
    wallet = models.CharField(max_length=50, blank=True, null=True)
    order_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.IntegerField()
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Course Transaction"
        verbose_name_plural = "Course Transactions"
        ordering = ('-created_at',)

    def __str__(self):
        return self.payment_id


class CourseOrder(models.Model):
    enrollment = models.ForeignKey(
        "courses.CourseEnrollment", on_delete=models.SET_NULL, null=True)
    amount = models.IntegerField()
    order_id = models.CharField(max_length=50, db_index=True)
    payment = models.ForeignKey(
        "courses.CourseTransaction", blank=True, null=True, on_delete=models.CASCADE)
    signature = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Order"
        verbose_name_plural = "Course Orders"

    def __str__(self):
        return self.order_id


class CourseDemoClassRegistration(models.Model):
    parent_name = models.CharField(max_length=200)
    child_name = models.CharField(max_length=200)
    class_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Demo Class Regisration"
        verbose_name_plural = "Course Demo Class Regisrations"

    def __str__(self):
        return f"{self.child_name} - {self.class_name}"
