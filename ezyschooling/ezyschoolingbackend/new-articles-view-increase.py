import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from articles.models import ExpertArticle
from news.models import News
import random

all_articles = ExpertArticle.objects.all()
all_news = News.objects.all()

for item in all_articles:
    if item.status == 'P':
        increasing_view_number = random.randint(254, 698)
        new_View = item.views + increasing_view_number
        item.views = new_View
        item.save()
        print("Published - Views Updated")
    else:
        item.views = 0
        item.save()
        print("Draft - Views Updated")

for item in all_news:
    if item.status == 'P':
        increasing_view_number = random.randint(254, 698)
        new_View = item.views + increasing_view_number
        item.views = new_View
        item.save()
        print("Published - Views Updated")
    else:
        item.views = 0
        item.save()
        print("Draft - Views Updated")
