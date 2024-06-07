from configargparse import ArgumentParser
from threading import Thread

import argparse
import requests
import socket
import atexit
import time
import sys
import os

args = None
vm_socket = None
vm_port = None
host_ip = None
host_port = None
host_port_2 = None

def main():
    global vm_socket
    global args

    parser = ArgumentParser(description = 'proxycam.py')

    parser.add_argument("--from_vs_code", action="store_true", help="flag so that the script knows it is called in vscode and not docker")
    parser.add_argument("--host_ip", required=True, help="sets the IP address of the local machine")
    parser.add_argument("--camera_ip", default="172.21.134.51", help="sets the IP address of the GoPro HERO 10")
    parser.add_argument("--camera_port", default="8554", help="sets the port of the camera")
    parser.add_argument("--forward_port_1", default="8555", help="sets the number of the first forwarded port")
    parser.add_argument("--forward_port_2", default="8556", help="sets the number of the second forwarded port")
    parser.add_argument("--cmds", default="stop,start", help="sets the HTTP commands to be submitted")
    
    args = parser.parse_args()

    vm_port = args.camera_port
    host_ip = args.host_ip
    host_port = args.forward_port_1
    host_port_2 = args.forward_port_2
    cmds = args.cmds

    if args.from_vs_code:
        print("removing pre-existing lock...")
        if os.path.exists('/tmp/.LOCK_FILE_PROXYCAM'):
            os.remove('/tmp/.LOCK_FILE_PROXYCAM')

    for cmd_ in cmds.split(','):
        cmd_ = cmd_.lower()

        if cmd_ not in ['start','stop','exit','fps25']:
            print("Unknown proxycam command: %s" % cmd_)
            sys.exit()
        
        if cmd_ == 'exit':
            print("Exiting proxycam...")
            sys.exit()

        if cmd_ == 'fps25':
            urlstart = "http://%s:%d/gopro/camera/setting?setting=3&option=9" % (args.camera_ip,8080)
            conn_cnt = 0

            while True:
                response = requests.post(urlstart)
                if response.status_code == 200:
                    print("[!] Successfully '%s'-ed webcam." % cmd_)
                    break
                else:
                    print("[!] Retrying webcam '%s'..." % cmd_)
                    if conn_cnt == 5:
                        print("[!] Tried to '%s' webcam 5 consecutive times but failed. Exiting..." % cmd_)
                        sys.exit(1)

                    conn_cnt += 1

        if cmd_ == 'start' or cmd_ == 'stop':
            urlstart = "http://%s:%d/gopro/webcam/%s" % (args.camera_ip,8080,cmd_)
            conn_cnt = 0

            while True:
                response = requests.post(urlstart)
                if response.status_code == 200:
                    print("[!] Successfully '%s'-ed webcam mode." % cmd_)
                    break
                else:
                    print("[!] Retrying webcam '%s'..." % cmd_)
                    if conn_cnt == 5:
                        print("[!] Tried to '%s' webcam mode 5 consecutive times but failed. Exiting..." % cmd_)
                        sys.exit(1)

                    conn_cnt += 1

    print("[!] Entering main proxy loop...")

    vm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    vm_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    vm_socket.bind(("0.0.0.0", int(vm_port)))
    
    host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        data, vm_address = vm_socket.recvfrom(65536)
        
        host_socket.sendto(data, (host_ip, int(host_port)))
        host_socket.sendto(data, (host_ip, int(host_port_2)))

    host_socket.close()

def cleanup_cbk():
    global vm_socket
    
    print("Calling clean-up callback in proxycam...")

    # close server socket
    if vm_socket != None:
        vm_socket.close()

if __name__ == '__main__':
    atexit.register(cleanup_cbk)
    main()

