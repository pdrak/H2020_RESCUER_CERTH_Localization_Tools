import paho.mqtt.client as mqtt
import json
from datetime import datetime, timedelta
import time
import threading
import numpy as np
import random

class messages():

    def __init__(self, lat = None, long = None, heading = None, dateandtime = datetime(2023, 5, 11, 12, 36, 57, 643401), 
                 PublishingTopic= "hi", json_msg = {}, brokerip = '127.0.0.1' , frid = 'FR003', ToolID = 'LOC-SELF', 
                 sourceid = "FR001#FR", quality = None, quality_heading = None, outdoor = None, mounting = None, altitude = None) -> None:
        #self.tool = tool
        self.brokerip = brokerip
        self.frid = frid
        self.ToolID = ToolID
        self.PublishingTopic = PublishingTopic
        self.json_msg = json_msg
        self.PublishingTopic= 'fromtool-'+ self.ToolID.lower()
        self.client = mqtt.Client(self.ToolID)
        self.sourceid = sourceid
        self.lat = lat
        self.long = long
        self.dateandtime = dateandtime
        self.quality = quality
        self.quality_heading = quality_heading
        self.outdoor = outdoor
        self.mounting = mounting
        self.heading = heading
        self.altitude = altitude
    

    def create_json(self):
       # brokerip= '192.168.100.12' 
        if self.ToolID == 'LOC-SELF':
            #ToolName ='Visual based self-Localization'
            category = "VisualSelfLoc#FRLocation"
            types = 'SelfLocData'


        elif self.ToolID == 'LOC-IBL':
            #ToolName ='Inertial-Based Localisation'
            category = "INERTIO#LocationUpdate"
            types = 'InrLocData'


        elif self.ToolID == 'LOC-GLT':
            #ToolName ='Galileo based Localization'
            category = "GalileoLoc#FRLocation"
            types = 'GalLocData'

        elif self.ToolID == 'LOC-FUSION':
            #ToolName ='Galileo based Localization'
            category = "FusionLoc#FRLocation"
            types = 'FusLocData'

        #ToolID ='LOC-SELF'
        #self.PublishingTopic= 'fromtool-'+ self.ToolID.lower()
            
        self.json_msg= {}
        #self.json_msg['toolName'] = ToolName
        self.json_msg['toolID'] = self.ToolID
        self.json_msg['sourceID'] = self.sourceid
        self.json_msg['broadcast'] = True
                
        json_infoprioPayload = {}
        json_infoprioPayload['category'] = category
        json_infoprioPayload['type'] = types
        self.dateandtime = self.dateandtime
        json_infoprioPayload['startTS'] = self.dateandtime.isoformat() 

        json_tooldata={}
        if self.lat != None: json_tooldata['latitude'] = self.lat
        if self.long != None: json_tooldata['longitude'] = self.long
        if self.heading != None: json_tooldata['heading'] = self.heading
        if self.altitude != None: json_tooldata['altitude'] = self.altitude
        if self.mounting != None: json_tooldata['mounting'] = self.mounting
        if self.quality != None: json_tooldata['quality'] = self.quality
        if self.quality_heading != None: json_tooldata['qualityHeading'] = self.quality_heading
        if self.outdoor != None: json_tooldata['outdoor'] = self.outdoor
        
        json_infoprioPayload['toolData'] =  [json_tooldata]    
        self.json_msg['infoprioPayload'] = json_infoprioPayload
        self.json_msg = json.dumps(self.json_msg) 
        return self.json_msg

    def threads_visual(self, visual_latitude, visual_longitude, visual_heading, visual_timediff, sourceid, brokerip):
        mqtt_visual = []
        mess_visual = []
        date_visual = self.dateandtime
        for i in range(len(visual_latitude)):
            mqtt_visual.append(messages(ToolID = 'LOC-SELF', lat = visual_latitude[i], long = visual_longitude[i], heading = visual_heading[i],
                                        altitude = 0, mounting = "helmet", dateandtime = date_visual, sourceid = sourceid, brokerip=brokerip))
            mess_visual.append([(mqtt_visual[i].create_json())])
            date_visual = date_visual + timedelta(seconds = visual_timediff)
        mess_visual = (mqtt_visual[0].PublishingTopic, mess_visual, visual_timediff)
        return mess_visual

