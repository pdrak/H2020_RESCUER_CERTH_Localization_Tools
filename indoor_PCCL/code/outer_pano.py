################################
### CERTH Drakoulis, Pattas
################################
'''
    X = Right axis
    Y = Down axis
    Z = Forward axis
'''
import pccl_pano
import pccl_utils
import time
import os
from configargparse import ArgumentParser
import random
import pprint
import numpy as np
from plyfile import PlyData, PlyElement
import torch
import copy
import glob
import datetime

if __name__ == "__main__":
    
    # Parse arguments
    script_name = os.path.basename(__file__)
    parser = ArgumentParser(description = script_name)
    parser.add_argument("--config", is_config_file=True, help="config file")
    parser.add_argument("--debug", action="store_true", help="save various intermediate files")
    parser.add_argument("--output_dir", required=True, help="path where to save output files")
    parser.add_argument("--seed", default=161053, type=int, help="rng seed")
    parser.add_argument("--save_init_poses", action="store_true", help="flag to save initial poses into a .ply")
    parser.add_argument("--save_best", action="store_true", help="flag to save best.png and best.csv")
    parser.add_argument("--show_projections", action="store_true", help="flag to show the rasterized pointcloud projections")
    parser.add_argument("--show_best_histo", action="store_true", help="flag to show the K best poses after histogram loss")
    parser.add_argument("--show_optimization", action="store_true", help="flag to view the optimization as it progresses")
    parser.add_argument("--torch_device", default="cuda", help="[\'cpu\' \'cuda\' \'cuda:0\' etc...]")
    parser.add_argument("--room_ply", required=True, help="path of input room colored pointcloud")
    parser.add_argument("--entry_ply", help="a ply with one vertex on the building entrance")
    parser.add_argument("--camera_preconnected", action="store_true", help="flag to show if the pc is connected to the camera wifi before start")
    parser.add_argument("--queries_glob", 
            help="a glob path with all the trajectory jpegs. If it exists, it does not connect to the camera and use these images as input instead")
    parser.add_argument("--query_img", default="", help="Do not use it. It is a placeholder to overwrite with the specific image url before passing args to inner script.")
    parser.add_argument("--query_img_poses", help="path to .csv file containing the poses of the query images")
    parser.add_argument("--min_distance_from_end_m", default=0.6, type=float, help="min distance from ray's end or bounding-box \
        (for the bounding-box case, it means along the X (left-right) and Z (forward-backwards) axes)")
    parser.add_argument("--min_distance_between_poses_m", default=0.6, type=float, help="")
    parser.add_argument("--min_dist_from_floor_m", default=1.3, type=float, help="minimum acceptable distance from floor")
    parser.add_argument("--min_dist_from_ceiling_m", default=1.0, type=float, help="minimum acceptable distance from ceiling")
    parser.add_argument("--min_pitch_deg", default=0, type=float, help="look up-down")
    parser.add_argument("--max_pitch_deg", default=10.0, type=float, help="look up-down")
    parser.add_argument("--min_roll_deg", default=0, type=float, help="lean left-right")
    parser.add_argument("--max_roll_deg", default=10.0, type=float, help="lean left-right")
    parser.add_argument("--init_T", default=300, type=int, help="initial number of translations to test")
    parser.add_argument("--init_max_attempts", default=300, type=int, help="max attempts to find init_T-feasible translations")
    parser.add_argument("--init_views_per_T", default=4, type=int,
        help="how many views to take around the yaw-axis of each translation \n(one view every 360/init_views_per_T degrees)")
    parser.add_argument("--best_K", default=8, type=int, help="first stage's best(histogram) number of poses to keep")
    parser.add_argument("--histo_bin_size", default=3, type=int, help="histogram's bin size")
    parser.add_argument("--itters", default=100, type=int, help="gradient-descend max itterations per pose")
    parser.add_argument("--lr", default=0.04, type=float, help="initial learning-rate")
    parser.add_argument("--sampl_loss", default='L2', help="sampling loss type [\'L1\' \'L2\']")
    parser.add_argument("--distance_w_lamda", default=0, type=int, help="changes the curve of how much the vertex distance from camera weights the loss. \
        0=distance does not count. 1=counts linearly. 2+=counts exponentially. Negative numbers means putting a thresshold at x meters distance. Closer than x count equally, \
        further than x don't count at all.")
    parser.add_argument("--penalty_factor", default=100, type=float,
        help="loss penalty factor for bounding-box and rotation constraints. Applies only for --constrained_optimization")
    parser.add_argument("--scheduler", default='cos', help="scheduler type [\'no\' \'rop\' \'step\' \'cos\']")
    parser.add_argument("--rendering_width", default=512, type=int,
        help="rasterization / rendering opperations will be done in this resolution across the pipeline")
    parser.add_argument("--dilate_outs", action="store_true", help="flag to apply pixel dilation to all image outputs.")
    parser.add_argument("--full_histo", action="store_true", help="flag to calculate histrogram-loss for all the color channels. \
        By default, it calculates histogram only for the green color.")
    parser.add_argument("--skip_histo", action="store_true", help="flag to skip histogram stage.")
    parser.add_argument("--model_lat", required=True, type=float, help="3d model axis origin latitude (earth degrees)")
    parser.add_argument("--model_lon", required=True, type=float, help="3d model axis origin longtitude (earth degrees)")
    parser.add_argument("--model_alt", required=True, type=float, help="3d model axis origin altimeter (meters)")
    parser.add_argument("--model_north", required=True, type=float, help="")
    parser.add_argument("--broker_ip", help="If it exists, sends results to broker")
    parser.add_argument("--init_point_search_radius_m", default=2.5, type=float,
        help="the radius around each itteration's solution where to look for the next iteration's initial points")
    parser.add_argument("--mask_pixel_h", type=int, default=0, help="begining from the bottom, mask's height in pixels")
    parser.add_argument("--image_filter", action="store_true", help="flag to apply image filter to query images.")
    parser.add_argument("--show_save_query", action="store_true", help="flag to show and save the filtered query image.")
    parser.add_argument("--frID", default="defaultFR", help="")
    args = parser.parse_args()
    
    # Start logging
    if args.output_dir: pccl_utils.mkdir(args.output_dir)
    logger = pccl_utils.setup_logger(name = "logger", save_dir = args.output_dir, filename = script_name + ".log")
    print("\nSTART.")
    logger.info("\nSTART.")
    print("\nArguments:{}".format(pprint.pformat(args.__dict__)))
    logger.info("\nArguments:{}".format(pprint.pformat(args.__dict__)))
    
    # Set the environemnt
    device = torch.device("cpu") if not torch.cuda.is_available() else torch.device(args.torch_device)
    random.seed(args.seed)
    
    # Load ply and calculate bbox
    t1 = time.time()
    room_ply = np.array(PlyData.read(args.room_ply)["vertex"])
    room_xyz = np.stack((room_ply['x'],room_ply['y'],room_ply['z'],np.ones((room_ply.shape[0],),dtype=float)), axis=1).T
    room_bbox = pccl_utils.bbox(room_xyz)
    room_xyz = torch.tensor(room_xyz, dtype=torch.float32, device=device)
    room_rgb = np.stack((room_ply['red'],room_ply['green'],room_ply['blue']), axis=1)
    room_rgb = torch.tensor(room_rgb, dtype=torch.float32, device=device)
    if args.entry_ply:
        entry_ply = np.array(PlyData.read(args.entry_ply)["vertex"])
        init_point_xyz = np.stack((entry_ply['x'],entry_ply['y'],entry_ply['z'])).flatten().tolist()
    pccl_utils.time_from(t1, "LOAD PLY AND CALC BBOX", logger, args.debug)
    
    # Generate initial poses
    t2 = time.time()
    init_poses = pccl_utils.initial_poses_from_pc(room_bbox, args, device)
    pccl_utils.time_from(t2, "GENERATE INITIAL POSES", logger, args.debug)
    if args.save_init_poses:
        vertex = np.array([tuple(i) for i in init_poses],
            dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('yaw', 'f4'), ('pitch', 'f4'), ('roll', 'f4')])
        el = PlyElement.describe(vertex, 'vertex')
        PlyData([el], text=True).write(os.path.join(args.output_dir, "init_poses" + ".ply"))
    
    # Connect to camera
    if not args.queries_glob:
        t3 = time.time()
        if not args.camera_preconnected:
            from open_gopro import GoPro # IMPORTANT gopro.py (open-gopro==0.11.0) comment-out lines 365-369. Also, add logging.disable() in the beggining of the script.
            gopro = GoPro()
            gopro.open()
        from goprocam import GoProCamera # GoProCamera.py (goprocam==4.2.0) comment-out line 923 to disable path prints.
        goproCamera = GoProCamera.GoPro()
        pccl_utils.time_from(t3, "CONNECT TO CAMERA", logger, args.debug)

    # Connect to broker
    ToolId = 'LOC-SELF' 
    frID = args.frID
    Role = 'FR'
    sourceID = frID + '#' + Role
    category = 'VisualSelfLoc#FRLocation'
    type = 'SelfLocData' 
    
    if args.broker_ip:
        PublishingTopic = 'fromtool-' + ToolId.lower()
        t4 = time.time()
        import paho.mqtt.client as mqtt
        client = mqtt.Client(ToolId)
        client.connect(args.broker_ip)
        pccl_utils.time_from(t4, "CONNECT TO BROKER", logger, args.debug)

    # Core loop
    frame_count = 0
    n_frames = 1000000000
    if args.queries_glob:
        queries = glob.glob(args.queries_glob)
        n_frames = len(queries)
    inner_args = copy.deepcopy(args)
    while frame_count < n_frames:
        
        # Set the inner environemnt
        inner_args.output_dir = os.path.join(args.output_dir, str(frame_count))
        inner_args.query_img = os.path.join(inner_args.output_dir, "last_capture.jpg")
        pccl_utils.mkdir(inner_args.output_dir)
        inner_args.debug = False
        
        # Capture image
        if not args.queries_glob:
            t5 = time.time()
            goproCamera.downloadLastMedia(goproCamera.take_photo(timer=0), inner_args.query_img)
            pccl_utils.time_from(t5, "CAPTURE AND DOWNLOAD IMAGE", logger, args.debug)
        else:
            inner_args.query_img = queries[frame_count]
        
        # Calculate initial positions sub-set
        init_poses_subset = pccl_utils.init_poses_subset(init_poses, init_point_xyz, inner_args.init_point_search_radius_m, device) \
            if inner_args.entry_ply else init_poses
        if inner_args.save_init_poses:
            vertex = np.array([tuple(i) for i in init_poses_subset],
                dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('yaw', 'f4'), ('pitch', 'f4'), ('roll', 'f4')])
            el = PlyElement.describe(vertex, 'vertex')
            PlyData([el], text=True).write(os.path.join(inner_args.output_dir, "init_poses" + ".ply"))
        
        # Localization
        t6 = time.time()
        dx, dy, dz, dyaw, dpitch, droll = pccl_pano.pccl_pano(inner_args, logger, room_xyz, room_rgb, room_bbox, init_poses_subset, inner_args.mask_pixel_h)
        pccl_utils.time_from(t6, "Loop number: " + str(frame_count) + " - LOCALIZATION", logger, args.debug)
        
        # Transform to global coordiantes
        lat, lon, alt, hea = pccl_utils.transform_to_earth_coordinates(dx, dy, dz, dyaw, inner_args.model_lat, inner_args.model_lon, inner_args.model_alt, inner_args.model_north)
        
        # Make JSON and send to broker
        json_msg = pccl_utils.make_json(ToolName, ToolId, lat, lon, alt, hea, dx, dy, dz, dyaw, dpitch, droll, extID, frID)
        #json_msg = pccl_utils.make_json_new(ToolId, sourceID, category, type, datetime.datetime.now().isoformat(), lat, lon, hea, alt, "helmet")
        with open(os.path.join(inner_args.output_dir, "best.json"), 'w', newline='') as json_file:
            json_file.write(json_msg)
        if args.broker_ip:
            client.publish(PublishingTopic, json_msg)
        
        # Prepare for next frame
        if inner_args.entry_ply:
            init_point_xyz = [dx, dy, dz]
        frame_count += 1
