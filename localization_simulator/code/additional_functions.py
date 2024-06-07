from geopy.distance import geodesic
from geopy import Point
import numpy as np
import math

class destination:
    def __init__(self, lat1 = 0, lat2 = 0, long1 = 0, long2 = 0, distance_meters = 1, heading = 0):
        self.lat1 = lat1
        self.lat2 = lat2
        self.long1 = long1
        self.long2 = long2
        self.distance_meters = distance_meters
        self.heading = heading

    def get_bearing(self):
        dLon = (self.long2 - self.long1)
        x = math.cos(math.radians(self.lat2)) * math.sin(math.radians(dLon))
        y = math.cos(math.radians(self.lat1)) * math.sin(math.radians(self.lat2)) - math.sin(math.radians(self.lat1)) * math.cos(math.radians(self.lat2)) * math.cos(math.radians(dLon))
        brng = np.arctan2(x,y)
        brng = np.degrees(brng)
        return brng

    def find_destination(self):
        coords = geodesic(meters=self.distance_meters).destination(Point(self.lat1, self.long1), self.get_bearing()).format_decimal()
        return coords #(float(coords.split(",")[0]) , float(coords.split(",")[1]))
    

    def point_given_heading(self):
        coords = geodesic(meters=self.distance_meters).destination(Point(self.lat1, self.long1), self.heading).format_decimal()
        return tuple(float(i) for i in coords.split(','))      
