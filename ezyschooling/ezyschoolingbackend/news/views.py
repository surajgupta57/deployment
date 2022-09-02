from django.contrib import messages
from django.contrib.admin import site
from django.shortcuts import redirect, render
from django.db.models import Count, F
from django.utils import timezone

from .forms import NewsEmailDashboardForm
from .models import *
from .tasks import send_weekly_news_bulk_email, send_weekly_news_email


def news_email_dashboard(request):
    if request.method == 'POST':
        form = NewsEmailDashboardForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            news = list(data["news"].values_list("id", flat=True))
            if data["send_all"]:
                send_weekly_news_bulk_email.delay(
                    data["subject"], data["preview"], news)
                messages.success(
                    request, f"Mails will be sent to all users shortly.")
                return redirect("news_email_dashboard")
            else:
                recipient = data["recipient"]
                send_weekly_news_email.delay(
                    data["subject"], data["preview"], news, recipient)
                messages.success(
                    request, f"Mail was sent to {recipient} successfully.")
                return redirect("news_email_dashboard")
    else:
        start_date = timezone.now().date() - timezone.timedelta(days=7)
        end_date = timezone.now().date()
        news = list(News.objects.filter(status=News.PUBLISHED, timestamp__date__range=(start_date, end_date)).order_by(
            "-timestamp").annotate(views_count=F("views")+Count("visits")).order_by("-views_count").values_list("id", flat=True)[:5])
        form = NewsEmailDashboardForm(initial={"news": news})
    context = {
        'is_popup': False,
        'has_permission': True,
        'form': form,
        'opts': News._meta,
        'site_title': site.site_title,
        'site_header': site.site_header,
    }
    return render(request, 'news/email_dashboard.html', context)
