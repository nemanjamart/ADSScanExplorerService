# ADSScanExplorerService
## Logic
## Setup

### ADSScanExplorerService

Start the service by running the docker compose. Make sure to set the correct urls to the db and OpenSearch instance in config.py
```
docker compose -f docker/service/docker-compose.yaml up -d
```

### Cantaloupe

The image server retrieving the images from the S3 Bucket. S3 Bucket keys needs to be edited in the docker compose file docker-compose_cantaloupe.yaml. 

A cache folder is also mounted by default in our compose file to /src/cache. This is for having a local file system cache of the source images which speeds up the loading significantly. Make sure to mount a folder with decent capacity and permissions so that docker can write to it. It's not possible to limit the isze of the cache but the time_to_live. We've set it quite low by default to 1 hour which can be adjusted to keep the size in check. Use the commented enviroment parameter to completely disable the source cache.

Then run the docker compose 

```
docker compose -f docker/cantaloupe/docker-compose.yaml up -d
```

Images should be accessible (if they have been uploaded).
Example url:
<http://localhost:8182/iiif/2/bitmaps%2Fseri%2FApJ__%2F0333%2F600%2F0000352.000/full/full/0/default.jpg>

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

Setup the tables by running through the pipeline container:
```
docker exec -it ads_scan_explorer_service python setup_db.py [--re-create] 
```