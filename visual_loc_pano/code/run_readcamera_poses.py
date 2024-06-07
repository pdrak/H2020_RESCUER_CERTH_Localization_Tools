from configargparse import ArgumentParser
import socket
import time
import sys
import os

script_name = os.path.basename(__file__)
parser = ArgumentParser(description = script_name)
parser.add_argument("--config", is_config_file=True, help="config file")
parser.add_argument("--debug", action="store_true", help="save various intermediate files")
parser.add_argument("--socket_path", default="/home/rescuer/Documents/GitHub/Localization/visual_loc_pano/stella_vslam/build/tpf_unix_sock.server", help="path to unix-domain socket")
args = parser.parse_args()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            
while True:
    p = "\nWaiting for stella to begin..."
    print(p)
        
    if not os.path.exists("/tmp/.LOCK_FILE"):
        time.sleep(0.125)
    else:
        print("Lock files found! Proceeding to connection.")
        break

try:
    print("connecting to socket: " + args.socket_path)
    sock.connect(args.socket_path)
except socket.error:
    print("\nCONNECTION TO CAMERA SOCKET FAILED!")
    sys.exit(1)

# Core loop
while True:
    circ_buff = ""
    idx_start = -1
    idx_end = -1

    # Read from camera
    data = sock.recv(8192)
    if len(data) == 0:
        sys.exit(1)

    data = data.decode('utf-8')
    circ_buff += data
    idx_start = circ_buff.rfind('--START-BUF--')
    idx_end = circ_buff.rfind('--END-BUF--')
    if idx_start == -1 or idx_end == -1:
        continue
    if circ_buff[idx_start:idx_end+len('--END-BUF--')] == "":
        continue
    nums = [float(x) for x in circ_buff[idx_start+len('--START-BUF--'):idx_end].split(',')[0:16]]
    if args.debug:
        print("\n" + str(nums))
    circ_buff = circ_buff.replace(circ_buff[idx_start:idx_end+len('--END-BUF--')], "")
    idx_start = -1
    idx_end = -1
