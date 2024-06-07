import os
import torch
import matplotlib.pyplot as plt

# Util function for loading meshes
from pytorch3d.io import load_objs_as_meshes, load_obj, load_ply

import pytorch3d.transforms
import open3d as o3d

import numpy as np
import time
import datetime
import torch.nn as nn

# Data structures and functions for rendering
from pytorch3d.structures import Meshes
from pytorch3d.vis.plotly_vis import AxisArgs, plot_batch_individually, plot_scene
from pytorch3d.vis.texture_vis import texturesuv_image_matplotlib
from pytorch3d.renderer import (
    look_at_view_transform,
    FoVPerspectiveCameras, 
    PointLights, 
    DirectionalLights, 
    Materials, 
    RasterizationSettings, 
    MeshRenderer, 
    MeshRasterizer,  
    SoftPhongShader,
    TexturesUV,
    TexturesVertex,
    SoftSilhouetteShader,
    HardFlatShader,
    look_at_rotation
    
)

import os
import torch
import numpy as np
from tqdm.notebook import tqdm
import imageio
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from skimage import img_as_ubyte

# io utils
from pytorch3d.io import load_obj

# datastructures
from pytorch3d.structures import Meshes, Pointclouds

# 3D transformations functions
from pytorch3d.transforms import Rotate, Translate

# rendering components
from pytorch3d.renderer import (
    FoVPerspectiveCameras, look_at_view_transform, look_at_rotation, 
    RasterizationSettings, MeshRenderer, MeshRasterizer, BlendParams,
    SoftSilhouetteShader, HardPhongShader, PointLights, TexturesVertex,PointsRasterizationSettings,
    PointsRenderer,
    PulsarPointsRenderer,
    PointsRasterizer,
    AlphaCompositor,
    NormWeightedCompositor
)

class Model(nn.Module):
    def __init__(self, meshes, renderer, image_ref):
        super().__init__()
        self.meshes = meshes
        self.device = meshes.device
        self.renderer = renderer
        
        # Get the silhouette of the reference RGB image by finding all non-white pixel values. 
        #image_ref = torch.from_numpy((image_ref[..., :3].max(-1) != 1).astype(np.float32))
        self.register_buffer('image_ref', image_ref)
        
        # Create an optimizable parameter for the x, y, z position of the camera. 
        self.camera_position = nn.Parameter(
            torch.from_numpy(np.array([3.0,  0, +2.5], dtype=np.float32)).to(meshes.device))

    def forward(self):
        
        # Render the image using the updated camera position. Based on the new position of the 
        # camera we calculate the rotation and translation matrices
        R = look_at_rotation(self.camera_position[None, :], device=self.device)  # (1, 3, 3)
        T = -torch.bmm(R.transpose(1, 2), self.camera_position[None, :, None])[:, :, 0]   # (1, 3)
        t1 = time.time()
        image = self.renderer(meshes_world=self.meshes.clone(), R=R, T=T)
        time_from(t1,"nice")
        
        # Calculate the silhouette loss
        loss = torch.sum((image[..., :3] - self.image_ref[..., :3]) ** 2)
        return loss, image

def time_from(start_time, description):
    end_time = time.time() - start_time
    delta_str = str(datetime.timedelta(seconds=end_time))
    print("\n" + description + ": " + delta_str)

# Set the cuda device 
if torch.cuda.is_available():
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
else:
    device = torch.device("cpu")

# # Set paths
# DATA_DIR = R"D:\dimpattas\rescuer_point_cloud\iPadscans\0\scans"
# obj_filename = os.path.join(DATA_DIR, "mesh_something_half_half.ply")

# # Load ply file
verts1, faces1, colors1 = load_ply(R"D:\dimpattas\rescuer_point_cloud\iPadscans\0\scans\mesh_something.ply")
tex = TexturesVertex(colors1.unsqueeze(0))

mesh = Meshes(verts=[verts1], faces=[faces1], textures=tex).to(device)

