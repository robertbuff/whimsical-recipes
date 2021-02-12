FROM gitpod/workspace-full-vnc

USER root

RUN apt-get update \
    && apt-get install -y apt-utils libx11-dev libxkbfile-dev libsecret-1-dev \
       libgconf2-dev libnss3 libgtk-3-dev libasound2-dev twm snapd \
    && apt-get clean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# This is a bit of a hack. At the moment we have no means of starting background
# tasks from a Dockerfile. This workaround checks, on each bashrc eval, if the
# Snap server is running, and if not starts it.
RUN printf "\n# Auto-start Snap server.\n[[ \$(systemctl is-active snapd.socket | grep active) ]] || systemctl enable --now snapd.socket > /dev/null\n" >> ~/.bashrc

USER gitpod