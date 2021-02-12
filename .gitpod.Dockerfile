FROM gitpod/workspace-full-vnc

USER root

RUN apt-get update \
    && apt-get install -y apt-utils libx11-dev libxkbfile-dev libsecret-1-dev \
       libgconf2-dev libnss3 libgtk-3-dev libasound2-dev twm \
    && apt-get clean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

USER gitpod