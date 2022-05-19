#!/usr/bin/env bash

set -euo pipefail

award_scripts="scripts/awards/"
config="awards-config.json"

script="${award_scripts}/update.py"

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"
gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"

website_dir="${gitroot}/website"

[ -d "${website_dir}" ] || {
  echo "Script ran from wrong repo?"
  exit 1
}

cd "${website_dir}"
python3 "${website_dir}/${script}" "${website_dir}/${config}"
