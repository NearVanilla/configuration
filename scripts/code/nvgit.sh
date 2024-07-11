#!/usr/bin/env bash
set -euo pipefail

readonly scriptpath="$(realpath "${0}")"
readonly scriptdir="$(dirname "${scriptpath}")"
readonly gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"
cd "${gitroot}"

all_dirs=(
  .
  server-config/*
)

get_base_branch_for_dir() {
  local dir="${1?Directory}"
  case "${dir}" in
    .) printf master;;
    server-config/*)
      local base
      base="$(basename "${dir}")"
      printf "${base//-/_}"
      ;;
    *)
      printf 'Unknown dir: %s\n' "${dir}" >&2
      return 1
      ;;
  esac
}

pull() {
  for d in "${all_dirs[@]}"; do
    printf "Pulling in %s\n" "${d}"
    git -C "${d}" pull
  done
}

set-upstream() {
  for d in "${all_dirs[@]}"; do
    local branch
    branch="$(git -C "${d}" branch --show-current)"
    git -C "${d}" branch --set-upstream-to=origin/"${branch}" "${branch}"
  done
}

action="${1?action}"

shift

case "${action}" in
  pull|set-upstream) "${action}"
    ;;
  *)
    printf 'Unknown action - %s\n' "${action}" >&2
    exit 1
    ;;
esac
