#!/usr/bin/env bash
# vim: ft=sh sw=2
set -euo pipefail

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"
gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"

cd "${scriptdir}"

venvdir="venv"

if ! [ -d "${venvdir}" ]; then
  python3 -m venv "${venvdir}"
  "${venvdir}/bin/pip" install -r "${scriptdir}/requirements.txt"
fi

{
  echo '##### Loading env vars #####'
  source .envrc
  echo '##### Starting notification script #####'
  "${venvdir}/bin/python" -u "notify.py" 
  echo '##### Ending notification script #####'
} 2>&1 | awk '/^[[:space:]]*$/ {print $0; next;} { "date" | getline d; printf("[%s] %s\n", d, $0); close("date")}' | tee -a cron.log
