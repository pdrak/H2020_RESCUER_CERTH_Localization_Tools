################################
### CERTH Drakoulis, Karavarsamis
################################

xhost +local:docker

export CAP_FPS=2
export BROKER_IP="127.0.0.1"
export CAMERA_PORT=8555
export CAMERA_TYPE="GOPRO_HERO10" # CAMERA_TYPE: GOPRO_MAX, GOPRO_HERO10
export MODE="USE_MAP_CALIBRATED"
export LAZY_START="False"

export BBOX_FILE_URL=""

export BBOX_UNAME=""
export BBOX_PASS=""

rm -f `basename $BBOX_FILE_URL` map.msg local_points.txt

wget --header="$BBOX_UNAME: $BBOX_PASS" $BBOX_FILE_URL

if [ $? -eq 0 ]; then
	unzip -d `pwd` `basename $BBOX_FILE_URL`

	if [ $? -eq 0 ]; then
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
		    --env QR1_LAT="0" \
		    --env QR1_LON="0" \
		    --env QR1_ALT="0" \
		    --env QR2_LAT="0" \
		    --env QR2_LON="0" \
		    --env QR2_ALT="0" \
		    --env QR3_LAT="0" \
		    --env QR3_LON="0" \
		    --env QR3_ALT="0" \
		    --env MODE=$MODE \
		    --env LAZY_START=$LAZY_START \
		    --name visual_loc_pano pdrak/visual_loc_pano:latest
	fi
fi

xhost -local:docker

