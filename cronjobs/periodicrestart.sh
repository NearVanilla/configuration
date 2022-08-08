#!/usr/bin/env bash

set -euo pipefail
set -x

declare -x COMPOSE_DOCKER_CLI_BUILD="1"
declare -x DOCKER_BUILDKIT="1"

readonly countdown_times=(
  30
  20
  10
  5
  3
  2
  1
  0
)

readonly scriptpath="$(realpath "${0}")"
readonly scriptdir="$(dirname "${scriptpath}")"
readonly gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"
cd "${gitroot}"

show_restart_reason_message() {
  local -r server="${1?}"
  rcon_cli "${server}" tellraw @a '["",{"text":"Due to a ","color":"blue"},{"text":"bug","color":"dark_red"},{"text":" in the server, we need to ","color":"blue"},{"text":"restart periodically","color":"dark_red"},{"text":".","color":"blue"}]'
}

show_restart_countdown() {
  local -r server="${1?}"
  local -r time="${2?}"
  rcon_cli "${server}" tellraw @a '["",{"text":"Restarting in ","color":"blue"},{"text":"'"${time}"'","color":"dark_red"},{"text":" seconds.","color":"blue"}]'
}

rcon_cli() {
  local -r container_name="${1?}"
  shift
  local -r command=( "${@}" )
  docker-compose exec -T "${container_name}" rcon-cli --port 25575 "${command[@]}"
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

target_servers=( "${@}" )
if [  "${#target_servers[@]}" -eq 0 ]; then
  for confdir in "${gitroot}"/server-config/*; do
    server="$(basename "${confdir}")"
    target_servers+=( "${server}" )
  done
fi

for (( idx=0; idx < "${#countdown_times[@]}" - 1; ++idx )); do
  to_restart="${countdown_times[$idx]}"
  for target_server in "${target_servers[@]}"; do
    [ "${target_server}" != "velocity" ] || continue
    [ "${idx}" -ne 0 ] || show_restart_reason_message "${target_server}"
    show_restart_countdown "${target_server}" "${to_restart}"
  done
  next_message_in="${countdown_times[$idx + 1]}"
  sleep "$((to_restart - next_message_in))"
done


for target_server in "${target_servers[@]}"; do
  [ "${target_server}" = "velocity" ] || rcon_cli "${target_server}" "kick @a Periodic server restart, sorry :/"
done

docker-compose stop "${target_servers[@]}"
git pull --ff-only --autostash
docker-compose up -d --build "${target_servers[@]}" "website"
