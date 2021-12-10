# XRPD data management: scientific backend

### Requirements

The core requirements are Python and Postgres. See `conf/install.sh`.

## Installation

Run `conf/install.sh` and then modify `conf/env.ini`.

Then setup your virtual env and install the Python requirements `pip install -r requirements.txt`.

## Running

Run `supervisorctl status` (see `conf/supervisord.conf` for details).

## License

Copyright 2021-2022 BASF SE

BSD 3-Clause
