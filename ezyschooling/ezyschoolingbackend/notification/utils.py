from django.conf import settings

WebPushKey = settings.FIREBASE_WEBPUSH_KEY

from schools.models import City
from django.db.models import Q

def get_city_list_tuple():
    return [(0,'No City / All Users')] + list(City.objects.values_list("id",'name').exclude(Q(name__exact='Boarding Schools') | Q(name__exact='Dubai') | Q(name__exact='Online Schools')))
