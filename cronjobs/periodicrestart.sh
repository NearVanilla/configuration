#!/usr/bin/env bash

set -euo pipefail

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
  docker-compose exec -T "${container_name}" rcon-cli "${command[@]}"
}

check_server_running() {
  local -r container_name="${1?}"
  docker-compose ps "${container_name}" | awk 'NR == 3 { if ($3 == "Up") { exit 0 } else { exit 1 }  }' || {
    echo "Server is not running!"
    return 1
  }
}

restart_server() {
  local -r container_name="${1?}"
  docker-compose restart "${container_name}"
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
