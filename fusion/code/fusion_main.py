####################
### CERTH Drakoulis
####################

from configargparse import ArgumentParser
import argparse
import time
import datetime
import json
import os
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import psutil

ToolId = 'LOC-FUSION'
PublishingTopic = 'fromtool-' + ToolId.lower()
DebugTopic = 'internal-comms-fusion-debug'
sourceID = None
TIME_WINDOW = None
GAL_QUAL = None
VIS_QUAL = None
INE_QUAL = None
LAST_GAL_MSG = None
LAST_GAL_T = None
LAST_VIS_MSG = None
LAST_VIS_T = None
LAST_INE_MSG = None
LAST_INE_T = None
USE_GAL = None
USE_VIS = None
USE_INE = None
PREVIOUSLY_EMITTED_T = None
EMITTED_MSG_COUNT = 0

def make_json_new(toolID, category, type, startTS, latitude=None, longitude=None, heading=None, altitude=None, mounting=None, quality=None, qualityHeading=None, outdoor=None, broadcast=True):
    json_msg= {}
    json_msg['toolID'] = toolID
    json_msg['broadcast'] = broadcast

    json_infopriopayload = {}
    json_infopriopayload['category'] = category
    json_infopriopayload['type'] = type
    json_infopriopayload['startTS'] = startTS

    json_tooldata={}
    if latitude != None: json_tooldata['latitude'] = float(latitude)
    if longitude != None: json_tooldata['longitude'] = float(longitude)
    if heading != None: json_tooldata['heading'] = float(heading)
    if altitude != None: json_tooldata['altitude'] = float(altitude)
    if mounting != None: json_tooldata['mounting'] = str(mounting)
    if quality != None: json_tooldata['quality'] = float(quality)
    if qualityHeading != None: json_tooldata['qualityHeading'] = float(qualityHeading)
    if outdoor != None: json_tooldata['outdoor'] = bool(outdoor)
    
    json_tooldata_list = [json_tooldata]
    json_infopriopayload['toolData'] = json_tooldata_list
    json_msg['infoprioPayload'] = json_infopriopayload
     
    return json.dumps(json_msg)

def on_receiving_info_msg(client, userdata, msg):
    global sourceID
    msg = msg.payload.decode()
    msg = json.loads(msg)
    if not msg['sourceID']==sourceID:
        sourceID = msg['sourceID']
        p = "*** Just got a new SourceID! Changing to " + sourceID + " ***"
        p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        client.publish(DebugTopic, p_json)
        print(p)

