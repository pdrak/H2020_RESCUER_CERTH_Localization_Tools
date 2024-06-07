import geopy.distance
from additional_functions import destination
import tkinter
import numpy as np

class wanted_marker():
        def __init__(self) -> None:
            self.d = 0
            self.l =[]
            self.new_marker_1 = []
            self.P1 = []
            self.heading = []

        def set_marker(self, dt, speed, noise, std):
        #I have already added two points on the map and want to print P1, which is the list points of interest
            if (len(self.new_marker_1)>=2) and (self.new_marker_1[-2][0] != 0) and (self.new_marker_1[-1][0] != 0):
                if speed == "":
                    tkinter.messagebox.showerror(title="", message="No speed selected. Please restart.")
                    assert (speed != ""), "No speed"
                else:
                    pass
                self.d = geopy.distance.geodesic(self.new_marker_1[-1], self.new_marker_1[-2]).meters
                if sum(self.l) > float(speed)*float(dt):
                    self.l = []
                    self.l.append(self.d)
                else:
                    self.l.append(self.d)
                if sum(self.l) < float(speed)*float(dt):
                    if self.P1 == []:
                        self.P1.append(self.new_marker_1[0])
                    self.d = sum(self.l)
                if sum(self.l) == float(speed)*float(dt):
                    self.l = []
                    self.P1.append(self.new_marker_1[-1])
                    self.d = 0
                while sum(self.l) > float(speed)*float(dt):
                    endiameso = destination(lat2 = self.new_marker_1[-1][0], long2 = self.new_marker_1[-1][1],
                                        lat1 = self.new_marker_1[-2][0], long1 = self.new_marker_1[-2][1],
                                        distance_meters = float(speed)*float(dt) - sum(self.l[:-1]))
                    self.new_marker_1.insert(-1, (float(endiameso.find_destination().split(",")[0]), float(endiameso.find_destination().split(",")[1])))
                    self.d = geopy.distance.geodesic(self.new_marker_1[-1], self.new_marker_1[-2]).meters
                    if self.P1 == []:
                        self.P1 = [self.new_marker_1[0]]
                        
                    self.P1.append((float(endiameso.find_destination().split(",")[0]), float(endiameso.find_destination().split(",")[1])))
                    self.l = [sum(self.l) - float(speed)*float(dt)]

            self.heading = []
            for i in range(len(self.P1)):
            #Noise on -> change the values of P1
                if noise == "on":
                    if std == "":
                        tkinter.messagebox.showerror(title="", message="No std selected. Please restart.")
                        assert (std != ""), "No speed"
                    noisy_point = destination(lat1 = self.P1[i][0], 
                                              long1 = self.P1[i][1], 
                                              distance_meters=np.random.normal(0,float(std)), 
                                              heading = np.random.uniform(0,360)).point_given_heading()
                    self.P1[i] = noisy_point
            #After having the P1 that we want (with or without noise doesn't matter) calculate the heading 
            for i in range(len(self.P1)):            
                if i == len(self.P1)-1:
                    heading = destination(lat1 = self.P1[len(self.P1)-2][0],  long1 = self.P1[len(self.P1)-2][1], lat2 = self.P1[len(self.P1)-1][0], long2 = self.P1[len(self.P1)-1][1]).get_bearing()
                    if heading >= 0:
                        pass
                    else:
                        heading = 360 + heading
                    self.heading.append(heading)
                else:
                    heading = destination(lat1 = self.P1[i][0],  long1 = self.P1[i][1], lat2 = self.P1[i+1][0], long2 = self.P1[i+1][1]).get_bearing()
                    if heading >= 0:
                        pass
                    else:
                        heading = 360 + heading
                    self.heading.append(heading)
                
            print("P1 = ", self.P1)
            print("heading = ", self.heading)
            return self.d, self.new_marker_1, self.P1, self.l, self.heading 
