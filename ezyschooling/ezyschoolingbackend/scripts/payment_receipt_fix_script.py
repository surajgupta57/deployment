import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()

from admission_forms.models import *
from schools.models import *
from childs.models import *


## just need to input child_id
child_id=8772
child=Child.objects.get(pk=child_id)
form_id=CommonRegistrationForm.objects.get(user=child.user,child=child).id
carts_list = ChildSchoolCart.objects.filter(child__id=child_id)
for cart in carts_list:
    school_obj = SchoolProfile.objects.filter(id=cart.school.id).first()
    application = SchoolApplication.objects.create(child=child, school=school_obj, form_id=form_id, user=child.user, apply_for=child.class_applying_for)
    ChildSchoolCart.objects.filter(form__pk=form_id, school=school_obj).delete()
    FormReceipt.objects.create(school_applied=application, form_fee=cart.form_price, receipt_id=application.uid)
    if school_obj.collab:
        app_status,created = ApplicationStatus.objects.get_or_create(rank=1, type="C", name="Form Submitted")
    else:
        app_status,created = ApplicationStatus.objects.get_or_create(rank=1, type="N", name="Application received by Ezyschooling")
    ApplicationStatusLog.objects.create( application=application, status=app_status )
print("done")
