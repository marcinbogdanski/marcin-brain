#!/usr/bin/env bash

# Startup script for Jupyter Lab and main entry point for this container

# Dump password into jupyter config file
# - source: https://jupyter-notebook.readthedocs.io/en/latest/public_server.html
# - we are skipping "jupyter notebook --generate-config" bacause it generates
#   file full of comments, might as well just echo single line we care about
# - JUPYTER_LAB_PASSWORD_HASH can be acquired with python script:
#    In [1]: from notebook.auth import passwd
#    In [2]: passwd(algorithm='sha1')
mkdir /root/.jupyter
echo "c.LabApp.password = '${JUPYTER_PASSWORD}'" > /root/.jupyter/jupyter_notebook_config.py

jupyter lab --ip=0.0.0.0 --port=${JUPYTER_PORT} --allow-root --no-browser
