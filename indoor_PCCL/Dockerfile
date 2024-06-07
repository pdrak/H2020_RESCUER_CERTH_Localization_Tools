# CERTH-ITI-VCL3D

# INHERIT FROM BASE IMAGE
FROM nvcr.io/nvidia/cuda:11.6.0-cudnn8-devel-ubuntu20.04

# INSTALL PYTHON AND PIP
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && sudo apt upgrade -y; exit 0
RUN apt install software-properties-common -y
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt install python3.10 -y
RUN update-alternatives --install /usr/bin/python3 python /usr/bin/python3.10 1
RUN apt install curl -y
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# INSTALL THE REST OF THE PACKAGES
RUN apt-get update
RUN apt install -y bluez
RUN apt install -y dbus
RUN apt install -y iputils-ping
RUN apt install -y nano
RUN apt install -y sudo
RUN apt install -y unzip
RUN apt-get install -y python3-opencv

# INSTALL PYTHON PACKAGES
RUN pip install --upgrade pip
RUN pip install configargparse==1.5.3
RUN pip install goprocam==4.2.0
RUN pip install matplotlib==3.6.1
RUN pip install numpy==1.23.3
RUN pip install opencv-python==4.6.0.66
RUN pip install paho-mqtt==1.6.1
RUN pip install plyfile==0.7.4
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
RUN pip install geopy==2.3.0

# MAKE CONTAINER FILESYSTEM
RUN mkdir action 
ADD exec /action
ADD code /code

# PORT-FORWARDING
#EXPOSE 8554/udp

# SET EXECUTION STARTING POINT
RUN chmod +rx /action/exec
ENTRYPOINT ["bash", "/action/exec"]
