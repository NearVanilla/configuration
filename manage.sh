#!/usr/bin/env bash

set -euo pipefail



main() {
  local -r subcommand="${1:-}"
  shift
  case "${subcommand:-}" in
    '')
}

log() {
  local -r level="${1?Log level missing}"
  local -r message="${2?Log message missing}"
  printf '[%s] %s\n' "${level^^}" "${message}" >&2
}

info() {
  log
}


# TODO: if __name__ == '__main__':
main "${@}"
