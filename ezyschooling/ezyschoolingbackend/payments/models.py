from django.db import models


class FormTransaction(models.Model):
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
        ordering = ('-created_at',)

    def __str__(self):
        return self.payment_id


class FormOrder(models.Model):
    child = models.ForeignKey(
        "childs.Child", related_name="transaction_order", on_delete=models.CASCADE)
    amount = models.IntegerField()
    order_id = models.CharField(max_length=50, db_index=True)
    payment_id = models.ForeignKey(
        "payments.FormTransaction", blank=True, null=True, on_delete=models.CASCADE)
    signature = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.order_id

class AdmissionGuidanceProgrammeFormTransaction(models.Model):
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
        ordering = ('-created_at',)

    def __str__(self):
        return self.payment_id

class AdmissionGuidanceProgrammeFormOrder(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    amount = models.IntegerField()
    order_id = models.CharField(max_length=50, db_index=True)
    payment_id = models.ForeignKey(
        "payments.AdmissionGuidanceProgrammeFormTransaction", blank=True, null=True, on_delete=models.CASCADE)
    signature = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.order_id


class AdmissionGuidanceFormTransaction(models.Model):
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
        ordering = ('-created_at',)

    def __str__(self):
        return self.payment_id

class AdmissionGuidanceFormOrder(models.Model):
    person = models.ForeignKey(
        "miscs.AdmissionGuidance", related_name="transaction_order", on_delete=models.CASCADE)
    amount = models.IntegerField()
    order_id = models.CharField(max_length=50, db_index=True)
    payment_id = models.ForeignKey(
        "payments.AdmissionGuidanceFormTransaction", blank=True, null=True, on_delete=models.CASCADE)
    signature = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.order_id

""" School settelment Accounts related to Model """
class SchoolSettlementAccounts(models.Model):
    school =models.OneToOneField("schools.SchoolProfile",
        related_name="settelment_accounts",on_delete=models.DO_NOTHING,null=True,blank=True)
    razorpay_account_id = models.CharField(max_length=120,null=True,blank=True)

"""Transfer of school settelment amount to a particular school  related Details  Model """

class SchoolTransferDetail(models.Model):
    school =models.ForeignKey("schools.SchoolProfile",
        related_name="school_transfer_detail",on_delete=models.DO_NOTHING,null=True,blank=True)
    transfer_id = models.CharField(max_length=100,null=True,blank=True)
    recipient = models.CharField(max_length=100,null=True,blank=True)
    amount= models.FloatField(null=True,blank=True,default=0)
    notes = models.TextField(max_length=100,null=True,blank=True)
    payment_done_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)