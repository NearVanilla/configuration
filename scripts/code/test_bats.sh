#!/usr/bin/env bash
set -euo pipefail

readonly bats_bin="bats_tests/bats/bin/bats"

[ -e "${bats_bin}" ] || {
  printf 'Missing bats script under "%s". Did you forget to initialize submodules?\n' "${bats_bin}"
  exit 1
}

# Resolve directories resursively looking for tests
readarray -t args < <({
  for arg in "${@}"; do
    if [ -d "${arg}" ]; then
      while read -r file; do
        if [ -d "${file}" ]; then
          # Ignore submodules
          :
        elif [ -e "${file}" ] && [ "${file##*.}" = "bats" ]; then
          printf '%s\n' "${file}"
        fi
        # Ignore deleted
      done < <(git ls-files --cached --others --exclude-standard "${arg}")
    else
      printf '%s\n' "${arg}"
    fi
  done
} | tee >(cat - >&2) | sort -u)

"${bats_bin}" "${args[@]}"
