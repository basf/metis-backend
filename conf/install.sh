#!/bin/bash

apt-get -y update && apt-get -y upgrade
update-alternatives --install /usr/bin/python python /usr/bin/python3 1
apt-get -y install build-essential nginx libatlas-base-dev libopenblas-dev libblas-dev libffi-dev libreadline6-dev zlib1g-dev liblapack-dev supervisor python3-dev python3-pip python3-numpy python3-scipy python3-matplotlib p7zip-full git swig python3-setuptools rabbitmq-server pkg-config

update-rc.d supervisor defaults
update-rc.d supervisor enable

echo "set mouse-=a" > ~/.vimrc
mkdir /data
