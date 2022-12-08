#!/bin/bash
set -euo pipefail

verdi setup --non-interactive --db-host localhost --db-port 5432 --db-name aiida --db-username postgres --db-password nonce --repository /data/aiida --email gv@tilde.pro --first-name Giuseppe --last-name Verdi --institution LaScala --profile default

verdi computer setup --non-interactive --label=yascheduler --hostname=localhost --transport=core.ssh --scheduler=yascheduler --work-dir=/data/aiida
verdi computer configure core.ssh --non-interactive --username=root --port=22 --key-filename=~/.ssh/id_rsa.pub --key-policy=AutoAddPolicy --safe-interval 1 yascheduler
verdi computer test yascheduler --print-traceback

verdi code setup --non-interactive --label=Pcrystal --input-plugin=crystal_dft.parallel --on-computer --computer=yascheduler --remote-abs-path=/nonce
verdi code setup --non-interactive --label=Dummy --input-plugin=aiida_dummy --on-computer --computer=yascheduler --remote-abs-path=/nonce
