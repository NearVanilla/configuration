#!/usr/bin/env bash

set -euo pipefail

# Constants:
readonly color_reset="$(tput sgr0)"
readonly color_red="$(tput setaf 1)"
readonly color_green="$(tput setaf 2)"
readonly color_cyan="$(tput setaf 6)"
readonly substituted_commit_placeholder="[SUBST]"
readonly changes_commit_placeholder="[CHNG]"

print_usage() {
  printf 'Usage: %s (help|subst|patch|unsubst|unpatch)\n'
  printf 'Commands:\n'
  printf '\tsubst, patch - apply secret substitutions\n'
  printf '\tunsubst, unpatch <commit_message> - apply changes, reverting substitutions\n'

}

info() {
  printf '%sINFO%s: %s\n' "${color_green}" "${color_reset}" "${*}" >&2
}

error() {
  printf '%sERROR%s: %s\n' "${color_red}" "${color_reset}" "${*}" >&2
}

debug() {
  if is_debug; then
    printf '%sDEBUG%s: %s\n' "${color_cyan}" "${color_reset}" "${*}" >&2
  fi
}

is_debug() {
  local -r debug="${DEBUG:-false}"
  [ "${debug,,}" == 'true' ]
}

require_exact_args() {
  local -r required_amount="${1?Missing required args count}"
  local -r received_amount="${2?Missing received args count}"
  if [ "${received_amount}" -ne "${required_amount}" ]; then
    error "Function ${FUNCNAME[1]} requires ${required_amount} arguments, but ${received_amount} were given!"
    return 1
  fi
}

assert_vars_set() {
  local -r vars_to_check=( "${@}" )
  for var in "${vars_to_check[@]}"; do
    if [ -z "${!var+x}" ]; then
      error "Required variable ${var@Q} is not set!"
      return 1
    fi
  done
}

sponge() {
  require_exact_args 1 "${#}"
  local -r file="${1}"
  local content
  content="$(cat -)"
  printf '%s' "${content}" > "${file}"
}

all_config_tracked_files() {
  git ls-tree -r HEAD --name-only -- ./config \
    | grep -v '\.\(sh\)$' \
    | grep -v '^docker-compose.yml$'
}

is_in_git_work_tree() {
  git rev-parse --is-inside-work-tree &>/dev/null
}

is_worktree_clean() {
  git diff --exit-code --quiet
}

get_commit_subject() {
  git log -n1 --format=%s "${@}"
}

get_commit_sha() {
  git log -n1 --format=%H "${@}"
}

assert_is_in_git_work_tree() {
  is_in_git_work_tree || {
    local -r rcode="${?}"
    error "Not inside git repository - aborting!"
    return "${rcode}"
  }
}

substitute_placeholders() {
  local -r files_to_replace_placeholders_in=( "${@}" )
  for file in "${files_to_replace_placeholders_in[@]}"; do
    local file_placeholders
    readarray -t file_placeholders < <( envsubst --variables -- "$(cat "${file}")" )
    if [ "${#file_placeholders[@]}" -gt 0 ]; then
      debug "Placeholders discovered in ${file}: ${file_placeholders[*]@Q}"
      assert_vars_set "${file_placeholders[@]}"
      <"${file}" envsubst | sponge "${file}"
    else
      debug "No placeholders found in ${file}"
    fi
  done
}

substitute_tracked_placeholders() {
  assert_is_in_git_work_tree || return "${?}"
  local all_config_tracked_files
  all_config_tracked_files="$(all_config_tracked_files)" || {
    local -r rcode="${?}"
    error 'Unable to get all tracked files'
    return "${rcode}"
  }
  local all_config_tracked_files_array
  readarray -t all_config_tracked_files_array <<<"${all_config_tracked_files}"
  substitute_placeholders "${all_config_tracked_files_array[@]}"
}

substitute_tracked_and_commit() {
  assert_is_in_git_work_tree || return "${?}"
  is_worktree_clean || {
    local -r rcode="${?}"
    error "The workspace is modified - aborting!"
    return "${rcode}"
  }
  substitute_tracked_placeholders
  git commit --all --message "${substituted_commit_placeholder} $(date --iso-8601=s)"
}

commit_and_unsubstitute() {
  require_exact_args 1 "${#}"
  assert_is_in_git_work_tree || return "${?}"
  if get_commit_subject HEAD | grep --quiet --fixed-strings "${substituted_commit_placeholder}"; then
    if is_worktree_clean; then
      info "No new changes detected - reverting last commit."
      git reset --hard HEAD^
    else
      info "Changes detected - commiting"
      local scp_commit_sha
      scp_commit_sha="$(get_commit_sha HEAD)"
      git commit --all --message "${changes_commit_placeholder} $(date --iso-8601=s)"
      git revert --no-edit "${scp_commit_sha}" || {
        local -r rcode="${?}"
        error "Error reverting the commit - probably some conflict!"
        return "${rcode}"
      }
      git reset --soft "${scp_commit_sha}^"
      git commit --message "${1?}"
    fi
  else
    error "Previous commit doesn't have placeholder in subject - aborting!"
    return 1
  fi
}

main() {
  local -r trace="${TRACE:-false}"
  [ "${trace,,}" == 'true' ] && set -x
  if (( $# == 0 )); then
    error 'No arguments given'
    print_usage
    return 1
  fi
  readonly command="${1:-}"
  shift
  case "${command:-}" in
    subst|patch|s|p) substitute_tracked_and_commit;;
    unsubst|unpatch|us|up) commit_and_unsubstitute "${@}";;
    help) print_usage;;
    *)
      error "Invalid command: ${command@Q}"
      print_usage
      return 1
      ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
