#!/usr/bin/env bash

set -euo pipefail

set -x

git_root="$(git rev-parse --show-toplevel)"
cd "${git_root}"

is_subst() {
  local -r ref="${1:-HEAD}"
  git log -n1 --format=%s "${ref}" | grep --fixed-strings '[SUBST]' >/dev/null
}

current_branch() {
  git rev-parse --abbrev-ref HEAD
}

get_sha() {
  local -r ref="${1:-HEAD}"
  git log -n1 --format=%H "${ref}"
}

for repo in . ./server-config/*/; do
  cd "${git_root}/${repo}"
  ref=HEAD
  ! is_subst "${ref}" || ref='HEAD^'
  ! is_subst "${ref}" || {
    printf "Two commits substituted in %s?\n" "${repo}"
    exit 1
  }
  branch="$(current_branch)"
  [ "${branch}" != "HEAD" ] || {
    printf 'Unable to check the branch in %s\n' "${repo}"
    exit 1
  }
  local_sha="$(get_sha "${ref}")"
  # If remote doesn't exist- ignore it :)
  remote_sha="$(get_sha "origin/${branch}" || true)"
  [ "${local_sha}" = "${remote_sha}" ] || git push origin "${ref}":"${branch}"
done
