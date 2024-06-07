FROM ubuntu:22.04
ENV DEBIAN_FRONTEND noninteractive

# install dependencies via apt
ENV DEBCONF_NOWARNINGS yes
RUN set -x && \
  apt-get update -y -qq && \
  apt-get upgrade -y -qq --no-install-recommends && \
  : "basic dependencies" && \
  apt-get install -y -qq \
    build-essential \
    pkg-config \
    python3.10 \
    python3.10-distutils \
    python3-pip \
    cmake \
    git \
    wget \
    curl \
    libcurl4-openssl-dev \
    libspdlog-dev \
    libspdlog1 \
    libomp-dev \
    libgomp1 \
    libjsoncpp-dev \
    libjsoncpp25 \
    libfmt8 \
    libfmt-dev \
    tar \
    bluez \
    dbus \
    iputils-ping \
    nano \
    unzip \
    make \
    sudo \
    bash \
    libc6 \
    libc++1 \
    unzip && \
  : "g2o dependencies" && \
  apt-get install -y -qq \
    libatlas-base-dev \
    libsuitesparse-dev \
    libglew-dev && \
  : "gtsam dependencies" && \
  apt-get install -y -qq \
    libboost-all-dev \
    libtbb-dev && \
  : "OpenCV dependencies" && \
  apt-get install -y -qq \
    libgtk-3-dev \
    libjpeg-dev \
    libpng++-dev \
    libtiff-dev \
    libopenexr-dev \
    libwebp-dev \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev && \
  : "backward-cpp dependencies" && \
  apt install -y -qq binutils-dev && \
  : "other dependencies" && \
  apt-get install -y -qq \
    libyaml-cpp-dev \
    sqlite3 \
    libsqlite3-dev \
    python3-pyzbar && \
  : "remove cache" && \
  apt-get autoremove -y -qq && \
  rm -rf /var/lib/apt/lists/*

# INSTALL PYTHON PACKAGES
RUN pip3 install html5lib==1.1
RUN pip3 install --upgrade pip
RUN pip3 install configargparse==1.5.3
RUN pip3 install numpy==1.23.3
RUN pip3 install paho-mqtt==1.6.1
RUN pip3 install Pillow==10.0.0
RUN pip3 install opencv-python
RUN pip3 install pynput==1.7.6
RUN pip3 install geopy==2.4.0
RUN pip3 install psutil==5.9.4

ARG CMAKE_INSTALL_PREFIX=/usr/local
ARG NUM_THREADS=16

ENV CPATH=${CMAKE_INSTALL_PREFIX}/include:${CPATH}
ENV C_INCLUDE_PATH=${CMAKE_INSTALL_PREFIX}/include:${C_INCLUDE_PATH}
ENV CPLUS_INCLUDE_PATH=${CMAKE_INSTALL_PREFIX}/include:${CPLUS_INCLUDE_PATH}
ENV LIBRARY_PATH=${CMAKE_INSTALL_PREFIX}/lib:${LIBRARY_PATH}
ENV LD_LIBRARY_PATH=${CMAKE_INSTALL_PREFIX}/lib:${LD_LIBRARY_PATH}

ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

# Eigen
ARG EIGEN3_VERSION=3.3.7
WORKDIR /tmp
RUN set -x && \
  wget -q https://gitlab.com/libeigen/eigen/-/archive/${EIGEN3_VERSION}/eigen-${EIGEN3_VERSION}.tar.bz2 && \
  tar xf eigen-${EIGEN3_VERSION}.tar.bz2 && \
  rm -rf eigen-${EIGEN3_VERSION}.tar.bz2 && \
  cd eigen-${EIGEN3_VERSION} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *
ENV Eigen3_DIR=${CMAKE_INSTALL_PREFIX}/share/eigen3/cmake

# g2o
ARG G2O_COMMIT=20230223_git
WORKDIR /tmp
RUN set -x && \
  git clone https://github.com/RainerKuemmerle/g2o.git && \
  cd g2o && \
  git checkout ${G2O_COMMIT} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_UNITTESTS=OFF \
    -DG2O_USE_CHOLMOD=OFF \
    -DG2O_USE_CSPARSE=ON \
    -DG2O_USE_OPENGL=OFF \
    -DG2O_USE_OPENMP=OFF \
    -DG2O_BUILD_APPS=OFF \
    -DG2O_BUILD_EXAMPLES=OFF \
    -DG2O_BUILD_LINKED_APPS=OFF \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *
ENV g2o_DIR=${CMAKE_INSTALL_PREFIX}/lib/cmake/g2o

# gtsam
ARG GTSAM_TAG=4.2a7
WORKDIR /tmp
RUN set -x && \
  git clone https://github.com/borglab/gtsam.git && \
  cd gtsam && \
  git checkout ${GTSAM_TAG} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DGTSAM_USE_SYSTEM_EIGEN=ON \
    -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
    -DGTSAM_BUILD_UNSTABLE=OFF \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *
ENV gtsam_DIR=${CMAKE_INSTALL_PREFIX}/lib/cmake/gtsam

# OpenCV
ARG OPENCV_VERSION=4.7.0
WORKDIR /tmp
RUN set -x && \
  wget -q https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip && \
  unzip -q ${OPENCV_VERSION}.zip && \
  rm -rf ${OPENCV_VERSION}.zip && \
  cd opencv-${OPENCV_VERSION} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
    -DBUILD_DOCS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_JASPER=OFF \
    -DBUILD_OPENEXR=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PROTOBUF=OFF \
    -DBUILD_opencv_apps=OFF \
    -DBUILD_opencv_dnn=OFF \
    -DBUILD_opencv_ml=OFF \
    -DBUILD_opencv_python_bindings_generator=OFF \
    -DENABLE_CXX11=ON \
    -DENABLE_FAST_MATH=ON \
    -DWITH_EIGEN=ON \
    -DWITH_FFMPEG=ON \
    -DWITH_TBB=ON \
    -DWITH_OPENMP=ON \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *
ENV OpenCV_DIR=${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv4

# Pangolin
ARG PANGOLIN_COMMIT=eab3d3449a33a042b1ee7225e1b8b593b1b21e3e
WORKDIR /tmp
RUN set -x && \
  git clone https://github.com/stevenlovegrove/Pangolin.git && \
  cd Pangolin && \
  git checkout ${PANGOLIN_COMMIT} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_PANGOLIN_DEPTHSENSE=OFF \
    -DBUILD_PANGOLIN_FFMPEG=OFF \
    -DBUILD_PANGOLIN_LIBDC1394=OFF \
    -DBUILD_PANGOLIN_LIBJPEG=OFF \
    -DBUILD_PANGOLIN_LIBOPENEXR=OFF \
    -DBUILD_PANGOLIN_LIBPNG=OFF \
    -DBUILD_PANGOLIN_LIBTIFF=OFF \
    -DBUILD_PANGOLIN_LIBUVC=OFF \
    -DBUILD_PANGOLIN_LZ4=OFF \
    -DBUILD_PANGOLIN_OPENNI=OFF \
    -DBUILD_PANGOLIN_OPENNI2=OFF \
    -DBUILD_PANGOLIN_PLEORA=OFF \
    -DBUILD_PANGOLIN_PYTHON=OFF \
    -DBUILD_PANGOLIN_TELICAM=OFF \
    -DBUILD_PANGOLIN_UVC_MEDIAFOUNDATION=OFF \
    -DBUILD_PANGOLIN_V4L=OFF \
    -DBUILD_PANGOLIN_ZSTD=OFF \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *
ENV Pangolin_DIR=${CMAKE_INSTALL_PREFIX}/lib/cmake/Pangolin

# backward-cpp
ARG BACKWARD_CPP_COMMIT=5ffb2c879ebdbea3bdb8477c671e32b1c984beaa
WORKDIR /tmp
RUN set -x && \
  git clone https://github.com/bombela/backward-cpp.git && \
  cd backward-cpp && \
  git checkout ${BACKWARD_CPP_COMMIT} && \
  mkdir -p build && \
  cd build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  cd /tmp && \
  rm -rf *

# FBow
WORKDIR /tmp/
RUN git clone https://github.com/stella-cv/FBoW
RUN set -x && \
  mkdir -p /tmp/FBoW/build && \
  cd /tmp/FBoW/build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    .. && \
  make -j${NUM_THREADS} && \
  make install

# tinycolormap
WORKDIR /tmp/
RUN git clone https://github.com/yuki-koyama/tinycolormap
RUN set -x && \
  mkdir -p /tmp/tinycolormap/build && \
  cd /tmp/tinycolormap/build && \
  cmake \
    -DCMAKE_BUILD_TYPE=Release \
    .. && \
  make -j${NUM_THREADS} && \
  make install

# stella_vslam
WORKDIR /tmp/
#RUN git clone https://github.com/stella-cv/stella_vslam
ADD stella_vslam /tmp/stella_vslam
RUN set -x && \
  cd /tmp/stella_vslam/build && rm -rf CMakeFiles && rm -f CMakeCache.txt && \
  cmake \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_BUILD_TYPE=Release \
    -DUSE_OPENMP=OFF \
    -DINSTALL_PANGOLIN_VIEWER=YES \
    -DUSE_GTSAM=ON \
    -DUSE_PANGOLIN_VIEWER=ON \
    -DUSE_OPENMP=ON \
    -DUSE_SSE_ORB=ON \
    -DUSE_SSE_FP_MATH=ON \
    -DBUILD_EXAMPLES=YES \
    .. && \
  make -j${NUM_THREADS} && \
  make install && \
  rm -rf CMakeCache.txt CMakeFiles Makefile cmake_install.cmake example src && \
  chmod -R 777 ./*

# MAKE CONTAINER FILESYSTEM AND EXTERNAL INSTALLATIONS
WORKDIR /
RUN mkdir action 
ADD exec /action
ADD code /code

# PORT-FORWARDING
EXPOSE 8554

# SET EXECUTION STARTING POINT
RUN chmod +rx /action/exec
ENV DISPLAY=host.docker.internal:0
ENTRYPOINT ["bash", "/action/exec"]
