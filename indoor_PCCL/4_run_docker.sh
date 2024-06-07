sudo docker run -it --gpus all --net=host --privileged -v ./volume:/code/volume/ --name indoor_loc docker.rescuer.inov.pt/indoor_loc:latest
