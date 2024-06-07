################################
### CERTH Drakoulis, Karavarsamis
################################

xhost +local:docker

export BROKER_IP="127.0.0.1"
export TIME_WINDOW=2.0
export GAL_QUAL=100
export VIS_QUAL=80
export INE_QUAL=60
export USE_GAL="True"
export USE_VIS="True"
export USE_INE="True"
export FROM_TOOL="True"

sudo docker run \
    -it \
    --net=host \
    --env BROKER_IP=$BROKER_IP \
    --env TIME_WINDOW=$TIME_WINDOW \
    --env GAL_QUAL=$GAL_QUAL \
    --env VIS_QUAL=$VIS_QUAL \
    --env INE_QUAL=$INE_QUAL \
    --env USE_GAL=$USE_GAL \
    --env USE_VIS=$USE_VIS \
    --env USE_INE=$USE_INE \
    --env FROM_TOOL=$FROM_TOOL \
    --name fusion_loc pdrak/fusion_loc:latest
    
xhost -local:docker
