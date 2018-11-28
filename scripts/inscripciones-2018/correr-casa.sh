sudo docker run -v $(pwd):/tmp/importar -v /home/pablo/Descargas/importacion:/tmp/i --env-file ../../.env --name importar --rm -ti users-api:v2 bash

