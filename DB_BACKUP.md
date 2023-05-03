## DB backups

Create a 'backups' directory
```bash
mkdir backups
```

Before backup stop all services and run only `db` service
```bash
docker compose stop
docker compose start db
```

Make a backup:
```bash
docker exec metis-db mkdir /backups
docker exec -e PGPASSWORD=password metis-db pg_dump -F c -U metis -h db -f /backups/db.dump metis
```

Copy a backup from a container to the host
```bash
docker cp metis-db:/backups/db.dump ./backups/db.dump
```

To restore a DB, copy the backup to the DB container
```bash
docker cp ./backups/db.dump metis-db:/backups/db.dump
```


Restore the DB
```bash
docker exec -e PGPASSWORD=password metis-db pg_restore -U metis -h db -c -d metis /backups/db.dump
```

Restore DB from a plain-text dump
```bash
docker exec -e PGPASSWORD=password metis-db psql -U metis -h db -d metis \
  -c "DROP SCHEMA public CASCADE;" \
  -c "CREATE SCHEMA public;" \
  -c "GRANT ALL ON SCHEMA public TO metis;" \
  -c "GRANT ALL ON SCHEMA public TO public;" \
  -c "COMMENT ON SCHEMA public IS 'standard public schema';"

docker cp ./backups/db.sql metis-db:/backups/db.sql

docker exec -e PGPASSWORD=password metis-db psql -U metis -h db -d metis -f /backups/db.sql
```

