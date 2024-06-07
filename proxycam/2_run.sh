################################
### CERTH Drakoulis, Karavarsamis
################################

export CAMERA_IP=""

export HOST_IP="127.0.0.1"
export CAMERA_PORT="8554"
export FORWARD_PORT_1="8555"
export FORWARD_PORT_2="8556"
export CMDS="stop,start" # commands: 'stop', 'start', 'exit'

xhost +local:docker

sudo docker run \
    -it --gpus=all --net=host --privileged \
    --env HOST_IP=$HOST_IP \
    --env CAMERA_IP=$CAMERA_IP \
    --env CAMERA_PORT=$CAMERA_PORT \
    --env FORWARD_PORT_1=$FORWARD_PORT_1 \
    --env FORWARD_PORT_2=$FORWARD_PORT_2 \
    --env CMDS=$CMDS \
    --name proxycam pdrak/proxycam:latest
    
xhost -local:docker