def on_receiving_dso_msg(client, userdata, msg):
    global sourceID
    global TIME_WINDOW
    global GAL_QUAL
    global VIS_QUAL
    global INE_QUAL
    global LAST_GAL_MSG
    global LAST_GAL_T 
    global LAST_VIS_MSG 
    global LAST_VIS_T 
    global LAST_INE_MSG 
    global LAST_INE_T
    global USE_GAL
    global USE_VIS 
    global USE_INE
    global PREVIOUSLY_EMITTED_T
    global EMITTED_MSG_COUNT

    t_now = time.time()
    msg = msg.payload.decode()
    msg = json.loads(msg)

    # fromdso messages allways have sourceID. If it is not for you, skip.
    if not msg['sourceID']==sourceID:
        if sourceID==None:
            p = "*** Waiting to get a sourceID... ***"
            p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            client.publish(DebugTopic, p_json)
            print(p)
        return

    if msg['toolID']=='LOC-GLT' and msg['infoprioPayload']['toolData'][0]['outdoor']==True:
        if USE_GAL==False:
            return
        LAST_GAL_MSG = msg
        LAST_GAL_T = t_now
    elif msg['toolID']=='LOC-SELF':
        if USE_VIS==False:
            return
        LAST_VIS_MSG = msg
        LAST_VIS_T = t_now
    elif msg['toolID']=='LOC-IBL':
        if USE_INE==False:
            return
        LAST_INE_MSG = msg
        LAST_INE_T = t_now

    if LAST_GAL_MSG != None and t_now - LAST_GAL_T > TIME_WINDOW:
        LAST_GAL_MSG = None
        LAST_GAL_T = None
    if LAST_VIS_MSG != None and t_now - LAST_VIS_T > TIME_WINDOW:
        LAST_VIS_MSG = None
        LAST_VIS_T = None
    if LAST_INE_MSG != None and t_now - LAST_INE_T > TIME_WINDOW:
        LAST_INE_MSG = None
        LAST_INE_T = None

    selected_msg = None
    selected_qual = None
    if LAST_GAL_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_GAL_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_GAL_T
        selected_msg = LAST_GAL_MSG
        selected_qual = GAL_QUAL
    elif LAST_VIS_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_VIS_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_VIS_T
        selected_msg = LAST_VIS_MSG
        selected_qual = VIS_QUAL
    elif LAST_INE_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_INE_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_INE_T
        selected_msg = LAST_INE_MSG
        selected_qual = INE_QUAL
    else:
        return

    out_msg = make_json_new(
            toolID=ToolId, \
            category='FusionLoc#FRLocation', \
            type='FusLocData', \
            startTS=datetime.datetime.utcnow().isoformat(), \
            latitude=selected_msg['infoprioPayload']['toolData'][0]['latitude'], \
            longitude=selected_msg['infoprioPayload']['toolData'][0]['longitude'], \
            heading=selected_msg['infoprioPayload']['toolData'][0]['heading'], \
            altitude=selected_msg['infoprioPayload']['toolData'][0]['altitude'], \
            quality=selected_qual)
    client.publish(PublishingTopic, out_msg)

    EMITTED_MSG_COUNT += 1
    p = "LOOP: " + str(EMITTED_MSG_COUNT) + " | LAT: " + str(selected_msg['infoprioPayload']['toolData'][0]['latitude']) + " | LON: " + str(selected_msg['infoprioPayload']['toolData'][0]['longitude']) + " | HEA: " + str(int(selected_msg['infoprioPayload']['toolData'][0]['heading'])) + " | ALT: " + str(int(selected_msg['infoprioPayload']['toolData'][0]['altitude'])) + " | QUA: " + str(selected_qual) + " | MS: " + str(int(1000*(time.time()-t_now))) + " | BAT: " + str(int(psutil.sensors_battery().percent))
    p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
    client.publish(DebugTopic, p_json)
    print(p)

def on_receiving_tool_msg(client, userdata, msg):
    global sourceID
    global TIME_WINDOW
    global GAL_QUAL
    global VIS_QUAL
    global INE_QUAL
    global LAST_GAL_MSG
    global LAST_GAL_T 
    global LAST_VIS_MSG 
    global LAST_VIS_T 
    global LAST_INE_MSG 
    global LAST_INE_T
    global USE_GAL
    global USE_VIS 
    global USE_INE
    global PREVIOUSLY_EMITTED_T
    global EMITTED_MSG_COUNT

    t_now = time.time()
    msg = msg.payload.decode()
    msg = json.loads(msg)

    # fromtool messages optionally have sourceID. If they do not have they are local.
    # If the message has sourceID and it is not for you, skip.
    try:
        if not msg['sourceID']==sourceID:
            if sourceID==None:
                p = "*** Waiting to get a sourceID... ***"
                p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                client.publish(DebugTopic, p_json)
                print(p)
            return
    except KeyError as e:
        pass

    if msg['toolID']=='LOC-GLT' and msg['infoprioPayload']['toolData'][0]['outdoor']==True:
        if USE_GAL==False:
            return
        LAST_GAL_MSG = msg
        LAST_GAL_T = t_now
    elif msg['toolID']=='LOC-SELF':
        if USE_VIS==False:
            return
        LAST_VIS_MSG = msg
        LAST_VIS_T = t_now
    elif msg['toolID']=='LOC-IBL':
        if USE_INE==False:
            return
        LAST_INE_MSG = msg
        LAST_INE_T = t_now

    if LAST_GAL_MSG != None and t_now - LAST_GAL_T > TIME_WINDOW:
        LAST_GAL_MSG = None
        LAST_GAL_T = None
    if LAST_VIS_MSG != None and t_now - LAST_VIS_T > TIME_WINDOW:
        LAST_VIS_MSG = None
        LAST_VIS_T = None
    if LAST_INE_MSG != None and t_now - LAST_INE_T > TIME_WINDOW:
        LAST_INE_MSG = None
        LAST_INE_T = None

    selected_msg = None
    selected_qual = None
    if LAST_GAL_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_GAL_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_GAL_T
        selected_msg = LAST_GAL_MSG
        selected_qual = GAL_QUAL
    elif LAST_VIS_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_VIS_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_VIS_T
        selected_msg = LAST_VIS_MSG
        selected_qual = VIS_QUAL
    elif LAST_INE_MSG != None:
        if PREVIOUSLY_EMITTED_T == LAST_INE_T:
            return
        PREVIOUSLY_EMITTED_T = LAST_INE_T
        selected_msg = LAST_INE_MSG
        selected_qual = INE_QUAL
    else:
        return

    out_msg = make_json_new(
            toolID=ToolId, \
            category='FusionLoc#FRLocation', \
            type='FusLocData', \
            startTS=datetime.datetime.utcnow().isoformat(), \
            latitude=selected_msg['infoprioPayload']['toolData'][0]['latitude'], \
            longitude=selected_msg['infoprioPayload']['toolData'][0]['longitude'], \
            heading=selected_msg['infoprioPayload']['toolData'][0]['heading'], \
            altitude=selected_msg['infoprioPayload']['toolData'][0]['altitude'], \
            quality=selected_qual)
    client.publish(PublishingTopic, out_msg)

    EMITTED_MSG_COUNT += 1
    p = "LOOP: " + str(EMITTED_MSG_COUNT) + " | LAT: " + str(selected_msg['infoprioPayload']['toolData'][0]['latitude']) + " | LON: " + str(selected_msg['infoprioPayload']['toolData'][0]['longitude']) + " | HEA: " + str(int(selected_msg['infoprioPayload']['toolData'][0]['heading'])) + " | ALT: " + str(int(selected_msg['infoprioPayload']['toolData'][0]['altitude'])) + " | QUA: " + str(selected_qual) + " | MS: " + str(int(1000*(time.time()-t_now))) + " | BAT: " + str(int(psutil.sensors_battery().percent))
    p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
    client.publish(DebugTopic, p_json)
    print(p)
    
