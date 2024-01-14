#!/usr/bin/env bash
# vim: ft=sh sw=2
set -euo pipefail
set -x

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"
gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"

scoreboard_file="${gitroot}/server-config/survival/world/data/scoreboard.dat"
venvdir="${scriptdir}/venv"
requirements="${scriptdir}/TabOverlordStats/requirements.txt"

if ! [ -d "${venvdir}" ]; then
  python3 -m venv "${venvdir}"
  "${venvdir}/bin/pip" install -r "${requirements}"
fi

# For docker compose to work properly
cd "${scriptdir}"

"${venvdir}/bin/python3" "${scriptdir}/TabOverlordStats/scoreboard.py" "${scoreboard_file}"
