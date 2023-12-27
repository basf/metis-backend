FROM docker.io/library/python:3.10-bullseye

WORKDIR /app

RUN apt-get update \
    && apt-get install -y libboost-dev postgresql-client swig wait-for-it xz-utils \
    && rm -rf /var/lib/apt/lists/*

# setup s6 init
ARG S6_OVERLAY_VERSION=3.1.2.1
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz
ENV S6_CMD_WAIT_FOR_SERVICES_MAXTIME 0
COPY .docker/s6-rc.d/ /etc/s6-overlay/s6-rc.d
ENTRYPOINT ["/init"]

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY ./conf/env.ini.sample ./conf/env.ini
