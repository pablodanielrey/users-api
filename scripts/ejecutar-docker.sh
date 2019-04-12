#!/bin/bash
docker run -ti -v $(pwd):/tmp --env-file ../.env users-api:v2 bash