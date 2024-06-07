docker pull ioannagkika/localization_simulator
docker run -it --name simulator1 -v C:/localization_simulator:/localization_simulator/C ioannagkika/localization_simulator
docker rm --volumes simulator1
pause