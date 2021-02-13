FROM gitpod/workspace-mysql

USER root

RUN apt-get update \
    && apt-get install -y lynx \
    && apt-get clean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

RUN printf "\n# Set PYTHONPATH to the only workspace folder.\nexport PYTHONPATH=\$GITPOD_REPO_ROOT/src\n" >> ~/.bashrc

USER gitpod