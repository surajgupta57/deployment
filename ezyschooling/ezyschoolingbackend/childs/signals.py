from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from admission_forms.models import (CommonRegistrationForm)
from schools.models import SchoolClasses

from .models import Child


# @receiver(post_save, sender=Child)
def create_admission_form(sender, instance, created, **kwargs):
    if created:
        CommonRegistrationForm.objects.get_or_create(
            user=instance.user, child=instance)


@receiver(pre_save, sender=Child)
def update_fields(sender, instance, **kwargs):
    if instance.id is not None:
        previous = Child.objects.get(id=instance.id)
    if instance.class_applying_for is None:
        instance.class_applying_for = SchoolClasses.objects.first()
    if instance.id is not None:
        try:
            if (instance.gender != previous.gender) and (instance.gender == "male"):
                instance.child_admission_forms.first_girl_child = False
                instance.child_admission_forms.save()
            if (instance.gender != previous.gender) and (instance.gender == "female") and (instance.child_admission_forms.first_child):
                instance.child_admission_forms.first_girl_child = True
                instance.child_admission_forms.save()
        except:
            pass

@receiver(pre_save, sender=Child)
def update_cart_items(sender, instance, **kwargs):
    if instance.id is not None:
        previous = Child.objects.get(id=instance.id)
        if (previous.class_applying_for != instance.class_applying_for) and (instance.class_applying_for is not None):
            cart_items = instance.child_cart.select_related(
                "school").only("school").all()
            for item in cart_items:
                if item.school.admmissionopenclasses_set.filter(class_relation=instance.class_applying_for).exists():
                    if item.school.agecriteria_set.filter(class_relation=instance.class_applying_for).exists():
                        if not item.school.agecriteria_set.filter(class_relation=instance.class_applying_for, start_date__lte=instance.date_of_birth, end_date__gte=instance.date_of_birth).exists():
                            item.delete()
                    else:
                        pass
                else:
                    item.delete()
        if (previous.date_of_birth != instance.date_of_birth) and (instance.date_of_birth is not None):
            cart_items = instance.child_cart.select_related("school").only("school").all()
            for item in cart_items:
                if item.school.agecriteria_set.filter(class_relation=instance.class_applying_for).exists():
                    if not item.school.agecriteria_set.filter(class_relation=instance.class_applying_for, start_date__lte=instance.date_of_birth, end_date__gte=instance.date_of_birth).exists():
                        item.delete()
                else:
                    pass
