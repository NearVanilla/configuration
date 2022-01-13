#!/usr/bin/env bash

set -euo pipefail

gitroot="$(git rev-parse --show-toplevel)"
cd "${gitroot}"

for file in .env*; do
  [ "${file##*.}" = "example" ] || sed 's/=.*/=<EXAMPLE>/' "${file}" > "${file}.example"
done