# Load point cloud
# pointcloud = np.load(R"D:\dimpattas\rescuer_point_cloud\iPadscans\0\scans\point_cloud.ply",allow_pickle=True)
pcd = o3d.io.read_point_cloud(R"D:\dimpattas\rescuer_point_cloud\iPadscans\0\scans\point_cloud_small.ply")
verts = torch.Tensor(np.asarray(pcd.points)).to(device)
rgb = torch.Tensor(np.asarray(pcd.colors)).to(device)
# verts = torch.Tensor(np.asarray(pcd.points)).to(device)
# rgb = torch.Tensor(np.asarray(pcd.colors)).to(device)
# room_ply = np.array(PlyData.read(R"D:\dimpattas\Datasets\M3D\1LXtFkjw3qL_48\1LXtFkjw3qL_48_spherical_1_pc.ply")["vertex"])
# # verts = torch.Tensor(np.stack((room_ply['x'],room_ply['y'],room_ply['z']),axis = 1)).to(device)
# # rgb = torch.Tensor(np.stack((room_ply['red'],room_ply['green'],room_ply['blue']), axis=1)).to(device)

# verts = torch.Tensor(pointcloud['verts']).to(device)       
# rgb = torch.Tensor(pointcloud['rgb']).to(device)

point_cloud = Pointclouds(points=[verts], features=[rgb])

# plt.figure(figsize=(7,7))
# texture_image=mesh.textures.maps_padded()
# plt.imshow(texture_image.squeeze().cpu().numpy())
# plt.axis("off")


R = pytorch3d.transforms.euler_angles_to_matrix(
    torch.tensor([np.pi/2, 0, np.pi]), "YXZ"
).unsqueeze(0) #yaw , pitch , roll
T = torch.Tensor([-1,1,0]).unsqueeze(0)  #ολα ειναι με μειον
cameras = FoVPerspectiveCameras(device=device, R=R, T=T, fov=84)

t0 = time.time()
# Define the settings for rasterization and shading. Here we set the output image to be of size
# 512x512. As we are rendering images for visualization purposes only we will set faces_per_pixel=1
# and blur_radius=0.0. Refer to raster_points.py for explanations of these parameters. 
raster_settings = PointsRasterizationSettings(
    image_size=512, 
    radius = 0.02,
    points_per_pixel = 100
)


# Create a points renderer by compositing points using an alpha compositor (nearer points
# are weighted more heavily). See [1] for an explanation.
rasterizer = PointsRasterizer(cameras=cameras, raster_settings=raster_settings)
renderer = PointsRenderer(
    rasterizer=rasterizer,
    compositor=AlphaCompositor()
)

images = renderer(point_cloud)
time_from(t0, "pointcloud time")
# plt.figure(figsize=(10, 10))
# plt.imshow(images[0, ..., :3].cpu().numpy())
# plt.axis("off");
# # plt.show()

t1 = time.time()
raster_settings = RasterizationSettings(
)


renderer = MeshRenderer(
    rasterizer=MeshRasterizer(
        cameras=cameras, 
        raster_settings=raster_settings
    ),
    shader=HardFlatShader(
        device=device, 
        cameras=cameras,
    )
)

images = renderer(mesh)
time_from(t1, "mesh time")
# t0 = time.time()
# images = renderer(mesh)
# time_from(t0, f"time to render")

# plt.figure(figsize=(10, 10))
# plt.imshow(images[0, ..., :3].cpu().numpy())
# plt.axis("off");
# plt.show()

# We will save images periodically and compose them into a GIF.
filename_output = "./teapot_optimization_demo.gif"
writer = imageio.get_writer(filename_output, mode='I', duration=0.3)

# Initialize a model using the renderer, mesh and reference image
model = Model(meshes=mesh, renderer=renderer, image_ref=images).to(device)

# Create an optimizer. Here we are using Adam and we pass in the parameters of the model
optimizer = torch.optim.Adam(model.parameters(), lr=0.05)

loop = tqdm(range(150))
for i in loop:

    optimizer.zero_grad()
    loss, _ = model()
    loss.backward()
    optimizer.step()
    
    loop.set_description('Optimizing (loss %.4f)' % loss.data)
    
    # Save outputs to create a GIF. 
    if i % 10 == 0:
        R = look_at_rotation(model.camera_position[None, :], device=model.device)
        T = -torch.bmm(R.transpose(1, 2), model.camera_position[None, :, None])[:, :, 0]   # (1, 3)
        image = renderer(meshes_world=model.meshes.clone(), R=R, T=T)
        image = image[0, ..., :3].detach().squeeze().cpu().numpy()
        image = img_as_ubyte(image)
        writer.append_data(image)
        
        # plt.figure()
        # plt.imshow(image[..., :3])
        # plt.title("iter: %d, loss: %0.2f" % (i, loss.data))
        # plt.axis("off")
    
writer.close()



pass



