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
  local d
  for d in "${all_dirs[@]}"; do
    printf "Pulling in %s\n" "${d}"
    git -C "${d}" pull
  done
}

fetch() {
  local d
  for d in "${all_dirs[@]}"; do
    printf "Fetching in %s\n" "${d}"
    git -C "${d}" fetch
  done
}

set-upstream() {
  local d
  for d in "${all_dirs[@]}"; do
    local branch
    branch="$(git -C "${d}" branch --show-current)"
    git -C "${d}" branch --set-upstream-to=origin/"${branch}" "${branch}"
  done
}

checkout() {
  local prefix="${1:-}"
  local d base_branch branch
  for d in "${all_dirs[@]}"; do
    base_branch="$(get_base_branch_for_dir "${d}")"
    branch="${prefix}${base_branch}"
    printf "Checking out %s in %s\n" "${branch}" "${d}"
    git -C "${d}" checkout "${branch}"
  done
}

action="${1?action}"

shift

case "${action}" in
  pull|set-upstream|fetch|checkout) "${action}" "${@}"
    ;;
  *)
    printf 'Unknown action - %s\n' "${action}" >&2
    exit 1
    ;;
esac
