# ADSScanExplorerService
## Logic
## Setup

### ADSScanExplorerService

Start the service by running the docker compose. Make sure to set the correct urls to the db and OpenSearch instance in config.py
```
docker compose -f docker/service/docker-compose.yaml up -d
```

### Cantaloupe

The image server retrieving the images from the S3 Bucket. S3 Bucket keys needs to be edited in the docker compose file docker-compose_cantaloupe.yaml. Then run the docker compose 

```
docker compose -f docker/cantaloupe/docker-compose.yaml up -d
```

Images should be accessible (if they have been uploaded).
Example url:
http://localhost:8182/iiif/2/bitmaps%2Fseri%2FApJ__%2F0333%2F600%2F0000352.000/full/full/0/default.jpg


## Usage