import os
import time
from configargparse import ArgumentParser
import paho.mqtt.client as mqtt
import json

ToolId = "Lazy-starter"
DebugTopic = 'internal-comms-self-debug'
sourceID = None
finished = False

def on_receiving_info_msg(client, userdata, msg):
    global sourceID
    msg = msg.payload.decode()
    msg = json.loads(msg)
    if not msg['sourceID']==sourceID:
        sourceID = msg['sourceID']
        p = "*** Lazy-starter got a new SourceID! Changing to " + sourceID + " ***"
        p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        client.publish(DebugTopic, p_json)
        print(p)

def on_receiving_android_msg(client, userdata, msg):
    global finished
    msg = msg.payload.decode()
    msg = json.loads(msg)
    if msg['sourceID']==sourceID and msg['QR']=="START":
        p = "*** RECEIVED START MESSAGE! CONTINUE... ***"
        p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        client.publish(DebugTopic, p_json)
        print(p)
        finished = True

def main(broker_ip):
    info_client = mqtt.Client(ToolId + '-' + str(time.time()))
    info_client.connect(broker_ip)
    info_client.subscribe(topic='config-info', qos=0)
    info_client.on_message = on_receiving_info_msg
    info_client.loop_start()

    android_client = mqtt.Client(ToolId + '-' + str(time.time()))
    android_client.connect(broker_ip)
    android_client.subscribe(topic='internal-comms-android-app', qos=0)
    android_client.on_message = on_receiving_android_msg
    android_client.loop_start()

    while not finished:
        p = "*** Lazy-starter WAITING FOR START MESSAGE ***"
        p_json = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        android_client.publish(DebugTopic, p_json)
        print(p)
        time.sleep(1)

if __name__ == "__main__":  
    script_name = os.path.basename(__file__)
    parser = ArgumentParser(description = script_name)
    parser.add_argument("--config", is_config_file=True, help="config file")
    parser.add_argument("--broker_ip", default="127.0.0.1", help="The broker to monitor for the START message")
    args = parser.parse_args()

    main(args.broker_ip)
