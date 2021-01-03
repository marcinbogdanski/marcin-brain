#!/bin/bash

docker run -it --rm \
  --network="host" \
  -v $PWD:/app \
  --entrypoint=bash \
  marcin-brain
