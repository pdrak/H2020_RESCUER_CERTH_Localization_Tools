FROM ubuntu:22.04
ENV DEBIAN_FRONTEND noninteractive

# install dependencies via apt
ENV DEBCONF_NOWARNINGS yes
RUN set -x && \
  apt-get update -y -qq && \
  apt-get upgrade -y -qq --no-install-recommends && \
  : "basic dependencies" && \
  apt-get install -y -qq \
    pkg-config \
    python3.10 \
    python3.10-distutils \
    python3-pip \
    sudo \
    bash \
    curl

# INSTALL PYTHON PACKAGES
RUN pip3 install scipy==1.11.3
RUN pip3 install paho-mqtt==1.6.1
RUN pip3 install configargparse==1.7
RUN pip3 install psutil==5.9.7

ARG CMAKE_INSTALL_PREFIX=/usr/local
ARG NUM_THREADS=4

ENV CPATH=${CMAKE_INSTALL_PREFIX}/include:${CPATH}
ENV C_INCLUDE_PATH=${CMAKE_INSTALL_PREFIX}/include:${C_INCLUDE_PATH}
ENV CPLUS_INCLUDE_PATH=${CMAKE_INSTALL_PREFIX}/include:${CPLUS_INCLUDE_PATH}
ENV LIBRARY_PATH=${CMAKE_INSTALL_PREFIX}/lib:${LIBRARY_PATH}
ENV LD_LIBRARY_PATH=${CMAKE_INSTALL_PREFIX}/lib:${LD_LIBRARY_PATH}

# MAKE CONTAINER FILESYSTEM AND EXTERNAL INSTALLATIONS
WORKDIR /
RUN mkdir action 
ADD exec /action
ADD code /code

# SET EXECUTION STARTING POINT
RUN chmod +rx /action/exec
ENV DISPLAY=host.docker.internal:0
ENTRYPOINT ["bash", "/action/exec"]