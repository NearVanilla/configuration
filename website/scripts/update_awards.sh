#!/usr/bin/env bash

set -euo pipefail

award_scripts="scripts/awards/"
config="awards-config.json"

script="${award_scripts}/update.py"

toplevel="$(git rev-parse --show-toplevel)"

website_dir="${toplevel}/website"

[ -d "${website_dir}" ] || {
  echo "Script ran from wrong repo?"
  exit 1
}

python3 "${website_dir}/${script}" "${website_dir}/${config}"
