#!/usr/bin/env bash
# vim: ft=sh sw=2
set -euo pipefail
set -x

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"
gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"

cd "${scriptdir}"

venvdir="${scriptdir}/venv"

if ! [ -d "${venvdir}" ]; then
  python3 -m venv "${venvdir}"
  "${venvdir}/bin/pip" install -r "${scriptdir}/requirements.txt"
fi

"${venvdir}/bin/python" "${scriptdir}/PRAP.py" --config "${scriptdir}/config.ini"
