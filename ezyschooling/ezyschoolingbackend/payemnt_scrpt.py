import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.production")
django.setup()


from admission_forms.models import ChildSchoolCart, SchoolApplication
user = 60462
childs = ChildSchoolCart.objects.filter(user__id=user)

for child in childs:
    print(child)

print("----------------")
applicationsss = SchoolApplication.objects.filter(user__id=user)

for app in applicationsss:
    print(app)