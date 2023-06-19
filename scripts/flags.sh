#!/usr/bin/env bash

set -euo pipefail
readonly config_dir=server-config
readonly entrypoint_script=docker/entrypoint.sh

git_root() {
  local -r dir="${1:-.}"
  git -C "${dir}" rev-parse --show-toplevel
}

current_git_root="."
# search parent dirs while they are in git repo
while new_git_root="$(git_root "${current_git_root}/.." 2>/dev/null)"; do
  current_git_root="${new_git_root}"
done

cd "${current_git_root}"

GIT_BRANCH=unused source "${entrypoint_script}"

readonly entry_files=(
  HARD_FAILED_FILE
  NO_UNPATCH_FILE
  COMMIT_MSG_FILE
  NO_PULL_FILE
  NO_SYNC_JARS_FILE
)

servers=()
for d in "${config_dir}"/*; do
  name="${d##*/}"
  servers+=( "${name}" )
done

case "${1:-}" in
  ""|ls)
    for server in "${servers[@]}"; do
      printf '### %s ###\n' "${server}"
      for file in "${entry_files[@]}"; do
        if [ -e "${config_dir}/${server}/${!file}" ]; then
          printf '%s\n' "${file%%_FILE}"
        fi
      done
    done
    ;;
  s|set)
    shift
    for server in "${servers[@]}"; do
      for file in "${@}"; do
        touch "${config_dir}/${server}/${file}"
      done
    done
    ;;
  r|rm|u|unset)
    shift
    for server in "${servers[@]}"; do
      for file in "${@}"; do
        p="${config_dir}/${server}/${file}"
        [ ! -e "${p}" ] || rm "${p}"
      done
    done
    ;;
  *)
    printf 'Unknown cmd - "%s"\n' "${1:-}"
    exit 1
    ;;
esac
