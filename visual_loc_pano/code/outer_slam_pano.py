#################################
### CERTH Drakoulis, Karavarsamis
### To function it NEEDS the 3 calibration points (both in GPS and local coordinates) to NOT be on a straight line! Else it will cause a linalg exception.
#################################

import time
import sys
import datetime
import os
from configargparse import ArgumentParser
import argparse
import pprint
import numpy as np
import numpy.linalg as npl
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import errno
import math
import logging
import datetime
import json
import socket
from PIL import Image
from pyzbar.pyzbar import decode
import base64
import cv2
from Equirec2Perspec import Equirectangular
from pynput import keyboard
from geopy.distance import geodesic as GD
from geographiclib.geodesic import Geodesic
import psutil
import lazy_start

# Global variables
found = False
qr = None
client = None
ToolId = 'LOC-SELF' 
PublishingTopic = 'fromtool-' + ToolId.lower()
DebugTopic = 'internal-comms-self-debug'
sourceID = None

def setup_logger(name : str, save_dir : bool, filename : str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    
    if save_dir:
        fh = logging.FileHandler(os.path.join(save_dir, filename))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        logger.addHandler(fh)
    
    return logger

def mkdir(path : str):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST: raise ValueError("Invalid output path!")

def time_from(start_time, description, logger, debug=True):
    global client

    end_time = time.time() - start_time
    delta_str = str(datetime.timedelta(seconds=end_time))
    
    if debug:
        p = "\n" + description + ": " + delta_str
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)
       
    return end_time

def detect_QR_perspec(equ):
    global client
    results = []
    found = False

    im = Image.fromarray(np.uint8(equ))
    b, g, r = im.split()
    im = Image.merge("RGB", (r, g, b))

    #im.save('qrcode_theta_%d_phi_%d.png' % (theta,phi))
    ret = decode(im)
    
    if ret == []:
        return (False,None)

    for barcode in ret:
        myData = barcode.data.decode("utf-8")
        results.append((-1,-1,myData))
        found = True
        break

    if found == True:
        if results[0][2] == "1":
            p = "\nFOUND QR1!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

        elif results[0][2] == "2":
            p = "\nFOUND QR2!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

        elif results[0][2] == "3":
            p = "\nFOUND QR3!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

        return (True,results[0][2])
    
    return (False,None)

def detect_QR(equ):
    global client
    results = []
    found = False

    thetaphis = [(-90,0),(0,-180),(0,-90),(0,0),(0,90),(90,0)] # cuboid decomposition

    for thetaphi in thetaphis:
        theta = thetaphi[0]
        phi = thetaphi[1]

        if found == True:
            if results[0][2] == "1":
                p = "\nFOUND QR1!"
                print(p)
                logger.info(p)
                p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                if client: client.publish(DebugTopic, p_intnl)

            elif results[0][2] == "2":
                p = "\nFOUND QR2!"
                print(p)
                logger.info(p)
                p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                if client: client.publish(DebugTopic, p_intnl)

            elif results[0][2] == "3":
                p = "\nFOUND QR3!"
                print(p)
                logger.info(p)
                p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                if client: client.publish(DebugTopic, p_intnl)

            return (True,results[0][2])

        img = equ.GetPerspective(90, theta, phi, 512, 512) # Specify parameters(FOV, theta, phi, height, width)
        im = Image.fromarray(np.uint8(img))
        b, g, r = im.split()
        im = Image.merge("RGB", (r, g, b))

        #im.save('qrcode_theta_%d_phi_%d.png' % (theta,phi))

        ret = decode(img)
        if ret  == []:
            continue

        for barcode in ret:
            myData = barcode.data.decode("utf-8")
            results.append((theta,phi,myData))
            found = True
            break

    return (False,None)

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

def xy2latlon(qLL, QR1, QR2, QR3, QR1_c, QR2_c, QR3_c):
    L = np.matrix([[QR1[0], QR2[0], QR3[0]],[QR1[1], QR2[1], QR3[1]],[1, 1, 1]])
    C = np.matrix([[QR1_c[0], QR2_c[0], QR3_c[0]],[QR1_c[1], QR2_c[1], QR3_c[1]],[1, 1, 1]])
    T = C*npl.inv(L)
    Tinv = npl.inv(T)
    qLL_T = Tinv * np.matrix([qLL[0],qLL[1],1]).T
    return float(qLL_T[0]), float(qLL_T[1]) # lat, lon

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

