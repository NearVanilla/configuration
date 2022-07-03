# vim: ft=bash

git_toplevel="$(git rev-parse --show-toplevel)" || exit $?
git_toplevel="$(realpath "${git_toplevel}")"
declare -rx git_toplevel="${git_toplevel}"
git_dir="$(git rev-parse --git-dir)"
git_dir="$(realpath "${git_dir}")"
declare -rx git_dir="${git_dir}"

declare -rx hook_persistent_storage_directory="${git_dir}/nearvanilla/hooks"

matches_single_cron() {
  local -r cron_spec="${1?}"
  local current_value="${2?}"
  if [ "${cron_spec}" = '*' ]; then
    return 0
  fi

  # Trim leading 0s from current_value
  local -r current_value="$(( "10#${current_value}" ))"

  local value values
  IFS=',' read -r -a values <<<"${cron_spec}"
  for value in "${values[@]}"; do
    if [ -z "${value##*-*}" ]; then
      local start="${value%%-*}"
      local end="${value##*-}"
      if ((current_value >= start && current_value <= end)); then
        return 0
      fi
    elif [ -z "${value##*/*}" ]; then
      local start="${value%%/*}"
      local step="${value##*/}"
      if [ "${start}" = '*' ]; then
        start=0
      fi
      local substracted
      if (( (substracted=current_value-start) >= 0 && substracted%step == 0 )); then
        return 0
      fi
    else
      # Trim leading 0s from value
      value="$(( "10#${value}" ))"
      if [ "${value}" -eq "${current_value}" ]; then
        return 0
      fi
    fi
  done
  return 1
}

matches_cron() {
  # Check whether given cron specification is satisfied by given timestamp, current time by default
  local -r cron="${1?}"
  local ts="${2:-}"
  if [ -z "${ts:-}" ]; then
    ts="$(date +%s)"
  fi
  local -r ts="${ts}"

  local cron_array
  read -r -a cron_array <<<"${cron}"

  local date_cronified="$(date --date="@${ts}" +'%M %H %d %m %w')"
  local date_array
  read -r -a date_array <<<"${date_cronified}"

  if [ "${#cron_array[@]}" -ne "${#date_array[@]}" ]; then
    printf 'Expected cron spec to split into %s parts, but got %s instead: %s\n' "${#date_array[@]}" "${#cron_array[@]}" "${cron_array[@]@Q}" >&2
    return 2
  fi
  local index
  for index in "${!cron_array[@]}"; do
    matches_single_cron "${cron_array[$index]}" "${date_array[$index]}" || return $?
  done
}

optional_stdin() {
  if [ -p /dev/stdin ]; then
    cat -
  fi
}

get_file_path() {
  printf '%s/%s/%s' "${hook_persistent_storage_directory?}" "${HOOK_NAME?}" "${1?}"
}

read_file() {
  local path
  path="$(get_file_path "${1:-}")"
  [ ! -e "${path}" ] || cat "${path}"
}

write_file() {
  local path
  path="$(get_file_path "${1:-}")"
  touch_file "${1:-}"
  optional_stdin >| "${path}"
}

touch_file() {
  local path
  path="$(get_file_path "${1:-}")"
  local dir
  dir="$(dirname "${path}")"
  mkdir -p "${dir}"
  touch "${path}"
}

file_mod_time() {
  local path
  path="$(get_file_path "${1:-}")"
  local format="${2:-%s}"
  if [ -e "${path}" ]; then
    date --reference "${path}" "+${format}"
  else
    date --date=@0 "+${format}"
  fi
}

function _export_all_functions {
  local current_file="${BASH_SOURCE[0]}"
  local function_list
  function_list="$(sed -n 's/^\([[:alpha:]_]\+\)() .*/\1/p' "$current_file")"
  local function_name
  while read -r function_name; do
    export -f "${function_name}"
  done <<<"${function_list}"
}
_export_all_functions
unset _export_all_functions
