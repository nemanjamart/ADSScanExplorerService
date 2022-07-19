# ADSScanExplorerService

Micro service and image server for Scan Explorer
## Setup

### ADSScanExplorerService

Required configurations, such as database and open search, must be configured in config.py.

#### Running Scan Explorer Service
```
docker compose -f docker/service/docker-compose.yaml up -d
```

### Cantaloupe

The image server is setup to retrieve images from a S3 Bucket. A key need to be provided in docker-compose_cantaloupe.yaml.

A cache volume is required for good performance and can also be configured in the compose file, this will speed up consequent loads significantly. Make sure to mount a volume with adequate capacity and write permissions. The size of the cache can be controlled with ```CANTALOUPE_CACHE_SERVER_SOURCE_TTL_SECONDS```.

#### Running Cantaloupe
```
docker compose -f docker/cantaloupe/docker-compose.yaml up -d
```

### Database
Setup a postgresql container
```
docker compose -f docker/postgres/docker-compose.yaml up -d
```

Prepare the database:

```
docker exec -it postgres_service bash -c "psql -c \"CREATE ROLE scan_explorer WITH LOGIN PASSWORD 'scan_explorer';\""
docker exec -it postgres_service bash -c "psql -c \"CREATE DATABASE scan_explorer_service;\""
docker exec -it postgres_service bash -c "psql -c \"GRANT CREATE ON DATABASE scan_explorer_service TO scan_explorer;\""
```

Use alembic to setup the tables:
```
alembic upgrade head
```

## Tests

Run tests

```
python -m unittest scan_explorer_service/tests/test_*.py
```

## Documentation

Generate the appmap definitions

```
APPMAP=true python -m appmap.unittest scan_explorer_service/tests/test_*.py
```

Generate the OpenAPI documentation based on the appmap definitions

```
APPMAP=true npx @appland/appmap openapi --openapi-title "ScanExplorerService" -o service-openapi.yaml
```