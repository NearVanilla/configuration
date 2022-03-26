#!/usr/bin/env bash
# Workaround https://github.com/Hexaoxide/Carbon/issues/198
set -euo pipefail

readonly scriptpath="$(realpath "${0}")"
readonly scriptdir="$(dirname "${scriptpath}")"
readonly gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"
cd "${gitroot}"

readonly server_dir="${gitroot}/server-config/survival"

readonly usercache_file="${server_dir}/usercache.json"
readonly users_dir="${server_dir}/plugins/CarbonChat/users"

get_usercache_username() {
  local -r uuid="${1?}"
  local jq_args=(
    --raw-output # Print raw string instead of quoted JSON string
    --exit-status # If no match found, exit with error
    --arg uuid "${uuid}" # Assing UUID to $uuid
    'map(select(.uuid == $uuid)) | first | .name' # Select first entry with matching uuid
  )
  jq "${jq_args[@]}" "${usercache_file}"
}

get_carbon_username() {
  local -r file="${1?}"
  jq --raw-output '.username' "${file}"
}

set_carbon_username() {
  local -r file="${1?}"
  local -r username="${2?}"
  local -r tmp_file="${file}.tmp"
  jq --arg username "${username}" '. + {username: $username}' "${file}" >| "${tmp_file}"
  mv "${tmp_file}" "${file}"
}

changed=()

for user_file in "${users_dir}"/*.json; do
  file_name="$(basename "${user_file}")"
  uuid="${file_name%.json}"
  username="$(get_usercache_username "${uuid}")"
  carbon_username=$(get_carbon_username "${user_file}")
  if [ "${username}" != "${carbon_username}" ]; then
    change="${carbon_username}->${username}"
    changed+=( "${change}" )
    echo "Changing names: ${change}"
    set_carbon_username "${user_file}" "${username}"
  fi
done

no_changes="${#changed[@]}"
if [ "${no_changes}" -gt 0 ]; then
  echo "Changed ${no_changes} usernames, you should restart the server :)"
fi
