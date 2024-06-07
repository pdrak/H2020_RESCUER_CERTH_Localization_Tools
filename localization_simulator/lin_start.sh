docker pull ioannagkika/localization_simulator
xhost +
sudo docker run -it --name simulator --net=host --env="DISPLAY" -v /home:/localization_simulator/C ioannagkika/localization_simulator
sudo docker rm --volumes simulator
xhost -
