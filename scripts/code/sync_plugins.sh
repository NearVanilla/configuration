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
  # shellcheck disable=SC2015
  id="$(docker-compose ps -qa "${container_name}")" && [ -n "${id}" ] || {
    ecode=$?
    echo "Server not existing?"
    return $ecode
  }
  status="$(docker inspect "${id}" --format '{{ .State.Status }}')" || {
    ecode=$?
    echo "Unable to get server status"
    return $ecode
  }
  case "${status:-}" in
    running)
      echo "Server is ready!"
      return 0
      ;;
    exited)
      echo "Server is exited"
      return 1
      ;;
    *)
      echo "Unknown server status (status ${status:-})!"
      return 2
      ;;
  esac
}

stop_servers() {
  local servers=( "${@}" )
  docker-compose stop "${servers[@]}"
  for i in {1..60}; do
    local idx
    for idx in "${!servers[@]}"; do
      check_server_running "${servers[$idx]}" || unset "servers[$idx]"
    done
    [ "${#servers[@]}" -gt 0 ] || return 0
    sleep 1
  done
  return 1
}

wait_for_servers() {
  local servers=( "${@}" )
  # We should NEVER reach 10 minutes, but it's here just in case...
  for i in {1..60}; do
    local idx
    for idx in "${!servers[@]}"; do
      status="$(check_server_running "${servers[$idx]}")" || {
        printf '%s' "${status}"
        return 1
      }
      # TODO: Figure out a way to only get the logs since startup
      if docker-compose logs --tail=40 "${servers[$idx]}" | grep 'Done ([^)]*)!'; then
        printf 'Server %s got ready\n' "${servers[$idx]}" >&2
        unset "servers[$idx]"
      fi
    done
    [ "${#servers[@]}" -gt 0 ] || return 0
    printf 'After %s seconds, %s servers are not ready: %s\n' "$((i*10))" "${#servers[@]}" "${servers[*]}" >&2
    sleep 10s
  done
  return 1
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
  if ! git diff --exit-code || ! git diff --exit-code --cached ; then
    git commit --all --message "${COMMIT_SUBJECT}"
    to_run+=( "${name}" )
  fi
done

[ "${#to_run[@]}" -ne 0 ] || {
  printf 'No server had changes\n' >&2
  if [ "${1:-empty}" != "force" ]; then
    exit
  fi
}

manage synchronize upload

docker-compose up --build -d "${svc_names[@]}"
for i in {3..1}; do
  printf 'Waiting %s more seconds before polling for status...\n' "$((i*10))" >&2
  sleep 10s
done

wait_for_servers "${svc_names[@]}"

sleep 10s
printf 'All servers are ready - press Y to shut them down\n' >&2

while read -r -n1 char; do
  if [ "${char,,}" = "y" ]; then
    break
  else
    printf 'Got invalid character - "%s". Try again.\n' "${char}" >&2
  fi
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
    if [ -e "${confdir}/.HARD_FAILED" ]; then
      printf 'ERROR: Failed hard in %s - leaving commits intact\n' "${name}" >&2
      ecode=1
    else
      if manage config unpatched "${confdir}"; then
        # Squash into previous commit
        git reset HEAD^
        git commit --all --amend --no-edit
      else
        printf 'ERROR: The config for %s is still patched!\n' "${name}" >&2
        ecode=1
      fi
    fi
  fi
done
exit "${ecode}"
