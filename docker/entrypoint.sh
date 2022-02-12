#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_ROOT='/'
readonly MANAGE_SCRIPT="${SCRIPT_ROOT}/manage.py"
readonly START_SCRIPT="${SCRIPT_ROOT}/start.sh"
readonly GIT_HOOK_PATH="${SCRIPT_ROOT}/githooks/"

readonly GIT_REPO_ADDRESS="git@github.com:NearVanilla/configuration.git"
readonly GIT_KEY="${HOME}/.ssh/config_repo_ro_key"

# TODO: Handle it based on hostname, if not set?
readonly GIT_BRANCH="${GIT_BRANCH?:Missing git branch to use}"

readonly HARD_FAILED_FILE=".HARD_FAILED"
readonly NO_UNPATCH_FILE=".NO_UNPATCH"
readonly COMMIT_MSG_FILE=".COMMIT_MSG"
readonly NO_PULL_FILE=".NO_PULL"
readonly NO_SYNC_JARS_FILE=".NO_SYNC_JARS"

[ -z "${TRACE:-}" ] || set -x

manage() {
  "${MANAGE_SCRIPT}" "${@}"
}

patch_config() {
  manage config patch .
}

unpatch_config() {
  local extra_args=()
  local commit_msg
  if [ -e "${COMMIT_MSG_FILE}" ]; then
    commit_msg="$(cat "${COMMIT_MSG_FILE}")"
    extra_args+=( --commit-message "${commit_msg}" )
  fi
  if ! manage config unpatch "${extra_args[@]}" .; then
    local ecode="${?}"
    hard_fail
    todo implement
    return "${ecode}"
  fi
  if [ -e "${COMMIT_MSG_FILE}" ]; then
    rm "${COMMIT_MSG_FILE}"
  fi
}

git() {
  local -r git_args=(
    -c core.hookPath="${GIT_HOOK_PATH}"
    -c core.sshCommand="ssh -i ${GIT_KEY} -F /dev/null"
  )
  command git "${git_args[@]}" "${@}"
}

is_git_repo() {
  git log -n1
}

todo() {
  notify 'TODO(%s:%s): %s\n' "${FUNCNAME[1]}" "${BASH_LINENO[0]}" "${*}"
  exit 24
}

setup_git() {
  local username email
  username="$(id -u)"
  email="${username}@$(hostname)"
  git config --global user.name "${username}"
  git config --global user.email "${email}"
}

is_not_patched() {
  manage config unpatched .
}

is_patched() {
  ! is_not_patched
}

pull_config() {
  git pull --ff-only --autostash
}

download_jars() {
  manage jars download --disable-orphaned
}

server_run_loop() {
  run "${START_SCRIPT}"
}

is_hard_failed() {
  [ -e "${HARD_FAILED_FILE}" ]
}

should_skip_unpatch() {
  [ -e "${NO_UNPATCH_FILE}" ]
}

should_skip_pull() {
  [ -e "${NO_PULL_FILE}" ]
}

should_skip_jar_sync() {
  [ -e "${NO_SYNC_JARS_FILE}" ]
}

hard_fail() {
  log "Failing hard"
  touch "${HARD_FAILED_FILE}"
}

is_process_running() {
  [ -e "/proc/${1?PID missing}" ]
}

run() {
  "${@}" &
  local -r pid="${!}"
  local sig
  for sig in SIGINT SIGTERM; do
    # shellcheck disable=SC2064
    trap "log Killing && kill -${sig} ${pid}" "${sig}"
  done
  while :; do
    if wait "${pid}"; then
      log 'Returned success!'
      return
    else
      local -r ecode="${?}"
      log "Exit code ${ecode}"
      # If process is not running, return
      is_process_running "${pid}" || return "${ecode}"
    fi
  done
}

log() {
  printf '%s\n' "${@}" >&2
}

notify() {
  local -r content=( "${@}" )
  log "${content[@]}"
  if [ -n "${WEBHOOK_URL:-}" ]; then
    local -r target_url="${WEBHOOK_URL?}?wait=true"
    local webhook_content
    webhook_content="$(
      jq --null-input '$ARGS.positional | join("\n") | {content: .}' --args "${content[@]}"
    )"
    curl -s --header "Content-Type: application/json" --data "${webhook_content}" "${target_url}"
  else
    log 'Skipping webhook notification'
  fi
}

notify_err() {
  local -r ecode="${?}"
  local -r error_line="${BASH_LINENO[0]}"
  local -r error_func="${FUNCNAME[1]}"
  local -r error_source="${BASH_SOURCE[1]}"
  local errored_code
  errored_code="$(awk --assign LINE="${error_line}" 'NR==LINE' "${error_source}" | sed -e 's/^\s*//;s/\s*[;&|]\{1,2\}\s*notify_err.*//')"
  local error_message
  error_message="$(printf 'ERROR(%s:%s:%s) %s\n' "${error_func}" "${error_line}" "${errored_code}" "${*:-}")"
  notify "${error_message}"
  return "${ecode}"
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
}

prepare_git_repo() {
  if ! is_git_repo; then
    log 'Not in git repo - clonning'
    git clone "${GIT_REPO_ADDRESS}" --branch "${GIT_BRANCH}" . || notify_err "Failed to clone the repo"
  fi
}

main() {
  # If we are hard-failed, then we notified already - skip doing anything
  ! is_hard_failed || return 1
  trap 'notify_err "Uncaught error"' ERR
  setup_git
  sanity_check
  prepare_git_repo
  should_skip_pull || pull_config
  is_patched || patch_config
  should_skip_jar_sync || download_jars
  server_run_loop
  should_skip_unpatch || unpatch_config
}

main
