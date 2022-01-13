#!/usr/bin/env bash

set -euo pipefail
set -x

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

restart_server() {
  local -r container="${1?}"
  # TODO: Fix restarts
  rcon_cli "${container}" stop
  for i in {1..30}; do
    if check_server_running "${container}"; then
      break
    fi
    sleep "${i}"
  done
  docker-compose start "${container}"
  #docker-compose restart "${container}"
}

target_server="${1?}"

check_server_running "${target_server}"
show_restart_reason_message "${target_server}"
for (( idx=0; idx < "${#countdown_times[@]}" - 1; ++idx )); do
  to_restart="${countdown_times[$idx]}"
  show_restart_countdown "${target_server}" "${to_restart}"
  next_message_in="${countdown_times[$idx + 1]}"
  sleep "$((to_restart - next_message_in))"
done

restart_server "${target_server}"
