import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from admission_forms.models import SchoolApplication, ChildSchoolCart
from accounts.models import User

if ChildSchoolCart.objects.filter(user__id=65936).exists():
    get_cart = ChildSchoolCart.objects.get(user__id=65936)
    print(get_cart.school.name)
    print("yes")
else:
    print("no")
