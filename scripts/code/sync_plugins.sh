#!/usr/bin/env bash

set -euo pipefail

readonly COMMIT_SUBJECT="Update plugins"

git_root="$(git rev-parse --show-toplevel)"
cd "${git_root}"

[ -d "server-config" ] || {
  printf 'Unable to find server-config directory - are you too deep?\n'
  exit 1
}

manage() {
  "${git_root}/manage.py" "${@}"
}

check_server_running() {
  local -r container_name="${1?}"
  local id
  local status
  local ecode
  id="$(docker-compose ps -q "${container_name}")" || {
    ecode=$?
    echo "Server not existing?"
    return $ecode
  }
  status="$(docker inspect "${id}" --format '{{ .State.Status }}')" || {
    ecode=$?
    echo "Unable to get server status"
    return $ecode
  }
  [ "${status:-}" = "running" ] || {
    ecode=$?
    echo "Server is not running (status ${status:-})!"
    return $ecode
  }
}

stop_servers() {
  local servers=( "${@}" )
  docker-compose stop "${servers[@]}"
  local server
  for server in "${servers[@]}"; do
    for i in {1..60}; do
      check_server_running "${server}" || break
      sleep 1
    done
  done
}

confdirs=(
  "${git_root}"/server-config/*
)

svc_names=()
for confdir in "${confdirs[@]}"; do
  svc_names+=( "$(basename "${confdir}")" )
done

stop_servers "${svc_names[@]}"

to_run=()

git() {
  command git -C "${confdir}" "${@}"
}

for confdir in "${confdirs[@]}"; do
  name="$(basename "${confdir}")"
  printf 'Updating %s\n' "${name}" >&2
  manage jars update "${confdir}"
  git diff --exit-code || {
    git commit --all --message "${COMMIT_SUBJECT}"
    to_run+=( "${name}" )
  }
done

[ "${#to_run[@]}" -ne 0 ] || {
  printf 'No server had changes\n' >&2
  exit
}

manage synchronize upload

docker-compose up --build -d "${to_run[@]}"
for i in {9..1}; do
  printf 'Waiting %s more seconds...\n' "$((i*10))" >&2
  sleep 10s
done

stop_servers "${svc_names[@]}"

ecode=0

for name in "${to_run[@]}"; do
  confdir="${git_root}/server-config/${name}"
  subject="$(git log -n1 --format=%s)"
  if [ "${subject}" = "${COMMIT_SUBJECT}" ]; then
    printf 'No config changes in %s\n' "${name}" >&2
  else
    printf 'Detected new config commit in %s with subject: %s\n' "${name}" "${subject}" >&2
    if manage config unpatched "${confdir}"; then
      # Squash into previous commit
      git reset HEAD^
      git commit --all --amend --no-edit
    else
      printf 'ERROR: The config for %s is still patched!\n' "${name}" >&2
      ecode=1
    fi
  fi
done
exit "${ecode}"
