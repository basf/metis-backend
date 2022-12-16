#!/usr/bin/env python3

import logging

from configparser import ConfigParser
from os import environ
from pathlib import Path

from pg8000.native import Connection as DB

log = logging.getLogger()

cfg_path = Path(__file__).parent.parent / "conf" / "env.ini"

if not cfg_path.exists():
    cfg_path.write_text((cfg_path.parent / "env.ini.sample").read_text())


# update config with env variables
log.info(f"Loading config file from {str(cfg_path)}...")
cfg = ConfigParser()
cfg.read(cfg_path)

for sec_name in ["api", "db", "webhooks"]:
    if sec_name not in cfg:
        cfg[sec_name] = {}

for key in ("host", "port", "user", "password", "database"):
    ekey = f"PG{key.upper()}"
    if environ.get(ekey) is not None:
        cfg["db"][key] = environ[ekey]

if environ.get("API_KEY") is not None:
    cfg["api"]["key"] = environ["API_KEY"]

for key in ("key", "calc_update", "calc_create"):
    ekey = f"WEBHOOKS_{key.upper()}"
    if environ.get(ekey) is not None:
        cfg["webhooks"][key] = environ[ekey]

with cfg_path.open("w") as fp:
    log.info(f"Saving updated config file to {str(cfg_path)}...")
    cfg.write(fp)

log.info("Initialize database...")
schema = (Path(__file__).parent.parent / "i_data" / "schema.sql").read_text()
db = DB(
    user=cfg["db"]["user"],
    host=cfg["db"]["host"],
    database=cfg["db"]["database"],
    port=cfg["db"]["port"],
    password=cfg["db"]["password"],
)
db.run(schema)
db.close()
