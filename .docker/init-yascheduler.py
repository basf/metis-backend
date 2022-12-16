#!/usr/bin/env python

import logging
import urllib.request
import stat

from configparser import ConfigParser
from os import environ
from pathlib import Path

from pg8000.exceptions import DatabaseError

from yascheduler.config import Config
from yascheduler.utils import init as yainit
from yascheduler.variables import CONFIG_FILE

log = logging.getLogger()

# default minimal config
MIN_CONF = """
[db]
user =
password =
database =
host =
port = 5432

[engine.dummy]
deploy_local_files = dummyengine
spawn = {engine_path}/dummyengine *
check_pname = dummyengine
sleep_interval = 1
input_files = 1.input 2.input 3.input
output_files = 1.input 2.input 3.input 1.input.out 2.input.out 3.input.out
"""

cfgf = Path(CONFIG_FILE)

# create config if not exists
if not cfgf.exists():
    log.info(f"Config file {CONFIG_FILE} not exists - creating default...")
    if not cfgf.parent.exists():
        cfgf.parent.mkdir(parents=True)
    cfgf.write_text(MIN_CONF)

# update config with env variables
log.info(f"Loading config file from {CONFIG_FILE}...")
cfg = ConfigParser()
cfg.read(CONFIG_FILE)

for sec_name in ["db", "local"]:
    if sec_name not in cfg.sections():
        cfg[sec_name] = {}

for key in ("host", "port", "user", "password", "database"):
    ekey = f"PG{key.upper()}"
    if environ.get(ekey) is not None:
        cfg["db"][key] = environ[ekey]

if environ.get("YASCHEDULER_LOCAL_DATA_DIR"):
    cfg["local"]["data_dir"] = environ["YASCHEDULER_LOCAL_DATA_DIR"]
    Path(cfg["local"]["data_dir"]).mkdir(parents=True, exist_ok=True)
if environ.get("WEBHOOKS_KEY"):
    cfg["local"][
        "webhook_url"
    ] = f"http://localhost:7050/calculations/update?Key={environ['WEBHOOKS_KEY']}"

if (
    environ.get("HOME")
    and environ.get("YASCHEDULER_DUMMY_ENGINE_URL")
    and "engine.dummy" in cfg.sections()
):
    dummy_path = Path(environ["HOME"]) / "dummyengine"
    cfg["engine.dummy"]["deploy_local_files"] = str(dummy_path)
    if not dummy_path.exists():
        log.info("Downloading dummy engine ...")
        dummy_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(environ["YASCHEDULER_DUMMY_ENGINE_URL"]) as r:
            dummy_path.write_bytes(r.read())
        dummy_path.chmod(dummy_path.stat().st_mode | stat.S_IEXEC)


with cfgf.open("w") as fp:
    log.info(f"Saving updated config file to {CONFIG_FILE}...")
    cfg.write(fp)

log.info("Load config...")
yacfg = Config.from_config_parser(cfgf)
keys_dir = yacfg.local.keys_dir
if environ.get("HOME"):
    ssh_key_path = Path(environ["HOME"]) / ".ssh" / "id_rsa"
    if ssh_key_path.exists():
        log.info("Copy ssh private key...")
        if not keys_dir.exists():
            keys_dir.mkdir(parents=True, exist_ok=True)
        (Path(keys_dir) / "id_rsa").write_bytes(ssh_key_path.read_bytes())

log.info("Initialize yascheduler...")
try:
    yainit()
except DatabaseError as e:
    if "already exists" in str(e.args[0]):
        log.info("Database already initialized!")
except Exception as e:
    log.error(e)
    exit(1)
