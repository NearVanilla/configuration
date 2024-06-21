# syntax=docker/dockerfile:1
ARG DEBIAN_VERSION=bookworm-slim

FROM debian:${DEBIAN_VERSION} AS downloader

WORKDIR /tmp/packages

ARG RCON_VERSION=1.6.2
ADD https://github.com/itzg/rcon-cli/releases/download/${RCON_VERSION}/rcon-cli_${RCON_VERSION}_linux_amd64.tar.gz rcon-cli.tar.gz
RUN tar xf rcon-cli.tar.gz

ARG MC_SERVER_RUNNER_VERSION=1.9.0

ADD https://github.com/itzg/mc-server-runner/releases/download/${MC_SERVER_RUNNER_VERSION}/mc-server-runner_${MC_SERVER_RUNNER_VERSION}_linux_amd64.tar.gz mc-server-runner.tar.gz
RUN tar xf mc-server-runner.tar.gz

FROM debian:${DEBIAN_VERSION} AS base

SHELL ["/bin/bash", "-c"]

# Install all requirements first
#COPY docker/*.aptlist /tmp/
RUN --mount=type=bind,source=docker,target=/docker <<APT
  base64 -d </docker/corretto.key > /usr/share/keyrings/corretto-keyring.gpg
  cat - <<<"deb [signed-by=/usr/share/keyrings/corretto-keyring.gpg] https://apt.corretto.aws stable main" > /etc/apt/sources.list.d/corretto.list
  set -eux
  apt-get update
  apt-get upgrade -y
  for list in /docker/*.aptlist; do
    apt-get update
    xargs apt-get install -y < <(sed '/^#/d' "${list}")
  done
  rm -rf /var/lib/apt/lists/*
APT

RUN useradd --create-home --uid 1000 runner

COPY --link docker/known_hosts docker/config_repo_ro_key /home/runner/.ssh/

RUN chown -R runner:runner /home/runner/ \
    && chmod 0600 /home/runner/.ssh/*

USER runner

# Create VirtualEnv
ENV VENV_DIR=/home/runner/manager-venv
RUN python3 -m venv "${VENV_DIR}"

# Install required software in requirements.txt
COPY docker/requirements.txt /tmp/requirements.txt

RUN "${VENV_DIR}/bin/pip3" install -r /tmp/requirements.txt

COPY --from=downloader /tmp/packages/rcon-cli /usr/bin/rcon-cli
COPY --from=downloader /tmp/packages/mc-server-runner /usr/bin/mc-server-runner

WORKDIR /nearvanilla

COPY --link manage.py /nearvanilla/manage.py
COPY --link server_manager/ /nearvanilla/server_manager/

# TODO: Configure entrypoint git to use it
COPY --link scripts/githooks/ /nearvanilla/githooks/

COPY --link docker/*.sh /nearvanilla/
ENTRYPOINT ["dumb-init", "--", "/nearvanilla/entrypoint.sh"]
CMD ["/nearvanilla/start.sh"]

ENV RCON_PORT=25575
