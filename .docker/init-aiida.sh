#!/usr/bin/env bash

set -euo pipefail

: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGUSER:=aiida}"
: "${PGPASSWORD:=password}"
: "${PGDATABASE:=aiida}"
: "${RMQHOST:=localhost}"
: "${RMQPORT:=5672}"
: "${RMQUSER:=guest}"
: "${RMQPASSWORD:=password}"
: "${AIIDA_PROFILE_NAME:=default}"
: "${AIIDADB_BACKEND:=psql_dos}"
: "${AIIDA_REPO:=/data/aiida}"
: "${USER_EMAIL:=aiida@localhost}"
: "${USER_FIRST_NAME:=Giuseppe}"
: "${USER_LAST_NAME:=Verdi}"
: "${USER_INSTITUTION:=LaScala}"

echo "Create AiiDA repository directory..."
mkdir -p "${AIIDA_REPO}"

echo "Create default AiiDA profile..."
verdi profile show "$AIIDA_PROFILE_NAME" 2>/dev/null || verdi quicksetup \
    --non-interactive \
    --profile "${AIIDA_PROFILE_NAME}" \
    --repository "${AIIDA_REPO}" \
    --email "${USER_EMAIL}" \
    --first-name "${USER_FIRST_NAME}" \
    --last-name "${USER_LAST_NAME}" \
    --institution "${USER_INSTITUTION}" \
    --db-backend "${AIIDADB_BACKEND}" \
    --db-host "${PGHOST}" \
    --db-port "${PGPORT}" \
    --db-name "${PGDATABASE}" \
    --db-username "${PGUSER}" \
    --db-password "${PGPASSWORD}" \
    --broker-host "${RMQHOST}" \
    --broker-port "${RMQPORT}" \
    --broker-username "${RMQUSER}" \
    --broker-password "${RMQPASSWORD}" && \
    verdi profile setdefault "${AIIDA_PROFILE_NAME}"

echo "Setup yascheduler computer..."
verdi computer show yascheduler 2>/dev/null || verdi computer setup \
    --non-interactive \
    --label=yascheduler \
    --hostname=localhost \
    --transport core.local \
    --scheduler yascheduler \
    --work-dir="${AIIDA_REPO}"

verdi computer configure core.local yascheduler \
    --non-interactive \
    --safe-interval 1

verdi computer test yascheduler --print-traceback

verdi code show Dummy 2>/dev/null || verdi code setup \
    --non-interactive \
    --label=Dummy \
    --input-plugin=aiida_dummy \
    --on-computer \
    --computer=yascheduler \
    --remote-abs-path=/nonce

verdi storage migrate --force || echo "Database migration failed."
verdi status || true
