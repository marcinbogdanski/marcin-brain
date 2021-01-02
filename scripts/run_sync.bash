#!/bin/bash

docker run -it --rm \
  --network="host" \
  -v /home/marcin/marcin-notes:/mnt/marcin-notes \
  --entrypoint=python \
  marcin-brain scripts/jupyanki.py sync /mnt/marcin-notes Testing --debug
