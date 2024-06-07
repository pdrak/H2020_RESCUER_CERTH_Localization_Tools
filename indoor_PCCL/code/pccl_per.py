################################
### CERTH Drakoulis, Pattas
################################
'''
    X = Right axis
    Y = Down axis
    Z = Forward axis
'''
import pccl_utils
import time
import os
from configargparse import ArgumentParser
import random
import pprint
import numpy as np
from plyfile import PlyData, PlyElement
import torch
import cv2
import csv

def pccl_per(args_inner, logger, room_xyz, room_rgb, room_bbox, init_Poses):
    
    # Open query image
    t2 = time.time()
    query_img = cv2.cvtColor(cv2.imread(args_inner.query_img, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    pccl_utils.time_from(t2, "OPEN QUERY IMG", logger, args_inner.debug)
    
    width = args_inner.rendering_width
    aspect_ratio = query_img.shape[1] / query_img.shape[0]
    height = int(width/aspect_ratio)
    aspect_ratio = width / height
    
    if query_img.shape[1] != width: query_img = cv2.resize(query_img, (width, height), interpolation=cv2.INTER_LANCZOS4)
    query_img = torch.tensor(query_img, dtype=torch.float32, device=device)
    
    sensor_limits = pccl_utils.sensor_limits(aspect_ratio)
    sensor_plane_z = pccl_utils.sensor_plane_z(args.fov)
    intrinsics = pccl_utils.calculate_intrinsics(sensor_plane_z, device)

    if not args_inner.skip_histo:
        # Project pointcloud and calculate its histogramm loss
        t3 = time.time()
        hist_loss = []
        init_Filters = []
        for pose in init_Poses:
            extrinsics = pccl_utils.calculate_extrinsics(pose, device)
            sampled_query_img, filter = pccl_utils.sample_query_img_per(extrinsics, intrinsics, sensor_limits, query_img, room_xyz)
            hist_loss.append(pccl_utils.histogram_loss_per(room_rgb, sampled_query_img, filter, args_inner))
            init_Filters.append(filter)
            if args_inner.show_projections: pccl_utils.show_or_save_per(extrinsics, intrinsics, sensor_limits, width, height, room_xyz, room_rgb, filter, device, args_inner.dilate_outs, name="--show_projections")   

        # Sort initial_poses by histogram loss and pick the k-best  
        init_Poses = [x for _,x in sorted(zip(hist_loss, init_Poses), key=lambda y: y[0])][0:args_inner.best_K]
        init_Filters = [x for _,x in sorted(zip(hist_loss, init_Filters), key=lambda y: y[0])][0:args_inner.best_K]
        pccl_utils.time_from(t3, "HISTOGRAMS", logger, args_inner.debug)
        
        if args_inner.show_best_histo:
            sorted_indices = [x for _,x in sorted(zip(hist_loss, range(len(hist_loss))), key=lambda y: y[0])][0:args_inner.best_K]
            sorted_hist_loss = sorted(hist_loss)
            for i, m, n, q in zip(sorted_indices, sorted_hist_loss, init_Poses, init_Filters):
                if args_inner.query_img_poses:
                    metric = pccl_utils.calculate_metrics(n, args_inner, device)
                    print(f"id: {i}     histogramm loss: {m}     Metric L2 (m): {metric[0].item()} Angular Distance (rad): {metric[1].item()}")
                    logger.info(f"id: {i}     histogramm loss: {m}     Metric L2 (m): {metric[0].item()} Angular Distance (rad): {metric[1].item()}")
                else:
                    print(f"id: {i}     histogramm loss: {m}")
                    logger.info(f"id: {i}     histogramm loss: {m}")
                pccl_utils.show_or_save_per(pccl_utils.calculate_extrinsics(n, device), intrinsics, sensor_limits, width, height, room_xyz, room_rgb, q, device, args_inner.dilate_outs, name="--show_best_histo")

    # Optimization
    t4 = time.time()
    best_loss = torch.tensor(float('inf'), device=device)
    best_pose = None
    best_filter = None
    for i in range(len(init_Poses)):
        pose = init_Poses[i].clone().detach()
        pose.requires_grad_()
        opt = torch.optim.Adam([pose], lr=args_inner.lr, amsgrad=True)
        
        if args_inner.scheduler == 'no':
            pass # no lr scheduler
        elif args_inner.scheduler == 'rop':
            sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.25)
        elif args_inner.scheduler == 'step':
            sch = torch.optim.lr_scheduler.StepLR(opt, step_size=args_inner.itters//2, gamma=0.25)
        elif args_inner.scheduler == 'cos':
            sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args_inner.itters)
        else:
            raise ValueError(f"scheduler type [\'no\' \'rop\' \'step\' \'cos\']. Got = {args_inner.scheduler}")
        
        for j in range(args_inner.itters):
            opt.zero_grad()
            extrinsics = pccl_utils.calculate_extrinsics(pose, device)
            sampled_query_img, filter = pccl_utils.sample_query_img_per(extrinsics, intrinsics, sensor_limits, query_img, room_xyz)
            loss = pccl_utils.sampling_loss_per(room_rgb, sampled_query_img, filter, pose, room_bbox, args_inner, args_inner.sampl_loss, args_inner.penalty_factor)
            loss.backward()
            
            backup_pose = pose.detach().clone()
            opt.step()
            if torch.isnan(pose).sum() > 0:
                pose = backup_pose
                break
            
            if args_inner.scheduler != 'no': sch.step(metrics=loss) if args_inner.scheduler == 'rop' else sch.step()

            if args_inner.show_optimization:
                if j % 2 != 0: continue
                print(f"\nPose: {i}     Itteration: {j}     Loss: {loss.item()}     Pose: {pose.cpu().detach().numpy()}")
                logger.info(f"\nPose: {i}     Itteration: {j}     Loss: {loss.item()}     Pose: {pose.cpu().detach().numpy()}")
                if args_inner.query_img_poses:
                    metric = pccl_utils.calculate_metrics(pose, args_inner, device)
                    print(f"Metric L2 (m): {metric[0].item()} Angular Distance (rad): {metric[1].item()}")
                    logger.info(f"Metric L2 (m): {metric[0].item()} Angular Distance (rad): {metric[1].item()}")
                pccl_utils.show_or_save_per(extrinsics, intrinsics, sensor_limits, width, height, room_xyz, room_rgb, filter, device, args_inner.dilate_outs, name="--show_optimization", wait=1)
        
        if loss < best_loss:
            best_loss = loss
            best_pose = pose
            best_filter = filter
    pccl_utils.time_from(t4, "OPTIMIZATION", logger, args_inner.debug)
    
    # Print best
    print(f"\nBest pose: {best_pose.cpu().detach().numpy()}     Loss: {best_loss.item()}")
    logger.info(f"\nBest pose: {best_pose.cpu().detach().numpy()}     Loss: {best_loss.item()}")
    if args_inner.query_img_poses:
        best_metric = pccl_utils.calculate_metrics(best_pose, args_inner, device)
        print(f"Metric L2 (m): {best_metric[0].item()} Angular Distance (rad): {best_metric[1].item()}")
        logger.info(f"Metric L2 (m): {best_metric[0].item()} Angular Distance (rad): {best_metric[1].item()}")
    
    if args_inner.save_best:
        t5 = time.time()
        best_pose_np = best_pose.cpu().detach().numpy()
        f_base = os.path.join(args_inner.output_dir, "best")
        
        # Save best pose as image
        pccl_utils.show_or_save_per(pccl_utils.calculate_extrinsics(best_pose, device), intrinsics, sensor_limits, width, height, room_xyz, room_rgb, best_filter, device, args_inner.dilate_outs,
            path = f_base + ".png")
        
        # Save best pose as csv
        with open(f_base + ".csv", 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([str(best_pose_np[0])])
            writer.writerow([str(best_pose_np[1])])
            writer.writerow([str(best_pose_np[2])])
            writer.writerow([str(best_pose_np[3])])
            writer.writerow([str(best_pose_np[4])])
            writer.writerow([str(best_pose_np[5])])
            writer.writerow([str(best_loss.item())])
            if args_inner.query_img_poses:
                writer.writerow([str(best_metric[0].item())])
                writer.writerow([str(best_metric[1].item())])
                
        # Save best pose as ply
        vertex = np.array([tuple(best_pose_np)],
            dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('yaw', 'f4'), ('pitch', 'f4'), ('roll', 'f4')])
        el = PlyElement.describe(vertex, 'vertex')
        PlyData([el], text=True).write(f_base + ".ply")
                
        pccl_utils.time_from(t5, f"FILE SAVES", logger, args_inner.debug)
    
    return best_pose[:6].cpu().detach().numpy()

################################

if __name__ == "__main__":
    tt = time.time()
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
    parser.add_argument("--room_exr",
        help="path of input room's depth .exr. If it exists, it calculates the initial poses by sampling pixels on this image \
        instead of picking random locations inside the room pointcloud's bounding-box")
    parser.add_argument("--query_img", required=True, help="path of query image")
    parser.add_argument("--query_img_poses", help="path to .csv file containing the poses of the query images")
    parser.add_argument("--fov", required=True, type=float, help="query image's field of view (deg)")
    parser.add_argument("--max_valid_depth_m", default=10.0, type=float,
        help="max valid value of input depth image (in meters, valid only for creating initial poses with --room_exr)")
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
    parser.add_argument("--better_distribution", action="store_true",
        help="flag to sample from a distribution that mitigates the effect of outwards diminishing points density. \
        (valid only for creating initial poses with --room_exr)")
    parser.add_argument("--init_max_attempts", default=300, type=int, help="max attempts to find init_T-feasible translations")
    parser.add_argument("--init_views_per_T", default=6, type=int,
        help="how many views to take around the yaw-axis of each translation \n(one view every 360/init_views_per_T degrees)")
    parser.add_argument("--best_K", default=8, type=int, help="first stage's best(histogram) number of poses to keep")
    parser.add_argument("--histo_bin_size", default=3, type=int, help="histogram's bin size")
    parser.add_argument("--itters", default=100, type=int, help="gradient-descend max itterations per pose")
    parser.add_argument("--lr", default=0.04, type=float, help="initial learning-rate")
    parser.add_argument("--sampl_loss", default='L2', help="sampling loss type [\'L1\' \'L2\']")
    parser.add_argument("--penalty_factor", default=100, type=float,
        help="loss penalty factor for bounding-box and rotation constraints. Applies only for --constrained_optimization")
    parser.add_argument("--scheduler", default='cos', help="scheduler type [\'no\' \'rop\' \'step\' \'cos\']")
    parser.add_argument("--rendering_width", default=512, type=int,
        help="rasterization / rendering opperations will be done in this resolution across the pipeline")
    parser.add_argument("--dilate_outs", action="store_true", help="flag to apply pixel dilation to all image outputs.")
    parser.add_argument("--full_histo", action="store_true", help="flag to calculate histrogram-loss for all the color channels. \
        By default, it calculates histogram only for the green color.")
    parser.add_argument("--skip_histo", action="store_true", help="flag to skip histogram stage.")
    parser.add_argument("--init_point_xyz", nargs=3, type=float,
        help="list containing the coordinates of the center point around which the algorithm will search for random initial points (e.g. 3.1 -1.2 2.0).")
    parser.add_argument("--init_point_max_translation_m", default=3.0, type=float,
        help="max translation around the --init_point_xyz point to search for random initial points")
    args = parser.parse_args()
    
    if args.output_dir: pccl_utils.mkdir(args.output_dir)
    device = torch.device("cpu") if not torch.cuda.is_available() else torch.device(args.torch_device)
    random.seed(args.seed)
    
    logger = pccl_utils.setup_logger(name = "logger", save_dir = args.output_dir, filename = script_name + ".log")
    print("\nSTART...")
    logger.info("\nSTART...")
    if args.debug:
        print("\nArguments:{}".format(pprint.pformat(args.__dict__)))
        logger.info("\nArguments:{}".format(pprint.pformat(args.__dict__)))
    
    # Load ply and calculate bbox
    t0 = time.time()
    room_ply = np.array(PlyData.read(args.room_ply)["vertex"])
    room_xyz = np.stack((room_ply['x'],room_ply['y'],room_ply['z'],np.ones((room_ply.shape[0],),dtype=float)), axis=1).T
    room_bbox = pccl_utils.bbox(room_xyz)
    room_xyz = torch.tensor(room_xyz, dtype=torch.float32, device=device)
    room_rgb = np.stack((room_ply['red'],room_ply['green'],room_ply['blue']), axis=1)
    room_rgb = torch.tensor(room_rgb, dtype=torch.float32, device=device)
    pccl_utils.time_from(t0, "LOAD PLY", logger, args.debug)
    
    # Create initial poses
    t1 = time.time()
    if args.init_point_xyz:
        init_Poses = pccl_utils.initial_poses_around_a_point(room_bbox, args, device)
    elif args.room_exr:
        init_Poses = pccl_utils.initial_poses_from_exr(room_bbox, args, device)
    else:
        init_Poses = pccl_utils.initial_poses_from_pc(room_bbox, args, device)
    pccl_utils.time_from(t1, "INITIAL POSES", logger, args.debug)
    if args.save_init_poses:
        vertex = np.array([tuple(i) for i in init_Poses],
            dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('yaw', 'f4'), ('pitch', 'f4'), ('roll', 'f4')])
        el = PlyElement.describe(vertex, 'vertex')
        PlyData([el], text=True).write(os.path.join(args.output_dir, "init_Poses" + ".ply"))
    
    # Localization
    dx, dy, dz, dyaw, dpitch, droll = pccl_per(args, logger, room_xyz, room_rgb, room_bbox, init_Poses)
    pccl_utils.time_from(tt, "TOTAL", logger)
    print("")
    logger.info("")
