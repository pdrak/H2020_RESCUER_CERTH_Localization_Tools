################################
### CERTH Drakoulis, Karavarsamis
################################

sudo docker cp visual_loc_pano:/tmp/stella_vslam/build/map.msg map.msg
sudo docker stop visual_loc_pano
sudo docker rm visual_loc_pano
