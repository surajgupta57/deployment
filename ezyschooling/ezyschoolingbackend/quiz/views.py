from django.contrib import messages
from django.contrib.admin import site
from django.shortcuts import redirect, render

from .forms import QuizEmailDashboardForm
from .tasks import send_quiz_email, send_bulk_quiz_email
from .models import *


def quiz_email_dashboard(request):
    if request.method == 'POST':
        form = QuizEmailDashboardForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            quizzes = list(data["quizzes"].values_list("id", flat=True))
            if data["send_all"]:
                send_bulk_quiz_email.delay(data["subject"], data["preview"], quizzes)
                messages.success(
                    request, f"Mails will be sent to all users shortly.")
                return redirect("quiz_email_dashboard")
            else:
                recipient = data["recipient"]
                send_quiz_email.delay(data["subject"], data["preview"], quizzes, recipient)
                messages.success(
                    request, f"Mail was sent to {recipient} successfully.")
                return redirect("quiz_email_dashboard")
    else:
        form = QuizEmailDashboardForm()
    context = {
        'is_popup': False,
        'has_permission': True,
        'form': form,
        'opts': Quiz._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'quiz/email_dashboard.html', context)
