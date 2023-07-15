#!/usr/bin/env bash

set -euo pipefail


readonly host=NV
readonly backup_path=nearvanilla/manual-backups
readonly backup_prefix=end_reset_backup
readonly dest=server-config/survival/world_the_end/DIM1


readonly block_x="${1?Missing X block coord}"
readonly block_z="${2?Missing Z block coord}"

readonly region_x="$(( block_x >> 9 ))"
readonly region_z="$(( block_z >> 9 ))"

latest_backup="$(ssh "${host}" ls -td1 "${backup_path}/${backup_prefix}_*" | head -n1)"
region_dirs_str="$(ssh "${host}" ls -1 "${latest_backup}")"
readarray -t region_dirs <<<"${region_dirs_str}"

for dir in "${region_dirs[@]}"; do
  [ "${dir}" != "data" ] || continue
  files=()
  for (( xoff=-1; xoff<=1; ++xoff)); do
    for (( zoff=-1; zoff<=1; ++zoff)); do
      files+=( "${host}:${latest_backup}/${dir}/r.$((region_x + xoff)).$((region_z + zoff)).mca" )
    done
  done
  destination="${dest}/${dir}"
  mkdir -p "${destination}"
  scp "${files[@]}" "${destination}" || true
done
