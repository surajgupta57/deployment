from django.shortcuts import redirect, render
from .models import SchoolEqnuirySource
from.forms import AddNewIDForm
from django.contrib.admin import site
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
# Create your views here.

def get_user_permission_status(user):
    if user.is_authenticated and user.is_superuser:
        return True
    elif user.is_authenticated:
        ct = ContentType.objects.get_for_model(SchoolEqnuirySource)
        perm_name = ["add_schooleqnuirysource","add_shooleqnuirysource"]
        if Permission.objects.filter(user=user,content_type=ct,codename__in=perm_name).exists():
            return True
        return False


def add_new_tracking_id_dashboard(request):
    if request.method == "POST":
        form = AddNewIDForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                allowed = get_user_permission_status(request.user)
                if allowed:
                    SchoolEqnuirySource.objects.create(source_name=data["title"])
                    messages.success(request, f"Source added successfully.")
                else:
                    messages.warning(request, f"You don't have permissions to perfome this action")
            except Exception as e:
                messages.warning(request, f"Something went wrong: {e}")
            return redirect('/admin/schools/schooleqnuirysource/')
    else:
        form = AddNewIDForm()
    context = {
        "form": form,
        'opts': SchoolEqnuirySource._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'schools/add_new_tracking_id.html', context)
