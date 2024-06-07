################################
### CERTH Drakoulis, Karavarsamis
################################

xhost +local:docker

export CAP_FPS=2
export CAMERA_PROXY_PORT=8555
export CAMERA_TYPE="GOPRO_HERO10" # CAMERA_TYPE: GOPRO_MAX, GOPRO_HERO10
export BROKER_IP="127.0.0.1"
export QR1_LAT="40.5578374"
export QR1_LON="23.0220602"
export QR1_ALT="1.9"
export QR2_LAT="40.5578705"
export QR2_LON="23.0219697"
export QR2_ALT="1.9"
export QR3_LAT="40.5578288"
export QR3_LON="23.0219523"
export QR3_ALT="1.9"
export MODE="LOC_ONESHOT"
export GLT_CALIB="False"
export LAZY_START="True"

sudo docker run \
    -it --gpus=all --net=host --privileged -p 8554:8554 \
    --env="DISPLAY" \
    --env CAP_FPS=$CAP_FPS \
    --env CAMERA_TYPE=$CAMERA_TYPE \
    --env BROKER_IP=$BROKER_IP \
    --env CAMERA_PORT=$CAMERA_PROXY_PORT \
    --env MAX_SCALE_FACTOR="1.0" \
    --env HERO_SCALE_FACTOR="1.0" \
    --env MODE=$MODE \
    --env QR1_LAT=$QR1_LAT \
    --env QR1_LON=$QR1_LON \
    --env QR1_ALT=$QR1_ALT \
    --env QR2_LAT=$QR2_LAT \
    --env QR2_LON=$QR2_LON \
    --env QR2_ALT=$QR2_ALT \
    --env QR3_LAT=$QR3_LAT \
    --env QR3_LON=$QR3_LON \
    --env QR3_ALT=$QR3_ALT \
    --env GLT_CALIB=$GLT_CALIB \
    --env LAZY_START=$LAZY_START \
    --name visual_loc_pano pdrak/visual_loc_pano:latest
    
xhost -local:docker
