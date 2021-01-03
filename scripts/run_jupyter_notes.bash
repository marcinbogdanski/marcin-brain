#!/bin/bash

docker run -it --rm \
  -p 8890:8890 \
  -u $(id -u):$(id -g) \
  -v /home/marcin/marcin-notes:/mnt/marcin-notes \
  -w /mnt/marcin-notes \
  --entrypoint=jupyter \
  marcin-brain lab \
    --ip=0.0.0.0 --port=8890 --allow-root
