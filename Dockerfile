FROM python:3.8-slim-buster

# Install apt-get packages
#  - curl required to install nodejs required by ipywidgets
#  - gcc, python3-dev - required to build psutil
#  - git, ssh - required to pip install from private repos
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl gcc git python3-dev ssh

# Upgrade pip
RUN pip install --upgrade pip

# Additional dependencies for Jupyter Notebooks
RUN pip install nbdime==2.1.0
RUN pip install ipywidgets==7.6.2
RUN pip install jupyterlab==2.2.9

RUN curl -sL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
RUN jupyter labextension install @ijmbarr/jupyterlab_spellchecker
RUN jupyter labextension install jupyterlab-drawio
RUN jupyter labextension install nbdime-jupyterlab

# Lock nbconvert <6.0.0 to avoid a bug
RUN pip install nbconvert==5.6.1

# Development
RUN pip install pylint

# Create and switch to non-root user
# - this is mainly so files created in mounted volumes have normal permissions
RUN useradd -ms /bin/bash appuser
USER appuser

# # Required to run Jupyter as non-root
# ENV HOME="/root"
# RUN chmod a+rwx /root

ENV SHELL="/bin/bash"
ENV PYTHONPATH="/home/appuser/app"

COPY --chown=appuser:appuser . /home/appuser/app
WORKDIR /home/appuser/app

# Container Setup
RUN bash /home/appuser/app/scripts/container_setup.bash

ENTRYPOINT ["/bin/bash", "/home/appuser/app/launch.bash"]

# Build like this
# docker build -t marcin-brain .
