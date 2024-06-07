################################
### CERTH Drakoulis, Pattas
################################
'''
    X = Right axis
    Y = Down axis
    Z = Forward axis
'''
import os
import errno
import logging
import time
import datetime
import numpy as np
import random
import torch
import torch.nn.functional as fn
import cv2
import grid
import cartesian
import math
import json
import histogram_matching
import geopy.distance

def setup_logger(name:str, save_dir:str, filename:str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    if save_dir:
        fh = logging.FileHandler(os.path.join(save_dir, filename))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

################################

def mkdir(path:str):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST: raise ValueError("Invalid output path!")
        
################################   
        
def time_from(start_time, description, logger, debug=True):
    end_time = time.time() - start_time
    delta_str = str(datetime.timedelta(seconds=end_time))
    if debug:
        print("\n" + description + ": " + delta_str)
        logger.info("\n" + description + ": " + delta_str)
        
################################      

def show_or_save_pano(extrinsics, width, height, room_xyz, room_rgb, device, dilate_outs=False, name="", wait=0, path="") :
    Xformed_pc = torch.matmul(extrinsics, room_xyz)
    # we name X,Y,Z left,down,forward because we use a formula built on this convention.
    left = -Xformed_pc[0]
    down = Xformed_pc[1]
    forward = Xformed_pc[2]
    
    eps = torch.full(left.shape, 1e-8, device=device)
    all_proj_x = torch.clamp(torch.where(left > 0,
        (width / (2 * np.pi)) * torch.atan(torch.div(forward, left)) + width * 0.25,
        (width / (2 * np.pi)) * torch.atan(torch.div(forward, torch.where(left==0, eps, left))) + width * 0.75),
    min = 0, max = width - 1)
    all_proj_y = torch.clamp(
        (height / np.pi) * torch.atan(torch.div(down, 
            torch.sqrt(torch.pow(left, 2) + torch.pow(forward, 2)) + 1e-8)) + 0.5 * height,
    min = 0, max = height - 1)
    
    img = torch.zeros((height, width, 3), dtype=torch.uint8, device=device)
    img[all_proj_y.long(),all_proj_x.long()] = room_rgb.type(torch.uint8)
    
    img = img.cpu().detach().numpy()
    if dilate_outs: img = cv2.dilate(img, np.ones((3,3), np.uint8))
    if path != "":
        cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    else:
        cv2.imshow(name, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        cv2.waitKey(wait)
        
################################

def show_or_save_per(extrinsics, intrinsics, sensor_limits, width, height, room_xyz, room_rgb, filter, device, dilate_outs=False, name="", wait=0, path="") :
    Xformed_pc = torch.matmul(extrinsics, room_xyz)
    all_proj = (torch.matmul(intrinsics, Xformed_pc) / (torch.abs(Xformed_pc[2]) + torch.finfo(torch.float32).eps)).t()
    all_proj_x = torch.clamp(
        (all_proj[filter][:,0] + 1) * 0.5 * width,
        min=0, max=width-1)
    all_proj_y = torch.clamp(
        (all_proj[filter][:,1] * sensor_limits["aspect_ratio"] + 1) * 0.5 * height,
        min=0, max=height-1)
    
    img = torch.zeros((height, width, 3), dtype=torch.uint8, device=device)
    img[all_proj_y.long(),all_proj_x.long()] = room_rgb[filter].type(torch.uint8)
    
    img = img.cpu().detach().numpy()
    if dilate_outs: img = cv2.dilate(img, np.ones((3,3), np.uint8))
    if path != "":
        cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    else:
        cv2.imshow(name, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        cv2.waitKey(wait)
        
################################

def calculate_metrics(current_pose, args_inner, device):
    with open(args_inner.query_img_poses, "r") as poses_csv:
        lines = poses_csv.readlines()
    query_pose_index = int(args_inner.query_img.replace("/","\\").split("\\")[-1].split("_")[0])
    line = lines[query_pose_index + 1].split(",")
    query_pose = [float(line[1]), float(line[2]), float(line[3]), float(line[4][:-1]), 0, 0]
    query_pose = torch.tensor(query_pose, device=device)
    L2 = torch.norm(current_pose[0:3] - query_pose[0:3], p=2)
    Angular_dist = torch.abs(current_pose[3] - query_pose[3]) % (2*np.pi) # only for yaw
    if Angular_dist > np.pi: Angular_dist = 2*np.pi - Angular_dist
    return L2, Angular_dist

################################

def calculate_metrics_from_name(current_pose, args_inner, device):
    temp = args_inner.query_img.split("\\")[-1].split("_")
    translation = temp[-2].split(" ")
    rot = temp[-1].split(".")[0]
    query_pose = [-float(translation[0][1:]), -float(translation[2][:-1]), -float(translation[1]), float(rot)*2*np.pi/360, 0, 0]
    query_pose = torch.tensor(query_pose, device=device)
    L2 = torch.norm(current_pose[0:3] - query_pose[0:3], p=2)
    Angular_dist = torch.abs(current_pose[3] - query_pose[3])%(2*np.pi) # only for yaw
    if Angular_dist > np.pi: Angular_dist = 2*np.pi - Angular_dist
    return L2, Angular_dist

################################

def sampling_loss_pano(room_rgb, sampled_query_img, pose, room_bbox, vertex_dist_from_camera, args_inner, sampl_loss='L2', penalty_factor=100, distance_w_lamda=0):
    # For w_lamda = 0 all vertices count the same. For w_lamda > 0 vertices count less according to their distance. For w_lamda < 0 they count the same up to a
    # distance of w_lamda. Any further than that they don't count at all. All these methods exist to produce a pseudo-occlusion effect. 
    # IMPORTANT! If you don't average loss, it will try to place the camera as far as possible from any vertex.
    if distance_w_lamda >= 0:
        vertex_dist_from_camera = (vertex_dist_from_camera - vertex_dist_from_camera.min()) / vertex_dist_from_camera.max() # normalization [0,...)
        if sampl_loss == 'L1':
            loss = (torch.norm(sampled_query_img - room_rgb, p=1, dim=1) * torch.pow(1 - vertex_dist_from_camera, distance_w_lamda)).mean()
        elif sampl_loss == 'L2':
            loss = (torch.norm(sampled_query_img - room_rgb, p=2, dim=1) * torch.pow(1 - vertex_dist_from_camera, distance_w_lamda)).mean()
        else:
            raise ValueError(f"sampling loss type = [\'L1\' \'L2\']. Got = {sampl_loss}")
    else:
        if sampl_loss == 'L1':
            loss = (torch.norm(sampled_query_img - room_rgb, p=1, dim=1) * torch.where(vertex_dist_from_camera + distance_w_lamda <= 0, 1, 0)).sum() / \
                torch.where(vertex_dist_from_camera + distance_w_lamda <= 0, 1, 0).sum()
        elif sampl_loss == 'L2':
            loss = (torch.norm(sampled_query_img - room_rgb, p=2, dim=1) * torch.where(vertex_dist_from_camera + distance_w_lamda <= 0, 1, 0)).sum() / \
                torch.where(vertex_dist_from_camera + distance_w_lamda <= 0, 1, 0).sum()
        else:
            raise ValueError(f"sampling loss type = [\'L1\' \'L2\']. Got = {sampl_loss}")
    
    # soft penalize positions out of bounding-box and extreme rotations
    loss += penalty_factor * fn.relu(
        pose[0] - room_bbox['x_max'] + args_inner.min_distance_from_end_m)
    loss += penalty_factor * fn.relu(
        room_bbox['x_min'] + args_inner.min_distance_from_end_m - pose[0])
    
    loss += penalty_factor * fn.relu(
        pose[2] - room_bbox['z_max'] + args_inner.min_distance_from_end_m)
    loss += penalty_factor * fn.relu(
        room_bbox['z_min'] + args_inner.min_distance_from_end_m - pose[2])
    
    loss += penalty_factor * fn.relu(
        pose[1] - room_bbox['y_max'] + args_inner.min_dist_from_floor_m)
    loss += penalty_factor * fn.relu(
        room_bbox['y_min'] + args_inner.min_dist_from_ceiling_m - pose[1])
    
    loss += penalty_factor * fn.relu(
        pose[4] - args_inner.max_pitch_deg * np.pi / 180.0)
    loss += penalty_factor * fn.relu(
        -args_inner.max_pitch_deg * np.pi / 180.0 - pose[4])
    
    loss += penalty_factor * fn.relu(
        pose[5] - args_inner.max_roll_deg * np.pi / 180.0)
    loss += penalty_factor * fn.relu(
        -args_inner.max_roll_deg * np.pi / 180.0 - pose[5])
    return loss

################################

def sampling_loss_per(room_rgb, sampled_query_img, filter, pose, room_bbox, args_inner, sampl_loss='L2', penalty_factor=100):
    if sampl_loss == 'L1':
        loss = torch.norm(sampled_query_img - room_rgb[filter], p=1, dim=1).mean()
    elif sampl_loss == 'L2':
        loss = torch.norm(sampled_query_img - room_rgb[filter], p=2, dim=1).mean()
    else:
        raise ValueError(f"sampling loss type = [\'L1\' \'L2\']. Got = {sampl_loss}")
    
    # soft penalize positions out of bounding-box and extreme rotations
    loss += penalty_factor * fn.relu(
        pose[0] - room_bbox['x_max'] + args_inner.min_distance_from_end_m)
    loss += penalty_factor * fn.relu(
        room_bbox['x_min'] + args_inner.min_distance_from_end_m - pose[0])
    
    loss += penalty_factor * fn.relu(
        pose[2] - room_bbox['z_max'] + args_inner.min_distance_from_end_m)
    loss += penalty_factor * fn.relu(
        room_bbox['z_min'] + args_inner.min_distance_from_end_m - pose[2])
    
    loss += penalty_factor * fn.relu(
        pose[1] - room_bbox['y_max'] + args_inner.min_dist_from_floor_m)
    loss += penalty_factor * fn.relu(
        room_bbox['y_min'] + args_inner.min_dist_from_ceiling_m - pose[1])
    
    loss += penalty_factor * fn.relu(
        pose[4] - args_inner.max_pitch_deg * np.pi / 180.0)
    loss += penalty_factor * fn.relu(
        -args_inner.max_pitch_deg * np.pi / 180.0 - pose[4])
    
    loss += penalty_factor * fn.relu(
        pose[5] - args_inner.max_roll_deg * np.pi / 180.0)
    loss += penalty_factor * fn.relu(
        -args_inner.max_roll_deg * np.pi / 180.0 - pose[5])
    return loss

################################

def histogram_loss_pano(room_rgb, sampled_query_img, args_inner):
    room_rgb = room_rgb.cpu().numpy() # in torch 1.10 we will use torch.histogram
    green_hist_room = np.histogram(room_rgb[:,1], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    if args_inner.full_histo:
        red_hist_room = np.histogram(room_rgb[:,0], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
        blue_hist_room = np.histogram(room_rgb[:,2], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    
    sampled_query_img = sampled_query_img.cpu().detach().numpy()
    green_hist_query = np.histogram(sampled_query_img[:,1], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    if args_inner.full_histo:
        red_hist_query = np.histogram(sampled_query_img[:,0], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
        blue_hist_query = np.histogram(sampled_query_img[:,2], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]

    rgb_loss = abs(green_hist_room - green_hist_query).mean()
    if args_inner.full_histo:
        rgb_loss += abs(red_hist_room - red_hist_query).mean()
        rgb_loss += abs(blue_hist_room - blue_hist_query).mean()
        rgb_loss /= 3
        
    return rgb_loss

################################

def histogram_loss_per(room_rgb, sampled_query_img, filter, args_inner):
    room_rgb = room_rgb[filter].cpu().numpy() # in torch 1.10 we will use torch.histogram
    green_hist_room = np.histogram(room_rgb[:,1], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    if args_inner.full_histo:
        red_hist_room = np.histogram(room_rgb[:,0], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
        blue_hist_room = np.histogram(room_rgb[:,2], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    
    sampled_query_img = sampled_query_img.cpu().detach().numpy()
    green_hist_query = np.histogram(sampled_query_img[:,1], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
    if args_inner.full_histo:
        red_hist_query = np.histogram(sampled_query_img[:,0], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]
        blue_hist_query = np.histogram(sampled_query_img[:,2], bins=256//args_inner.histo_bin_size, range=(0,255), density=True)[0]

    rgb_loss = abs(green_hist_room - green_hist_query).mean()
    if args_inner.full_histo:
        rgb_loss += abs(red_hist_room - red_hist_query).mean()
        rgb_loss += abs(blue_hist_room - blue_hist_query).mean()
        rgb_loss /= 3
        
    return rgb_loss

################################

def sample_query_img_pano(extrinsics, query_img, width, height, room_xyz, device):
    Xformed_pc = torch.matmul(extrinsics, room_xyz)
    vertex_dist_from_camera = torch.norm(Xformed_pc[0:3], p=2, dim=0) # The order in it is the same like room_xyz and room_rgb arrays.
    
    # we name X,Y,Z left,down,forward because we use a formula built on this convention.
    left = -Xformed_pc[0]
    down = Xformed_pc[1]
    forward = Xformed_pc[2]
    
    eps = torch.full(left.shape, 1e-8, device=device)
    all_proj_x = torch.where(left > 0,
        (width / (2 * np.pi)) * torch.atan(torch.div(forward, left)) / (0.5*width) - 0.5,
        (width / (2 * np.pi)) * torch.atan(torch.div(forward, torch.where(left==0, eps, left))) / (0.5*width) + 0.5)
    all_proj_y = (height / np.pi) * torch.atan(torch.div(down,
        torch.sqrt(torch.pow(left, 2) + torch.pow(forward, 2)) + 1e-8)) / (0.5*height)
    
    sampled_vectorized = fn.grid_sample(
        input = query_img.permute(2,0,1).unsqueeze(0),
        grid = torch.vstack((all_proj_x, all_proj_y)).permute(1,0).unsqueeze(0).unsqueeze(0),
        padding_mode = 'zeros',
        mode = 'bilinear',
        align_corners = False)
    
    # to apotelesma exei mikos oso to number of vertices
    return torch.clamp(sampled_vectorized.permute(0,2,3,1).squeeze(0).squeeze(0), min=0, max=255), vertex_dist_from_camera

################################

def sample_query_img_per(extrinsics, intrinsics, sensor_limits, query_img, room_xyz):
    Xformed_pc = torch.matmul(extrinsics, room_xyz)
    all_proj = (torch.matmul(intrinsics, Xformed_pc) / (torch.abs(Xformed_pc[2]) + torch.finfo(torch.float32).eps)).t()
    # filter everything out of sensor
    filter = (all_proj[:,2]>0) &\
        (all_proj[:,0]<=sensor_limits["sensor_x_max"]) & (all_proj[:,0]>=sensor_limits["sensor_x_min"]) &\
        (all_proj[:,1]<=sensor_limits["sensor_y_max"]) & (all_proj[:,1]>=sensor_limits["sensor_y_min"])
    all_proj_x = all_proj[filter][:,0]
    all_proj_y = all_proj[filter][:,1] * sensor_limits["aspect_ratio"]
    
    sampled_vectorized = fn.grid_sample(
        input = query_img.permute(2,0,1).unsqueeze(0),
        grid = torch.vstack((all_proj_x, all_proj_y)).permute(1,0).unsqueeze(0).unsqueeze(0),
        padding_mode = 'zeros',
        mode = 'bilinear',
        align_corners = False)
    
    # to apotelesma exei mikos ton arithmo ton vertices pou perasan to filtro
    return torch.clamp(sampled_vectorized.permute(0,2,3,1).squeeze(0).squeeze(0), min=0, max=255), filter

################################

def calculate_extrinsics(k, device):
    # https://en.wikipedia.org/wiki/Rotation_matrix (α=roll_rad|z, β=yaw_rad|y, γ=pitch_rad|x) and just use the Inverse of it
    x_trans = k[0]
    y_trans = k[1]
    z_trans = k[2]
    yaw_rad = k[3]
    # -yaw + pi to be the same as our renders in blender
    yaw_rad = -yaw_rad + np.pi
    pitch_rad = k[4]
    roll_rad = k[5]
    
    ext_00 = (torch.cos(roll_rad) * torch.cos(yaw_rad)).unsqueeze(0)
    ext_01 = (torch.cos(roll_rad) * torch.sin(yaw_rad) * torch.sin(pitch_rad) - torch.sin(roll_rad) * torch.cos(pitch_rad)).unsqueeze(0)
    ext_02 = (torch.cos(roll_rad) * torch.sin(yaw_rad) * torch.cos(pitch_rad) + torch.sin(roll_rad) * torch.sin(pitch_rad)).unsqueeze(0)
    ext_03 = x_trans.unsqueeze(0)
    ext_0 = torch.cat((ext_00, ext_01, ext_02, ext_03), dim=0)

    ext_10 = (torch.sin(roll_rad) * torch.cos(yaw_rad)).unsqueeze(0)
    ext_11 = (torch.sin(roll_rad) * torch.sin(yaw_rad) * torch.sin(pitch_rad) + torch.cos(roll_rad) * torch.cos(pitch_rad)).unsqueeze(0)
    ext_12 = (torch.sin(roll_rad) * torch.sin(yaw_rad) * torch.cos(pitch_rad) - torch.cos(roll_rad) * torch.sin(pitch_rad)).unsqueeze(0)
    ext_13 = y_trans.unsqueeze(0)
    ext_1 = torch.cat((ext_10, ext_11, ext_12, ext_13), dim=0)

    ext_20 = -torch.sin(yaw_rad).unsqueeze(0)
    ext_21 = (torch.cos(yaw_rad) * torch.sin(pitch_rad).unsqueeze(0))
    ext_22 = (torch.cos(yaw_rad) * torch.cos(pitch_rad)).unsqueeze(0)
    ext_23 = z_trans.unsqueeze(0)
    ext_2 = torch.cat((ext_20, ext_21, ext_22, ext_23), dim=0)

    ext_3 = torch.tensor((0,0,0,1), dtype=torch.float32, device=device)

    Ext = torch.vstack((ext_0, ext_1, ext_2, ext_3))
    Ext_inv = torch.linalg.inv(Ext)
    return Ext_inv

################################

def initial_poses_from_exr(room_bbox, args_inner, device):
    room_exr = cv2.imread(args_inner.room_exr, cv2.IMREAD_ANYDEPTH).clip(0, args_inner.max_valid_depth_m)
    img_h = room_exr.shape[0]
    img_w = room_exr.shape[1]
    sgrid = grid.create_spherical_grid(img_w)

    # First, create translations Ts
    Ts = [np.zeros(3)]
    count_attempts = 0
    count_T = 1
    while True:
        count_attempts += 1
        if count_attempts >= args_inner.init_max_attempts or count_T >= args_inner.init_T: break
        
        img_u = int(random.uniform(0, img_w))
        img_v = int(random.uniform(0, img_h))
        max_depth_at_img_uv = room_exr[img_v][img_u]
        depth_upper = max(0, max_depth_at_img_uv - args_inner.min_distance_from_end_m)
        depth_lower = min(max_depth_at_img_uv, args_inner.min_distance_between_poses_m)
        if depth_lower > depth_upper: continue
        if args_inner.better_distribution:
            chosen_depth = depth_lower + (depth_upper-depth_lower) * np.sqrt(random.random())
        else:
            chosen_depth = random.uniform(depth_lower, depth_upper)

        uv_to_xyz_at_chosen_depth = cartesian.coords_3d(sgrid, chosen_depth)[0]
        vertex = (
            uv_to_xyz_at_chosen_depth[0][img_v][img_u],
            uv_to_xyz_at_chosen_depth[1][img_v][img_u],
            uv_to_xyz_at_chosen_depth[2][img_v][img_u],
        )
        T = np.asarray(vertex)

        if T[1] > room_bbox['y_max'] - args_inner.min_dist_from_ceiling_m or T[1] < room_bbox['y_min'] + args_inner.min_dist_from_floor_m:
            continue

        discard_pose = False
        for k in Ts:
            if np.linalg.norm(T - k) < args_inner.min_distance_between_poses_m:
                discard_pose = True
                break
        if discard_pose: continue

        Ts.append(T)
        count_T += 1

    # Second, create rotations
    init_P = []
    for k in Ts:
        yaw_offset_deg = random.uniform(0, 360)
        for m in range(args_inner.init_views_per_T):
            yaw = (m * 360.0 / args_inner.init_views_per_T + yaw_offset_deg) % 360
            yaw *= np.pi / 180.0
            pitch = random.uniform(args_inner.min_pitch_deg, args_inner.max_pitch_deg) * (random.getrandbits(1) * 2 - 1)
            pitch *= np.pi / 180.0
            roll = random.uniform(args_inner.min_roll_deg, args_inner.max_roll_deg) * (random.getrandbits(1) * 2 - 1)
            roll *= np.pi / 180.0
            init_P.append([k[0], k[1], k[2], yaw, pitch, roll])
            
    init_P = torch.tensor(init_P, dtype=torch.float32, device=device)
    return init_P

################################

def initial_poses_from_pc(room_bbox, args_inner, device):
    # Create translations Ts
    Ts = [np.zeros(3)]
    count_attempts = 0
    count_T = 1
    while True:
        count_attempts += 1
        if count_attempts >= args_inner.init_max_attempts or count_T >= args_inner.init_T: break
        
        if room_bbox['x_min'] + args_inner.min_distance_from_end_m > room_bbox['x_max'] - args_inner.min_distance_from_end_m \
            or room_bbox['y_min'] + args_inner.min_dist_from_ceiling_m > room_bbox['y_max'] - args_inner.min_dist_from_floor_m \
            or room_bbox['z_min'] + args_inner.min_distance_from_end_m > room_bbox['z_max'] - args_inner.min_distance_from_end_m:
            break
        
        vertex = (
            random.uniform(room_bbox['x_min'] + args_inner.min_distance_from_end_m, room_bbox['x_max'] - args_inner.min_distance_from_end_m),
            random.uniform(room_bbox['y_min'] + args_inner.min_dist_from_ceiling_m, room_bbox['y_max'] - args_inner.min_dist_from_floor_m),
            random.uniform(room_bbox['z_min'] + args_inner.min_distance_from_end_m, room_bbox['z_max'] - args_inner.min_distance_from_end_m),
        )
        T = np.asarray(vertex)

        discard_pose = False
        for k in Ts:
            if np.linalg.norm(T - k) < args_inner.min_distance_between_poses_m:
                discard_pose = True
                break
        if discard_pose: continue

        Ts.append(T)
        count_T += 1

    # Create rotations
    init_P = []
    for k in Ts:
        yaw_offset_deg = random.uniform(0, 360)
        for m in range(args_inner.init_views_per_T):
            yaw = (m * 360.0 / args_inner.init_views_per_T + yaw_offset_deg) % 360
            yaw *= np.pi / 180.0
            pitch = random.uniform(args_inner.min_pitch_deg, args_inner.max_pitch_deg) * (random.getrandbits(1) * 2 - 1)
            pitch *= np.pi / 180.0
            roll = random.uniform(args_inner.min_roll_deg, args_inner.max_roll_deg) * (random.getrandbits(1) * 2 - 1)
            roll *= np.pi / 180.0
            init_P.append([k[0], k[1], k[2], yaw, pitch, roll])
            
    init_P = torch.tensor(init_P, dtype=torch.float32, device=device)
    return init_P

################################

def initial_poses_from_inertio(init_point_xyz, room_bbox, args_inner, device):
    init_poses_subset = np.array([init_point_xyz, [init_point_xyz[0], room_bbox['y_min'] + args_inner.min_dist_from_ceiling_m, init_point_xyz[2]], [init_point_xyz[0], room_bbox['y_max'] - args_inner.min_dist_from_floor_m, init_point_xyz[2]]])
    init_P = []
    for k in init_poses_subset:
        yaw_offset_deg = random.uniform(0, 360)
        for m in range(args_inner.init_views_per_T):
            yaw = (m * 360.0 / args_inner.init_views_per_T + yaw_offset_deg) % 360
            yaw *= np.pi / 180.0
            pitch = random.uniform(args_inner.min_pitch_deg, args_inner.max_pitch_deg) * (random.getrandbits(1) * 2 - 1)
            pitch *= np.pi / 180.0
            roll = random.uniform(args_inner.min_roll_deg, args_inner.max_roll_deg) * (random.getrandbits(1) * 2 - 1)
            roll *= np.pi / 180.0
            init_P.append([k[0], k[1], k[2], yaw, pitch, roll])
        
    init_P = torch.tensor(init_P, dtype=torch.float32, device=device)
    return init_P

################################

def initial_poses_around_a_point(room_bbox, args_inner, device):
    # Create translations Ts
    Ts = [np.array(args_inner.init_point_xyz)]
    count_attempts = 0
    count_T = 1
    while True:
        count_attempts += 1
        if count_attempts >= args_inner.init_max_attempts or count_T >= args_inner.init_T: break
        
        if room_bbox['x_min'] + args_inner.min_distance_from_end_m > room_bbox['x_max'] - args_inner.min_distance_from_end_m \
            or room_bbox['y_min'] + args_inner.min_dist_from_floor_m > room_bbox['y_max'] - args_inner.min_dist_from_ceiling_m \
            or room_bbox['z_min'] + args_inner.min_distance_from_end_m > room_bbox['z_max'] - args_inner.min_distance_from_end_m:
            break
        
        vertex = (
            np.clip(random.uniform(args_inner.init_point_xyz[0] - args_inner.init_point_max_translation_m, args_inner.init_point_xyz[0] + args_inner.init_point_max_translation_m),
                    a_min=room_bbox['x_min'] + args_inner.min_distance_from_end_m, a_max=room_bbox['x_max'] - args_inner.min_distance_from_end_m),
            np.clip(random.uniform(args_inner.init_point_xyz[1] - args_inner.init_point_max_translation_m, args_inner.init_point_xyz[1] + args_inner.init_point_max_translation_m), 
                    a_min=room_bbox['y_min'] + args_inner.min_dist_from_floor_m, a_max=room_bbox['y_max'] - args_inner.min_dist_from_ceiling_m),
            np.clip(random.uniform(args_inner.init_point_xyz[2] - args_inner.init_point_max_translation_m, args_inner.init_point_xyz[2] + args_inner.init_point_max_translation_m),
                    a_min=room_bbox['z_min'] + args_inner.min_distance_from_end_m, a_max=room_bbox['z_max'] - args_inner.min_distance_from_end_m),
        )
        T = np.asarray(vertex)

        discard_pose = False
        for k in Ts:
            if np.linalg.norm(T - k) < args_inner.min_distance_between_poses_m:
                discard_pose = True
                break
        if discard_pose: continue

        Ts.append(T)
        count_T += 1

    # Create rotations
    init_P = []
    for k in Ts:
        yaw_offset_deg = random.uniform(0, 360)
        for m in range(args_inner.init_views_per_T):
            yaw = (m * 360.0 / args_inner.init_views_per_T + yaw_offset_deg) % 360
            yaw *= np.pi / 180.0
            pitch = random.uniform(args_inner.min_pitch_deg, args_inner.max_pitch_deg) * (random.getrandbits(1) * 2 - 1)
            pitch *= np.pi / 180.0
            roll = random.uniform(args_inner.min_roll_deg, args_inner.max_roll_deg) * (random.getrandbits(1) * 2 - 1)
            roll *= np.pi / 180.0
            init_P.append([k[0], k[1], k[2], yaw, pitch, roll])
            
    init_P = torch.tensor(init_P, dtype=torch.float32, device=device)
    return init_P

################################

def bbox(room_xyz):
    return {
        "x_min": room_xyz[0].min(),
        "x_max": room_xyz[0].max(),
        "y_min": room_xyz[1].min(),
        "y_max": room_xyz[1].max(),
        "z_min": room_xyz[2].min(),
        "z_max": room_xyz[2].max()
    }
    
################################

def sensor_plane_z(fov):
    return 1 / np.tan(fov * 0.5 * np.pi / 180.0)

################################

def sensor_limits(aspect_ratio):
    return {
        "sensor_x_max": 1.0,
        "sensor_x_min": -1.0,
        "sensor_y_max": 1.0 / aspect_ratio,
        "sensor_y_min": -1.0 / aspect_ratio,
        "aspect_ratio": aspect_ratio
    }
    
################################

def calculate_intrinsics(sensor_plane_z, device):
    intrinsics = np.zeros((3,4))
    intrinsics[0][0] = sensor_plane_z
    intrinsics[1][1] = sensor_plane_z
    intrinsics[2][2] = 1
    intrinsics = torch.tensor(intrinsics, dtype=torch.float32, device=device)
    return intrinsics

################################

def init_poses_subset(init_poses, init_point, radius, device):
    init_point = torch.tensor(init_point, device=device)
    init_point = init_point.repeat(init_poses.size()[0], 1)
    L2 = torch.norm(init_poses[:,0:3] - init_point, p=2, dim=1)
    return init_poses[L2 < radius]
    
################################

def distance_between_global_coordinates(coord_center_lat, coord_center_lon, coord_position_lat, coord_position_lon, model_north):
    center = (coord_center_lat, coord_center_lon)
    point_to_measure_lon_distance = (coord_center_lat, coord_position_lon)
    point_to_measure_lat_distance = (coord_position_lat, coord_center_lon)

    distance_lon = geopy.distance.geodesic(center, point_to_measure_lon_distance).m * np.sign(coord_position_lon - coord_center_lon)
    distance_lat = geopy.distance.geodesic(center, point_to_measure_lat_distance).m * np.sign(coord_position_lat - coord_center_lat)

    theta = (- model_north) * np.pi / 180

    x = distance_lon*math.cos(theta) - distance_lat*math.sin(theta)
    z = distance_lat*math.cos(theta) + distance_lon*math.sin(theta)

    return x, z

################################

'''
    X = right
    Y = down
    Z = forward
    dx (meters), dy (meters), dz (meters) = 3d model's local coordinates according to the assumptions above
    model_lat (GPS), model_lon (GPS), model_alt (meters) = 3d model's global gps coordinates
    dyaw (radians), model_north (degrees) = right rotation. model_north is the offset of the model's forward axis (Z) with the North
'''
def transform_to_earth_coordinates(dx, dy, dz, dyaw, model_lat, model_lon, model_alt, model_north):
    # based on FASTER codebase
    r1 = 6378137
    r2 = 6356752
    
    R = math.sqrt( ( (r1**2*math.cos(model_lat*math.pi/180))**2 + (r2**2*math.sin(model_lat*math.pi/180))**2) /
            ((r1*math.cos(model_lat*math.pi/180))**2 +(r2*math.sin(model_lat*math.pi/180))**2 ))
    
    d = math.sqrt(dx*dx + dz*dz) # distance from local 0,0

    if dz==0:
        b = 90*np.sign(dx)
    else:
        if dz>0:
            b = math.atan(dx/dz) * 180 / np.pi # angle on local XZ plane
        else:
            b = 180 + math.atan(-dx/dz) * 180 / np.pi

    b += model_north % 360
    
    lat = math.degrees(math.asin( math.sin(math.radians(model_lat))*math.cos((d/R)) +
            math.cos(math.radians(model_lat))*math.sin((d/R))*math.cos(math.radians(b)) ))
    
    lon = model_lon + math.degrees(math.atan2( 
            math.sin(math.radians(b))*math.sin( (d/R))*math.cos(math.radians(model_lat)),
            math.cos( (d/R))-math.sin(math.radians(model_lat))*math.sin(math.radians(lat)) 
            ))
    
    alt = model_alt - dy
    
    hea = (dyaw * 180 / np.pi + model_north) % 360

    return lat, lon, alt, hea

################################

def make_json(ToolName, ToolId, lat, lon, alt, hea, dx, dy, dz, dyaw, dpitch, droll, extID, frID):
    # header
    json_msg= {}
    json_msg['toolName'] = ToolName
    json_msg['toolID'] = ToolId
    json_msg['broadcast'] = True
            
    # body
    json_data = {}
    json_data['category'] = 'VisualSelfLoc#FRLocation'
    json_data['startTS'] = datetime.datetime.now().isoformat()
    json_location = {}
    json_location['geometryType'] = 'Point'
    json_location['coordinatePairs'] = [float(lat), float(lon)]
    json_data['locationData'] = json_location
    json_source = {}
    json_source['extID'] = extID
    json_source['frID'] = frID
    json_source['deviceSourceType'] = 'VisualSelfLoc'
    json_indata={}
    json_indata['type'] = 'SelfLocData'
    json_indata['creationTS'] = datetime.datetime.now().isoformat()
    json_indata['source'] = json_source
    json_tooldata={}
    json_tooldata['latitude'] = float(lat)
    json_tooldata['longitude'] = float(lon)
    json_tooldata['mounting'] = 'helmet'
    json_indata['toolData'] = [json_tooldata]
    json_includedData = [json_indata] 
    json_data['toolPayload'] = json_includedData
    json_msg['infoprioPayload'] = json_data    
    return json.dumps(json_msg)   
    
################################

def make_json_new(toolID, sourceID, category, type, startTS, latitude=None, longitude=None, heading=None, altitude=None, mounting=None, quality=None, qualityHeading=None, outdoor=None, broadcast=True):
    json_msg= {}
    json_msg['toolID'] = toolID
    json_msg['sourceID'] = sourceID
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
    
################################

def align_model_north():
    '''
    To use: 
    1) Create a 3d point inside the pointcloud which can be easily located on the building blueprints.
    2) Call it manually and draw on the blueprints all the point produced.
    3) It produces one point for every 10 degrees.
    '''
    reference_point_x = 0.0
    reference_point_z = 15.0
    model_latitude = 45.1959498360304
    model_longtitude = 6.667389106165433
    for degrees in range(0,359,10):
        [a,b,c,d] = transform_to_earth_coordinates(
            reference_point_x, 0, reference_point_z, 0, model_latitude, model_longtitude, 0, degrees)
        print("[ " + str(a) + ", ", str(b), "],")
    #degrees = 60
    #[a,b,c,d] = transform_to_earth_coordinates(
    #    reference_point_x, 0, reference_point_z, 0, model_latitude, model_longtitude, 0, degrees)
    #print("[ " + str(a) + ", ", str(b), "],")
        
################################

def filter_image(pointcloud_torch, query_numpy):
    pointcloud_numpy = pointcloud_torch.unsqueeze(0).cpu().detach().numpy()
    filtered_image = histogram_matching.match_histograms(query_numpy, pointcloud_numpy)
    return filtered_image

################################
