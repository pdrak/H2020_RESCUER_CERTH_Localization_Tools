################################
### CERTH Drakoulis, Karavarsamis
################################

xhost +local:docker

export CAP_FPS=2
export BROKER_IP="127.0.0.1"
export CAMERA_PORT=8555
export CAMERA_TYPE="GOPRO_HERO10" # CAMERA_TYPE: GOPRO_MAX, GOPRO_HERO10
export QR1_LAT="40.56671371791878"
export QR1_LON="22.99825556945781"
export QR1_ALT="1.0"
export QR2_LAT="40.56673346613334"
export QR2_LON="22.997958017999288"
export QR2_ALT="1.0"
export QR3_LAT="40.56680378391606"
export QR3_LON="22.997969744556126"
export QR3_ALT="1.0"
export MODE="USE_MAP"
export GLT_CALIB="False"

sudo docker run \
    -it --gpus=all --net=host --privileged -p 8554:8554 \
    -v `pwd`:/home/rescuer/Desktop/visual_loc_pano \
    --env="DISPLAY" \
    --env CAP_FPS=$CAP_FPS \
    --env CAMERA_TYPE=$CAMERA_TYPE \
    --env MAX_SCALE_FACTOR="1.0" \
    --env HERO_SCALE_FACTOR="1.0" \
    --env BROKER_IP=$BROKER_IP \
    --env CAMERA_PORT=$CAMERA_PORT \
    --env QR1_LAT=$QR1_LAT \
    --env QR1_LON=$QR1_LON \
    --env QR1_ALT=$QR1_ALT \
    --env QR2_LAT=$QR2_LAT \
    --env QR2_LON=$QR2_LON \
    --env QR2_ALT=$QR2_ALT \
    --env QR3_LAT=$QR3_LAT \
    --env QR3_LON=$QR3_LON \
    --env QR3_ALT=$QR3_ALT \
    --env MODE=$MODE \
    --env GLT_CALIB=$GLT_CALIB \
    --name visual_loc_pano pdrak/visual_loc_pano:latest
    
xhost -local:docker
