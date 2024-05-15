#!/bin/bash
set -euo pipefail

PG_VERSION="14.13" # NB subject to update
PG_SOURCE_ADDR=https://ftp.postgresql.org/pub/source/v$PG_VERSION/postgresql-$PG_VERSION.tar.gz

SETTINGS=(
postgresql.conf
supervisord.conf
)

for ((i=0; i<${#SETTINGS[@]}; i++)); do
    if [ ! -f $(dirname $0)/${SETTINGS[i]} ]; then
    echo "${SETTINGS[i]} does not exist" ; exit 1
    fi
done

apt-get -y update && apt-get -y upgrade
update-alternatives --install /usr/bin/python python /usr/bin/python3 1

apt-get install -y \
    build-essential \
    nginx \
    rabbitmq-server \
    p7zip-full \
    git \
    swig \
    pkg-config \
    zlib1g-dev \
    libreadline6-dev \
    libboost-all-dev \
    libatlas-base-dev \
    libopenblas-dev \
    libblas-dev \
    libffi-dev \
    liblapack-dev \
    supervisor \
    python3-setuptools \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
;

update-rc.d supervisor defaults
update-rc.d supervisor enable

echo "set mouse-=a" > ~/.vimrc

# Postgres compilation and installation

id -u postgres > /dev/null 2>&1 || useradd postgres
mkdir -p /data/pg/db
chown -R postgres:postgres /data/pg

wget $PG_SOURCE_ADDR
wget $PG_SOURCE_ADDR.md5
GOT_SUM=`md5sum *.tar.gz | cut -d" " -f1`
HAVE_SUM=`cut -d' ' -f1 < *.tar.gz.md5`
if [ "$GOT_SUM" != "$HAVE_SUM" ]; then
    echo "INVALID CHECKSUM"
    exit 1
fi

tar xvf postgresql-$PG_VERSION.tar.gz
cd postgresql-$PG_VERSION
./configure --prefix=/data/pg
make && make install

cd contrib/pgcrypto
PG_CONFIG=/data/pg/bin/pg_config make
PG_CONFIG=/data/pg/bin/pg_config make install

su postgres -c "/data/pg/bin/initdb -D /data/pg/db"
su postgres -c "/data/pg/bin/pg_ctl -D /data/pg/db -l /tmp/logfile start"
su postgres -c "/data/pg/bin/createdb metis"

# Other preparations

cd $(dirname $0)
cp postgresql.conf /data/pg/db/
cp supervisord.conf /etc/supervisor/
cp env.ini.sample env.ini

systemctl stop nginx
systemctl disable nginx
