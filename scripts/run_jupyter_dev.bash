#!/bin/bash

docker run -it --rm \
  -p 9999:9999 \
  -v $PWD:/app \
  --entrypoint=jupyter \
  marcin-brain lab \
    --ip=0.0.0.0 --port=9999 --allow-root