########################################################################################

    def threads_inertio(self, inertio_latitude, inertio_longitude, inertio_heading, inertio_timediff, sourceid, brokerip):
        mqtt_inertio = []
        mess_inertio = []
        date_inertio = self.dateandtime
        for i in range(len(inertio_latitude)):
            mqtt_inertio.append(messages(ToolID = 'LOC-IBL', lat = inertio_latitude[i], long = inertio_longitude[i],  heading = inertio_heading[i],
                                         dateandtime = date_inertio, sourceid=sourceid, brokerip = brokerip,
                                         quality=0, altitude=0))
            mess_inertio.append([(mqtt_inertio[i].create_json())])
            date_inertio = date_inertio + timedelta(seconds = inertio_timediff)

        mess_inertio = (mqtt_inertio[0].PublishingTopic, mess_inertio, inertio_timediff)
        return mess_inertio

########################################################################################

    def threads_galileo(self, galileo_latitude, galileo_longitude, galileo_heading, galileo_timediff, sourceid, brokerip):
        mqtt_galileo = []
        mess_galileo = []
        date_galileo = self.dateandtime
        for i in range(len(galileo_latitude)):
            mqtt_galileo.append(messages(ToolID = 'LOC-GLT', lat = galileo_latitude[i], long = galileo_longitude[i], heading = galileo_heading[i],
                                         dateandtime = date_galileo, sourceid=sourceid, brokerip = brokerip,
                                         altitude = 0, quality=0, quality_heading = 0, outdoor=True, mounting = "helmet"))
            mess_galileo.append([(mqtt_galileo[i].create_json())])
            date_galileo = date_galileo + timedelta(seconds = galileo_timediff)
        mess_galileo = (mqtt_galileo[0].PublishingTopic, mess_galileo, galileo_timediff)
        return mess_galileo

########################################################################################

    def threads_fusion(self, fusion_latitude, fusion_longitude, fusion_heading, fusion_timediff, sourceid, brokerip):
        mqtt_fusion = []
        mess_fusion = []
        date_fusion = self.dateandtime
        for i in range(len(fusion_latitude)):
            mqtt_fusion.append(messages(ToolID = 'LOC-FUSION', lat = fusion_latitude[i], long = fusion_longitude[i], heading = fusion_heading[i],
                                         dateandtime = date_fusion, sourceid=sourceid, brokerip = brokerip,
                                         quality=0, altitude = 0))
            mess_fusion.append([(mqtt_fusion[i].create_json())])
            date_fusion = date_fusion + timedelta(seconds = fusion_timediff)
        mess_fusion = (mqtt_fusion[0].PublishingTopic, mess_fusion, fusion_timediff)
        return mess_fusion  


    def publish_messages_with_delay(self, topic, message_list, delay, progress):
        client = mqtt.Client(topic + str(random.randint(0, 2000000000)))
        client.connect(self.brokerip)
    
        for index in range(len(message_list)):
            message = message_list[index][0]
            progress[topic] = float(index+1) / len(message_list)
            t_begin = datetime.utcnow()
            #Change the value of startTS with the current time
            messtojson = json.loads(message)
            messtojson['infoprioPayload']['startTS'] = t_begin.isoformat() 
           # messtojson['infoprioPayload']['toolData']['heading'] = destination.get_bearing()
            message = json.dumps(messtojson)
            client.publish(topic, message, qos= 0)
            time.sleep(delay - (datetime.utcnow()-t_begin).seconds)

        client.disconnect()

    # Publish messages with delays using multiple timers
    def send_messages_with_progress(self, messages, progress_button, windowclass):
        print("Begun sending messages!")

        progress = {}

        for topic, message_list, delay in messages:
            timer = threading.Timer(0, self.publish_messages_with_delay, args=(topic, message_list, delay, progress))
            timer.start()

        min_progress = 0.0
        while min_progress < 1.0:
            progress_list = list(progress.values())
            min_progress = np.min(progress_list) if len(progress_list) > 0 else 0

            progress_button.configure(text= str(int(min_progress * 100)) + "%")
            windowclass.update()

        print("All messages published!")