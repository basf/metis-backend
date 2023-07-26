# Metis scientific backend

**This is the third part of the whole Metis infra: [GUI](https://github.com/basf/metis-gui) &rlarr; [BFF](https://github.com/basf/metis-bff) &rlarr; [backend](https://github.com/basf/metis-backend).**


### Requirements

The basic requirements are **Python**, **Numpy**, and **Postgres**. Note that the Numpy depends on the low-level Fortran numeric system libraries, which might be absent in your system.

Another core requirement is [AiiDA](https://github.com/aiidateam/aiida-core) as well as its plugin [yascheduler](https://github.com/tilde-lab/yascheduler), introducing a separate cloud orchestration. The AiiDA requires the **RabbitMQ** message broker.

Thus, `metis-backend` consists of the 3 independent parts, each using Postgres:

- `metis-backend` Python server
- `aiida_core` workflow engine
- `yascheduler` cloud manager

Optionally, a frontend server is **Nginx** (`conf/nginx.conf` goes to `/etc/nginx`), and all these guys are controlled by the **Supervisor** daemon (`conf/supervisord.conf` goes to `/etc/supervisor`).


## Installation

Refer to `conf/install.sh` for installation of Nginx, Postgres, RabbitMQ, and Supervisor, as well as configuring them. Run `conf/install.sh` and then modify global options `conf/env.ini`. Alternatively, feel free to install each component on your own (or all together in a container, see below).

The AiiDA should be installed and configured separately. First, a possibility for _ssh-ing_ into a localhost should be ensured:

```shell
ssh-keygen -t rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
ssh $USER@localhost
```

Then a `yascheduler` plugin is configured (`conf/yascheduler.conf` goes to `/etc/yascheduler`). After that run `yainit` to start a `yascheduler` service. Then, if you have already run `conf/install.sh` script, it should be enought to do:

```shell
pip install aiida_core
bash conf/aiida_setup.sh
```

Then setup your virtual env, if needed, and install the Python requirements as simply as`pip install -r requirements.txt`.

Finally, apply the database schema: `/data/pg/bin/psql -U postgres -d metis -f schema/schema.sql`.


## Running

Run `supervisorctl status` to see (almost) all the services in Supervisor.

One by one, all the parts are managed as follows:

- `metis-backend` server is started with `index.py`
- `yascheduler` is started simply with `yascheduler` command
- AiiDA is managed with `verdi`, e.g. `verdi process list` or `verdi node show`
- AiiDA daemon is started separately with `verdi daemon start`
- Postgres database(s) can be seen with `/data/pg/bin/psql -U postgres -l`
- RabbitMQ is controlled with `rabbitmqctl status`


## Run in containers

This is an experimental feature intended primarily for development and testing.

It is assumed that you have the `metis-backend`, `metis-bff`, and `metis-gui`
repositories cloned on the same level. Also, you need `docker` (or `podman`
and `podman-compose`) installed.

Now, you can run `docker compose up` (`podman-compose up`) in `metis-backend`
directory. This should start all dependencies and services.

`metis-gui` should be available at `http://localhost:10000/`

`metis-bff` should be available at `http://localhost:3000/`


## Recognized data formats


### Crystalline structures

- CIF
- POSCAR
- Optimade JSON


### XRPD data

- XY patterns (TSV-alike)
- Bruker's RAW (*binary*)
- Bruker's Topas CLI
- Synchrotron HDF5 (*binary*)


## License

Copyright 2021-2023 BASF SE

BSD 3-Clause
