# Metis scientific backend

<p class="what_is_metis"><dfn>Metis</dfn> is an open scientific framework, materials data organizer, and collaborative online platform for the nanotechnology research. It was designed for the offline physical and online virtual autonomous laboratories dealing with the materials science. Metis is an AI-ready solution, aiming to bring the recent advances of computer science into a rather conservative area of new materials development and quality control. Metis currently focuses on the X-ray powder diffraction and atomistic simulations. Its development was started in 2021 in BASF (Ludwigshafen am Rhein, Germany) by Bernd Hinrichsen and Evgeny Blokhin.</p>

<p align="center"><img src="https://github.com/basf/metis-backend/blob/master/logo.png" width="300" /></p>

**This is the third part of the whole Metis infra: [GUI](https://github.com/basf/metis-gui) &rlarr; [BFF](https://github.com/basf/metis-bff) &rlarr; [backend](https://github.com/basf/metis-backend).**

Metis backend presents minimalistic utility toolset in materials informatics and Flask-based CRUD-server for the nano-scale crystalline data, XRPD measurements, and cloud simulations.


### Requirements

The basic requirements are **Python**, **Numpy**, and **PostgreSQL**. Note that the Numpy depends on the low-level Fortran numeric system libraries, which might be absent in your system. The Python dependency `xylib-py` requires C++ Boost stack to compile, install it on Debian with `apt-get install libboost-all-dev`.


A scientific cloud scheduler [yascheduler](https://github.com/tilde-lab/yascheduler) is required for a separate cloud orchestration. An optional requirement is [AiiDA](https://github.com/aiidateam/aiida-core), which can be linked to the cloud scheduler. The AiiDA is a Python framework for the complex scientific workflows, requiring PostgreSQL database and **RabbitMQ** message broker.

Thus, `metis-backend` consists of the 3 independent parts, each using PostgreSQL:

- `metis-backend` Python server per se
- `aiida_core` workflow engine
- `yascheduler` cloud scheduler

Optionally, a frontend server is **Nginx** (`conf/nginx.conf` goes to `/etc/nginx`), and all these guys are controlled by the **Supervisor** daemon (`conf/supervisord.conf` goes to `/etc/supervisor`).


## Installation

Refer to `conf/install.sh` for installation of Nginx, PostgreSQL, RabbitMQ, and Supervisor, as well as configuring them. Run `conf/install.sh` and then modify global options `conf/env.ini`. Alternatively, feel free to install each component on your own (or all together in a container, see below).

The AiiDA can be installed and configured separately. First, a possibility for _ssh-ing_ into a localhost should be ensured:

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

Run `supervisorctl status` to see all the services in Supervisor.

One by one, all the parts are managed as follows:

- `metis-backend` server is started with `index.py`
- `yascheduler` is started simply with `yascheduler` command
- AiiDA is managed with `verdi`, e.g. `verdi process list` or `verdi node show`
- AiiDA daemon is started separately with `verdi daemon start`
- PostgreSQL database(s) can be seen with `/data/pg/bin/psql -U postgres -l`
- RabbitMQ is controlled with `rabbitmqctl status`
- (Nginx can be added to Supervisor as well depending on your taste)

### Regular tasks

A script `scripts/assign_phases.py` should be run regularly to organize users' uploaded data, e.g. in cron job scheduler

`*/5 * * * * /path/to/metis-backend/scripts/assign_phases.py`


## Run in containers

This is an experimental feature intended primarily for the development and testing.

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

- XY and XYE patterns (TSV-alike)
- Bruker's RAW (*binary*)
- Bruker's Topas CLI modeling
- Synchrotron HDF5 NeXus (*binary*)


## License

Copyright 2021-2023 BASF SE

BSD 3-Clause
