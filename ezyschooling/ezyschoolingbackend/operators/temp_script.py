from datetime import *
import googlemaps
from dateutil.relativedelta import relativedelta
import geopy.distance

GOOGLE_MAP_API_KEY='AIzaSyDdsg_M9CSP1MIO3N5cBRRakTKiXw68Ohs'

def get_distance(a, b):
    API_KEY = GOOGLE_MAP_API_KEY
    gmaps = googlemaps.Client(key=API_KEY)
    tomorrow = datetime.now().date() + relativedelta(days=1)
    dept_time = datetime.combine(tomorrow, time(3, 0))
    result = gmaps.distance_matrix(origins=a, destinations=[b], departure_time=dept_time)
    return result["rows"][0]["elements"][0]["distance"]["value"] / 1000

def get_aerial_distance(a,b):
    return geopy.distance.distance(a,b).km


a_latitude=input("input first latitude")
a_longitude = input("input first longitude")
b_latitude=input("input second latitude")
b_longitude = input("input second longitude")

#a_latitude=28.6110
#a_longitude = 77.2300
#b_latitude=19.076
#b_longitude =72.8774

coordinate1 = (a_latitude, a_longitude)
coordinate2 = (b_latitude, b_longitude)

print("normal distance is",get_distance(coordinate1,coordinate2))
print("distance is",get_aerial_distance(coordinate1,coordinate2))

