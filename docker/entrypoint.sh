#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_ROOT='/'
readonly MANAGE_SCRIPT="${SCRIPT_ROOT}/manage.py"
readonly START_SCRIPT="${SCRIPT_ROOT}/start.sh"
readonly GIT_HOOK_PATH="${SCRIPT_ROOT}/githooks/"


manage() {
  "${MANAGE_SCRIPT}" "${@}"
}

patch_config() {
  manage config patch "${SERVER_LOCATION}"
}

unpatch_config() {
  manage config unpatch "${SERVER_LOCATION}"
}

git() {
  local -r git_args=(
    -c core.hookPath="${GIT_HOOK_PATH}"
  )
  command git "${git_args[@]}" "${@}"
}

is_git_repo() {
  git log -n1
}

is_patched() {
  manage config
}




sanity_check() {
  local script_path
  for script_path in "${MANAGE_SCRIPT}" "${START_SCRIPT}"; do
    if ! [ -f "${script_path}" ]; then
      printf 'Expected to find %s script\n' "${script_path}" >&2
      return 1
    fi
    if ! [ -x "${script_path}" ]; then
      printf 'Expected to find %s to be executable\n' "${script_path}" >&2
      return 1
    fi
  done

  # TODO: Do we always?
  if ! is_git_repo; then
    printf 'Expected the server root to be in git repo\n' >&2
    return 1
  fi
}
