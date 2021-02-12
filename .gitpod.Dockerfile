FROM gitpod/workspace-full-mysql

USER root
RUN printf "\n# Set PYTHONPATH to the only workspace folder.\nexport PYTHONPATH=\$GITPOD_REPO_ROOT/src\n" >> ~/.bashrc

USER gitpod