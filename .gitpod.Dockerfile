FROM gitpod/workspace-full-vnc

USER root

RUN apt-get update \
    && apt-get install -y firefox \
    && apt-get clean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

RUN printf "\n# Set PYTHONPATH to the only workspace folder.\nexport PYTHONPATH=export PYTHONPATH=/`ls /workspace`/src\n" >> ~/.bashrc

USER gitpod