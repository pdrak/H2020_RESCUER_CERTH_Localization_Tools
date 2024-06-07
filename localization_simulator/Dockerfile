FROM python:3.10.5-slim

RUN apt-get update && apt-get install -y \
    python3-tk 
RUN apt-get install -y --no-install-recommends libboost-all-dev
RUN apt-get install sudo

RUN pip install --upgrade pip

ENV DISPLAY=host.docker.internal:0
WORKDIR /localization_simulator
RUN mkdir -p ./code
COPY ./code ./code
COPY ./disk2.png ./
COPY ./load4.png ./
COPY ./send2.png ./
COPY ./requirements.txt ./

RUN pip install -r requirements.txt

# PORT-FORWARDING
EXPOSE 1883

#ENTRYPOINT sh docker_entrypoint.sh
CMD ["python", "./code/print_path.py"]

