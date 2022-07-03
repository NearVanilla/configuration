#!/usr/bin/env bash

_script_dir="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

run_hook() {
  local -r hook="${1?}"
  local hook_name
  hook_name="$(basename "${hook%%.sh}")"
  (
    export HOOK_NAME="${hook_name}"

    source "${_script_dir}/hook_utils.sh"
    "${hook}"
  )
}


run_hooks() {
  local -r hooks=( "${@}" )
  if [ "${#hooks[@]}" -eq 0 ]; then
    printf 'No hooks specified\n!' >&2
    return 1
  fi
  local file
  for file in "${hooks[@]}"; do
    if [ -x "${file}" ]; then
      : # Pass - we will run it down below
    elif [ -e "${file}" ]; then
      printf 'Hook "%s" is not executable!\n' "${file}" >&2
      return 1
    else
      printf 'Hook "%s" does not exist!\n' "${file}" >&2
      return 1
    fi
  done

  for file in "${hooks[@]}"; do
    run_hook "${file}" || return $?
  done
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  set -euo pipefail
  run_hooks "$@"
fi
