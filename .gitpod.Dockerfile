FROM gitpod/workspace-full-vnc

USER root

RUN apt-get update \
 && apt-get install -y libx11-dev libxkbfile-dev libsecret-1-dev libgconf-2–4 libnss3

USER gitpod