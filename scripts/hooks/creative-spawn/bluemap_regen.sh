#!/usr/bin/env bash

set -euo pipefail

readonly files=(
  "bluemap/web/index.html"
)

for file in "${files[@]}"; do
  if [ -e "${file}" ]; then
    rm --verbose "${file}"
  else
    printf 'Skipping removal of not existent %s\n' "${file}"
  fi
done
