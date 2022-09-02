import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()
import googlemaps
from decouple import config
from schools.models import SchoolProfile,DistrictRegion
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

app = Nominatim(user_agent="Ezyschool",timeout=3)
data = SchoolProfile.objects.all().select_related('district_region','school_city').order_by('id')
for i in data:
    try:
        if i.school_city.slug =="boarding-school":
            name = f"{i.district_region.name}"
            if app.geocode(name):
                city_coordinates = app.geocode(name)
                school_coords = (i.latitude, i.longitude)
                if int(geodesic(city_coordinates, school_coords).km) > 50:
                    self.latitude = i.district_region.latitude
                    self.longitude = i.district_region.longitude
                else:
                    pass
        elif i.school_city.slug =="online-school":
            pass
        else:
            school_coords = (i.latitude, i.longitude)
            city_coardinates = app.geocode(i.city.name)
            # checking if calculated distance between city and school_coords is not more than 50kms
            if int(geodesic(city, school_coords).km) > 50:
                self.latitude = i.district_region.latitude
                self.longitude = i.district_region.longitude
            else:
                pass
    except:
        pass
