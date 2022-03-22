#!/usr/bin/env bash

set -euo pipefail

original_args=( "${@}" )

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


translate_arg() {
  local -r arg="${1?}"
  case "${arg}" in
    s|sur|surv) printf 'survival';;
    c|creat) printf 'creative-spawn';;
    v|vel) printf 'velocity';;
    *) printf '%s' "${arg}";;
  esac
}

new_args=()
for arg in "${original_args[@]}"; do
  new_args+=( "$(translate_arg "${arg}")" )
done

docker-compose "${new_args[@]}"
