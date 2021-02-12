FROM gitpod/workspace-full-vnc

USER root

RUN apt-get update \
    && apt-get install -y firefox \
    && apt-get clean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

RUN printf "\n# Set PYTHONPATH to the only workspace folder.\nexport PYTHONPATH=/workspace/whimsical-recipes/src\n" >> ~/.bashrc
RUN printf "echo $GITPOD_REPO_HOME >~/.env.dump\n" >> ~/.bashrc

USER gitpod