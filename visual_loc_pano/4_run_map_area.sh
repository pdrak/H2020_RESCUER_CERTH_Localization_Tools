################################
### CERTH Drakoulis, Karavarsamis
################################

xhost +local:docker

export MODE="MAP"
export CAMERA_PORT=8555
export CAMERA_TYPE="GOPRO_HERO10" # CAMERA_TYPE: GOPRO_MAX, GOPRO_HERO10

sudo docker run \
    -it --gpus=all --net=host --privileged -p 8554:8554 \
    --env="DISPLAY" \
    --env MODE=$MODE \
    --env CAMERA_TYPE=$CAMERA_TYPE \
    --env CAMERA_PORT=$CAMERA_PORT \
    --env MAX_SCALE_FACTOR="1.0" \
    --env HERO_SCALE_FACTOR="1.0" \
    --name visual_loc_pano pdrak/visual_loc_pano:latest
    
xhost -local:docker