def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == '__main__':
    script_name = os.path.basename(__file__)
    parser = ArgumentParser(description = script_name)
    parser.add_argument("--broker_ip", default="127.0.0.1", help="sets the IP address of the message broker")
    parser.add_argument("--time_window", type=float, default="2.0", help="how many seconds to retain and use tool messages")
    parser.add_argument("--gal_qual", type=int, default="100", help="Tool's quality value when using Gallileo")
    parser.add_argument("--vis_qual", type=int, default="80", help="Tool's quality value when using Visual loc")
    parser.add_argument("--ine_qual", type=int, default="60", help="Tool's quality value when using INERTIO")
    parser.add_argument("--use_gal", type=str2bool, default=True, help="Whether to use Gallileo")
    parser.add_argument("--use_vis", type=str2bool, default=True, help="Whether to use Visual loc")
    parser.add_argument("--use_ine", type=str2bool, default=True, help="Whether to use INERTIO")
    parser.add_argument("--from_tool", type=str2bool, default=True, help="If true, it will read from-tool topics and not from-dso")
    args = parser.parse_args()

    TIME_WINDOW = args.time_window
    GAL_QUAL = args.gal_qual
    VIS_QUAL = args.vis_qual
    INE_QUAL = args.ine_qual
    USE_GAL = args.use_gal
    USE_VIS = args.use_vis
    USE_INE = args.use_ine

    #simple_client = subscribe.simple('config-info', qos=0, retained=False, hostname=args.broker_ip)
    #config_info = simple_client.payload.decode()
    #sourceID = json.loads(config_info)['sourceID']
    info_client = mqtt.Client(ToolId + '-' + str(time.time()))
    info_client.connect(args.broker_ip)
    info_client.subscribe(topic='config-info', qos=0)
    info_client.on_message = on_receiving_info_msg
    info_client.loop_start()

    loc_client = mqtt.Client(ToolId + '-' + str(time.time()))
    loc_client.connect(args.broker_ip)
    
    if args.from_tool:
        loc_client.subscribe(topic='fromtool-loc-ibl', qos=0)
        loc_client.subscribe(topic='fromtool-loc-glt', qos=0)
        loc_client.subscribe(topic='fromtool-loc-self', qos=0)
        loc_client.on_message = on_receiving_tool_msg
    else:
        loc_client.subscribe(topic='fromdso-loc-ibl', qos=0)
        loc_client.subscribe(topic='fromdso-loc-glt', qos=0)
        loc_client.subscribe(topic='fromdso-loc-self', qos=0)
        loc_client.on_message = on_receiving_dso_msg

    loc_client.loop_start()
    while True:
        p = "*** Alive ***"
        p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        info_client.publish(DebugTopic, p_json)
        print(p)
        time.sleep(2*args.time_window)
        