def on_receiving_qr_msg(client, userdata, msg):
    global found
    global qr

    msg  = msg.payload.decode()
    msg = json.loads(msg)

    if not msg["sourceID"] == sourceID:
        return
   
    if msg["QR"] == "1":
        found = True
        qr = "1"
        p = "\nFOUND QR1!"
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)

    elif msg["QR"] == "2":
        found = True
        qr = "2"
        p = "\nFOUND QR2!"
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)

    elif msg["QR"] == "3":
        found = True
        qr = "3"
        p = "\nFOUND QR3!"
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)

def on_press(key):
    global client
    global found
    global qr

    try:
        if key.char == "1":
            found = True
            qr = "1"
            p = "\nFOUND QR1!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

        elif key.char == "2":
            found = True
            qr = "2"
            p = "\nFOUND QR2!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

        elif key.char == "3":
            found = True
            qr = "3"
            p = "\nFOUND QR3!"
            print(p)
            logger.info(p)
            p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
            if client: client.publish(DebugTopic, p_intnl)

    except AttributeError:
        p = 'special key {0} pressed'.format(key)
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":  
    # Parse arguments
    script_name = os.path.basename(__file__)
    parser = ArgumentParser(description = script_name)
    parser.add_argument("--config", is_config_file=True, help="config file")
    parser.add_argument("--from_vs_code", action="store_true", help="flag so that the script knows it is called in vscode and not docker")
    parser.add_argument("--debug", action="store_true", help="save various intermediate files")
    parser.add_argument("--output_dir", required=True, help="path where to save output files")
    parser.add_argument("--broker_ip", help="If it exists, sends results to broker")
    parser.add_argument("--host_ip", help="IP address of the local machine (i.e., Ethernet/WiFi)")
    parser.add_argument("--camera_ip", default="172.21.134.51", help="sets the IP address of the GoPro HERO 10")
    parser.add_argument("--hero_port", default="8554", help="sets the port of the camera")
    parser.add_argument("--forward_port_1", default="8555", help="sets the number of the first forwarded port")
    parser.add_argument("--forward_port_2", default="8556", help="sets the number of the second forwarded port")
    parser.add_argument("--cmds", default="stop,start", help="sets the HTTP commands to be submitted")
    parser.add_argument("--which_camera", default="max", help="select which camera to use: GoPro MAX ('max') or GoPro Hero 10 ('hero')")
    parser.add_argument("--socket_path", default="", help="path to unix-domain socket")
    parser.add_argument("--stella_lib_path", default="test", help="path to stella built lib. REQUIRED if from_vs_code==True")
    parser.add_argument("--map", help="path to stella pre-scanned map")
    parser.add_argument("--create_map", action="store_true", help="map area and save it at map path")
    parser.add_argument("--calibrated", help="path to local points calibration file")
    parser.add_argument("--cap_fps", default=2.0, type=float, help="qr coordinates")
    parser.add_argument("--camera_port", default="8556", help="default port number for the GoPro HERO 10 camera")
    parser.add_argument("--qr1_lat", required=True, type=float, help="qr 1 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr1_lon", required=True, type=float, help="qr 1 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr1_alt", default=0, type=float, help="qr 1 altitude")
    parser.add_argument("--qr2_lat", required=True, type=float, help="qr 2 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr2_lon", required=True, type=float, help="qr 2 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr2_alt", default=0, type=float, help="qr 2 altitude")
    parser.add_argument("--qr3_lat", required=True, type=float, help="qr 3 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr3_lon", required=True, type=float, help="qr 3 coordinates. The 3 points chosen MUST not be on the same straight line and be different!")
    parser.add_argument("--qr3_alt", default=0, type=float, help="qr 3 altitude")
    parser.add_argument("--glt_calib", type=str2bool, default=False, help="Wether to use the output of Galileo localization to calibrate.")
    parser.add_argument("--lazy_start", type=str2bool, default=False, help="Wether to wait for a START QR code from the Android app to begin stella. Works only when run inside VS.")
    args = parser.parse_args()
    
    # Initial arrangements
    pwd = os.path.dirname(args.socket_path)
    socket_file = os.path.basename(args.socket_path)
    if not os.path.exists(os.path.join(pwd, ".SendImage")):
        # Oso yparxei to .SendImage to c++ code tou Stella, stelnei kai tin eikona.
        open(os.path.join(pwd, ".SendImage"), "w").close()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()  
    local_point1 = None
    local_point2 = None
    local_point3 = None
    if args.map and args.calibrated:
        with open(args.calibrated) as f:
            lines = f.readlines()
            local_point1 = (float(lines[0].split(',')[0]), float(lines[0].split(',')[1]))
            local_point2 = (float(lines[1].split(',')[0]), float(lines[1].split(',')[1]))
            local_point3 = (float(lines[2].split(',')[0]), float(lines[2].split(',')[1]))
            args.qr1_lat, args.qr1_lon, args.qr1_alt = (float(lines[3].split(',')[0]), float(lines[3].split(',')[1]), float(lines[3].split(',')[2]))
            args.qr2_lat, args.qr2_lon, args.qr2_alt = (float(lines[4].split(',')[0]), float(lines[4].split(',')[1]), float(lines[4].split(',')[2]))
            args.qr3_lat, args.qr3_lon, args.qr3_alt = (float(lines[5].split(',')[0]), float(lines[5].split(',')[1]), float(lines[5].split(',')[2]))

    # Executed in vscode only code
    if args.from_vs_code:

        if args.lazy_start:
            lazy_start.main(args.broker_ip)

        if os.path.exists('/tmp/.LOCK_FILE'):
            os.remove('/tmp/.LOCK_FILE')
        if os.path.exists(args.socket_path):
            os.remove(args.socket_path)

        import subprocess
        os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH'] + ":" + args.stella_lib_path
        if not args.map:
            # linux_one_shot
            if args.which_camera == "max":
                subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/aist/equirectangular.yaml -P 0.0 -d 1 -M -H 10.5.5.9 -p 8554 -S " + args.socket_path, cwd=pwd, shell=True)
            
            elif args.which_camera == "hero":
                subprocess.Popen("python3 ../../code/proxycam.py --host_ip " + args.host_ip + " --camera_ip " + args.camera_ip + " --camera_port " + args.hero_port + " --forward_port_1 " + args.forward_port_1 + " --forward_port_2 " + args.forward_port_2 + " --cmds " + args.cmds, cwd=pwd, shell=True)
                time.sleep(3)
                subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/rescuer/calib_360.yaml -P 0.0 -d 1 -W -H 172.21.134.51 -p 8555 -S " + args.socket_path, cwd=pwd, shell=True)
        else:
            if not args.create_map:
                #linux_use_map & linux_use_map_calibrated
                if args.which_camera == "max":
                    subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/aist/equirectangular.yaml -P 0.0 -d 1 -M -H 10.5.5.9 -p 8554 -S " + args.socket_path + " --disable-mapping --map-db-in " + args.map, cwd=pwd, shell=True)

                elif args.which_camera == "hero":
                    subprocess.Popen("python3 ../../code/proxycam.py --host_ip " + args.host_ip + " --camera_ip " + args.camera_ip + " --camera_port " + args.hero_port + " --forward_port_1 " + args.forward_port_1 + " --forward_port_2 " + args.forward_port_2 + " --cmds " + args.cmds, cwd=pwd, shell=True)
                    time.sleep(3)
                    subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/rescuer/calib_360.yaml -P 0.0 -d 1 -W -H 172.21.134.51 -p 8555 -S " + args.socket_path + " --disable-mapping --map-db-in " + args.map, cwd=pwd, shell=True)
            else:
                #linux_map
                if args.which_camera == "max":
                    subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/aist/equirectangular.yaml -P 0.0 -d 1 -M -H 10.5.5.9 -p 8554 -S " + args.socket_path + " --map-db-out " + args.map, cwd=pwd, shell=True)

                elif args.which_camera == "hero":
                    subprocess.Popen("python3 ../../code/proxycam.py --host_ip " + args.host_ip + " --camera_ip " + args.camera_ip + " --camera_port " + args.hero_port + " --forward_port_1 " + args.forward_port_1 + " --forward_port_2 " + args.forward_port_2 + " --cmds " + args.cmds, cwd=pwd, shell=True)
                    time.sleep(3)
                    subprocess.Popen("python3 ../../code/run_readcamera_poses.py --socket_path " + socket_file, cwd=pwd, shell=True)
                    subprocess.Popen("./run_camera_slam -V 1 -v ./orb_vocab.fbow -G 0 -n 0 -c ../example/rescuer/calib_360.yaml -P 0.0 -d 1 -W -H 172.21.134.51 -p 8556 -S " + args.socket_path + " --map-db-out " + args.map, cwd=pwd, shell=True)
        
                time.sleep(4000000000) # wait you to scan the area and push the gui button of pangolin to save the file

    # Start logging
    if args.output_dir: mkdir(args.output_dir)
    logger = setup_logger(name = "logger", save_dir = args.output_dir, filename = script_name + ".log")
    p = "\nSTART."
    print(p)
    logger.info(p)
    p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
    if client: client.publish(DebugTopic, p_intnl)

    p = "\nArguments:{}".format(pprint.pformat(args.__dict__))
    print(p)
    logger.info(p)
    p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
    if client: client.publish(DebugTopic, p_intnl)

    # Connect to broker
    if args.broker_ip:
        t4 = time.time()
        info_client = mqtt.Client(ToolId + '-' + str(time.time()))
        info_client.connect(args.broker_ip)
        info_client.subscribe(topic='config-info', qos=0)
        info_client.on_message = on_receiving_info_msg
        info_client.loop_start()
        client = mqtt.Client(ToolId + '-' + str(time.time()))
        client.connect(args.broker_ip)
        client.subscribe(topic='internal-comms-android-app', qos=0)
        client.on_message = on_receiving_qr_msg
        client.loop_start()      
        time_from(t4, "CONNECTED TO BROKER", logger, args.debug)

    # Connection to camera
    t3 = time.time()
    while True: # poll lockfile before attempting to sock.connect()
        p = "\nWaiting Stella to begin..."
        print(p)
        logger.info(p)
        p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
        if client: client.publish(DebugTopic, p_intnl)
        if not os.path.exists("/tmp/.LOCK_FILE"):
            time.sleep(0.125)
        else:
            break
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(args.socket_path)
    time_from(t3, "CONNECTED TO CAMERA SOCKET (FD=" + str(sock.fileno()) + ")", logger, args.debug)

    # Core loop
    frame_count = 1
    previous_lat_lon = (args.qr3_lat, args.qr3_lon)
    previous_lat_lon_time = time.time()
    total_distance_m = 0.0
    speed = 0.0
    hea = 0.0
    dist = 0.0
    scale_loc2met = 0.0

    while True:
        t0 = time.time()
        circ_buff = ""
        idx_start = -1
        idx_end = -1

        # Read from camera socket
        data = sock.recv(3000000)
        if len(data) == 0:
            sys.exit(0)

        # Get matrix values
        data = data.decode('utf-8')
        circ_buff += data
        idx_start = circ_buff.rfind('--START-BUF--')
        idx_end = circ_buff.rfind('--END-BUF--')
        if idx_start == -1 or idx_end == -1:
            continue
        if circ_buff[idx_start:idx_end+len('--END-BUF--')] == "":
            continue
        tokens = circ_buff[idx_start+len('--START-BUF--'):idx_end].split(',')
        nums = [float(x) for x in tokens[0:16]]

        # Get image - calibration mode
        calibrating = False
        if len(tokens) == 17:
            calibrating = True
            image_b64 = tokens[16][:-1] # trim /n at the end
            bin_data = base64.b64decode(image_b64)
            img_arr = np.asarray(bytearray(bin_data), dtype=np.uint8)
            img_cv2 = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

            equ = None
            if args.which_camera == 'hero':
                equ = img_cv2
            elif args.which_camera == 'max':
                equ = Equirectangular(img_cv2)

            if not found:
                if args.which_camera == 'hero':
                    found, qr = detect_QR_perspec(equ)
                elif args.which_camera == 'max':
                    found, qr = detect_QR(equ)

            if found and qr == "1":
                local_point1 = (nums[3], nums[11])
                if args.glt_calib:
                    more = True
                    while(more): # Filter glt messages by sourceID
                        glt_msg = json.loads(subscribe.simple(topics="fromtool-loc-glt", hostname=args.broker_ip).payload.decode())
                        try:
                            if glt_msg['sourceID']==sourceID: # if it has sourceID and is yours accept it
                                more = False
                        except KeyError as e: # if it does not have sourceID is local/yours, so accept it
                            more = False
                    args.qr1_lat = float(glt_msg['infoprioPayload']['toolData'][0]['latitude'])
                    args.qr1_lon = float(glt_msg['infoprioPayload']['toolData'][0]['longitude'])
                    args.qr1_alt = float(glt_msg['infoprioPayload']['toolData'][0]['altitude'])
                found = False
                qr = None
            elif found and qr == "2":
                local_point2 = (nums[3], nums[11])
                if args.glt_calib:
                    more = True
                    while(more): # Filter glt messages by sourceID
                        glt_msg = json.loads(subscribe.simple(topics="fromtool-loc-glt", hostname=args.broker_ip).payload.decode())
                        try:
                            if glt_msg['sourceID']==sourceID: # if it has sourceID and is yours accept it
                                more = False
                        except KeyError as e: # if it does not have sourceID is local/yours, so accept it
                            more = False
                    args.qr2_lat = float(glt_msg['infoprioPayload']['toolData'][0]['latitude'])
                    args.qr2_lon = float(glt_msg['infoprioPayload']['toolData'][0]['longitude'])
                    args.qr2_alt = float(glt_msg['infoprioPayload']['toolData'][0]['altitude'])
                found = False
                qr = None
            elif found and qr == "3":
                local_point3 = (nums[3], nums[11])
                if args.glt_calib:
                    more = True
                    while(more): # Filter glt messages by sourceID
                        glt_msg = json.loads(subscribe.simple(topics="fromtool-loc-glt", hostname=args.broker_ip).payload.decode())
                        try:
                            if glt_msg['sourceID']==sourceID: # if it has sourceID and is yours accept it
                                more = False
                        except KeyError as e: # if it does not have sourceID is local/yours, so accept it
                            more = False
                    args.qr3_lat = float(glt_msg['infoprioPayload']['toolData'][0]['latitude'])
                    args.qr3_lon = float(glt_msg['infoprioPayload']['toolData'][0]['longitude'])
                    args.qr3_alt = float(glt_msg['infoprioPayload']['toolData'][0]['altitude'])
                found = False
                qr = None
            else:
                found = False
                qr = None

            # Terminate calibration
            if local_point1 != None and local_point2 != None and local_point3 != None \
            and local_point1 != local_point2 and local_point1 != local_point3 and local_point2 != local_point3:
                if args.map and not args.calibrated:
                    with open(os.path.join(os.path.dirname(args.map),'local_points.txt'),'w+') as fp:
                        fp.write('%f,%f\n' % (local_point1[0], local_point1[1]))
                        fp.write('%f,%f\n' % (local_point2[0], local_point2[1]))
                        fp.write('%f,%f\n' % (local_point3[0], local_point3[1]))

                        # write GPS lat,lon pairs for the above local points
                        lat, lon = xy2latlon((local_point1[0],local_point1[1]), (args.qr1_lat,args.qr1_lon), (args.qr2_lat,args.qr2_lon), (args.qr3_lat,args.qr3_lon), local_point1, local_point2, local_point3)
                        fp.write('%f,%f,%f\n' % (lat, lon, args.qr1_alt))

                        lat, lon = xy2latlon((local_point2[0],local_point2[1]), (args.qr1_lat,args.qr1_lon), (args.qr2_lat,args.qr2_lon), (args.qr3_lat,args.qr3_lon), local_point1, local_point2, local_point3)
                        fp.write('%f,%f,%f\n' % (lat, lon, args.qr2_alt))

                        lat, lon = xy2latlon((local_point3[0],local_point3[1]), (args.qr1_lat,args.qr1_lon), (args.qr2_lat,args.qr2_lon), (args.qr3_lat,args.qr3_lon), local_point1, local_point2, local_point3)
                        fp.write('%f,%f,%f\n' % (lat, lon, args.qr3_alt))

                if os.path.exists(os.path.join(pwd, ".SendImage")):
                    os.remove(os.path.join(pwd, ".SendImage"))
                listener.stop()
                scale_loc2met = GD((args.qr1_lat, args.qr1_lon), (args.qr2_lat, args.qr2_lon)).m / math.dist([local_point1[0],local_point1[1]], [local_point2[0],local_point2[1]])
                p = "\n****** FINISHED CALIBRATION! Local Coordinates: QR1[{}, {}] QR2[{}, {}] QR3[{}, {}] 1 local unit = {} meters ******".format(local_point1[0], local_point1[1], local_point2[0], local_point2[1], local_point3[0], local_point3[1], scale_loc2met)
                print(p)
                logger.info(p)
                p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                if client: client.publish(DebugTopic, p_intnl)

        if args.debug:
            p = "\n" + ("CALIBRATING! QR[" + ("1:NONE" if local_point1==None else "1:FOUND") + ", " + ("2:NONE" if local_point2==None else "2:FOUND") + ", " + ("3:NONE" if local_point3==None else "3:FOUND") + "] " if calibrating else "CALIBRATED! ") + "Local Coordinates: [x:" + str(nums[3]) + ", y:" + str(nums[11]) + ", h:" + str(nums[7])  + "]"
            print(p)
            logger.info(p)
            if calibrating:  
                p_intnl = "{\n\"sourceID\": \"%s\",\n\"console\": \"%s\"\n}" % (sourceID, p)
                if client: client.publish(DebugTopic, p_intnl)

        circ_buff = circ_buff.replace(circ_buff[idx_start:idx_end+len('--END-BUF--')], "")
        idx_start = -1
        idx_end = -1
        
        # Transform to global coordiantes
        if local_point1 != None and local_point2 != None and local_point3 != None \
        and local_point1 != local_point2 and local_point1 != local_point3 and local_point2 != local_point3:
            if sum(nums) != 4: # Ean exei prolavei na kanei tracking to slam kai na epistrefei kati valid
                lat, lon = xy2latlon((nums[3],nums[11]), \
                    (args.qr1_lat,args.qr1_lon), (args.qr2_lat,args.qr2_lon), (args.qr3_lat,args.qr3_lon), \
                    local_point1, local_point2, local_point3)
                dist = GD((lat, lon), previous_lat_lon).m
                speed = 0.0
                hea = 0.0
                if dist > 0: # emmit no message if lose tracking / distance = 0
                    total_distance_m += dist
                    hea = Geodesic.WGS84.Inverse(previous_lat_lon[0], previous_lat_lon[1], lat, lon)['azi1'] # outputs [-180,180]
                    if hea < 0:
                        hea = 360 + hea # convert to [0,360]
                    speed = dist / (time.time() - previous_lat_lon_time)
                    previous_lat_lon = (lat, lon)
                    previous_lat_lon_time = time.time()
                    alt = (args.qr1_alt + args.qr2_alt + args.qr3_alt) / 3 - nums[7] * scale_loc2met # local height axis is negative

                    # Make JSON and send to broker
                    json_msg = make_json_new(ToolId, "VisualSelfLoc#FRLocation", "SelfLocData", datetime.datetime.utcnow().isoformat(), lat, lon, hea, alt, "helmet")
                    mkdir(os.path.join(args.output_dir, str(frame_count)))
                    with open(os.path.join(args.output_dir, str(frame_count), "best.json"), 'w', newline='') as json_file:
                        json_file.write(json_msg)
                    if client:
                        client.publish(PublishingTopic, json_msg)
        
        # Prepare for next frame
        frame_time = time_from(t0, "*** LOOP: " + str(frame_count) + " | SPEED: " + str(round(speed, 1)) + "m/s | HEADING: " + str(round(hea, 1)) + "\u00b0 | TOTAL DISTANCE: " + str(round(total_distance_m, 2)) + "m (+" + str(round(dist ,2)) + "m) | BATTERY: " + str(round(float(psutil.sensors_battery().percent), 1)) + "% | MS", logger, args.debug)
        frame_count += 1
        wait_for = 1.0 / args.cap_fps - frame_time
        if wait_for > 0:
            time.sleep(wait_for)
