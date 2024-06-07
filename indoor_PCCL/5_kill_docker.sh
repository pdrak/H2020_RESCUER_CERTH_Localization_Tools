sudo docker stop indoor_loc
FOLDER=$(date +%Y_%m_%d_%r)
mkdir -p Dumps
sudo docker cp "indoor_loc:/code/pccl" "./Dumps/$FOLDER"
sudo docker rm indoor_loc
