#!/usr/bin/env bash
set -euo pipefail

: "${end_reset_backup_dir:="${end_reset_backup_base_dir:-/backups}/end_reset_backup_$(date +%F)"}"
: "${end_reset_dimension_dir:=world_the_end/DIM1/}"
: "${mcaversion:=2.0.2}"

_script_dir="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

readonly mcafile="cache/mcaselector-${mcaversion}.jar"
readonly mcarepo="Querz/mcaselector"
readonly mcaselector_release_url="https://github.com/${mcarepo}/releases/download/${mcaversion}/mcaselector-${mcaversion}.jar"
readonly reset_script="${_script_dir}/end_reset.py"
readonly minimal_time_between_runs="$(( 7*24*60*60 ))"

[ -d "${end_reset_dimension_dir}" ] || {
  echo "Unable to find dimension dir"
  exit 1
}

[ -x "${reset_script}" ] || {
  echo "The end reset script not found or not executable: ${reset_script}"
  exit 1
}

if ! [ -f "${mcafile}" ]; then
  echo "Downloading mcaselector version ${mcaversion} to ${mcafile}"
  mkdir -p "$(dirname "${mcafile}")"
  wget -O "${mcafile}" "${mcaselector_release_url}"
fi

# Run on first Tuesday of each odd month
# https://crontab.guru/#*_*_1-7_1/2_2
matches_cron "* * 1-7 1/2 2" || exit 0
mod_time="$(file_mod_time "restart_guard")"
current_time="$(date +%s)"
(( (current_time - mod_time) >= minimal_time_between_runs )) || exit 0
touch_file "restart_guard"


echo "Backing up dimension..."
cp -r "${end_reset_dimension_dir}" "${end_reset_backup_dir}"

echo "Running prune script..."

"${reset_script}" reset-end --dimension-dir "${end_reset_dimension_dir}" --mcaselector-jar "${mcafile}"

# TODO: Add 'schedule command' to hook utils and integrate with mc-server-runner
notification=(
  "The end has been reset."
  ""
  "To cleanup dynmap, run following commands after starting the server:"
  "/dynmap pause all"
  "/dynmap purgemap world_the_end flat"
  "/dynmap pause none"
  "/dynmap fullrender world_the_end:flat"
)

notify "${notification[@]}"
