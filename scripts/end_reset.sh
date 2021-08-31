#!/usr/bin/env bash
set -euo pipefail

: "${dir:=manual-backups/end_reset_backup_$(date +%F)}"

: "${path:=server-config/survival/world_the_end/DIM1/region/}"

: "${mcaversion:=1.16.3}"

readonly mcafile="cache/mcaselector-${mcaversion}.jar"
readonly mcarepo="Querz/mcaselector"
readonly mcaselector_release_url="https://github.com/${mcarepo}/releases/download/${mcaversion}/mcaselector-${mcaversion}.jar"


region_regex='^\.\?/\?\([^/]\+/\)*r\.\(-\?[0-9]\+\.\)\+mca$'
region_keep_regex='^\.\?/\?\([^/]\+/\)*r\(\(\.\(0\|-1\)\)\{2\}\|\.0\.2\)\.mca$'
region_coords_to_keep=(
  {0,-1}.{0,-1} # Spawn island
  0.2 # Yami wither farm
  {-1,-2}.{1,2} # mathisawesome wither farm
)
mca_query="$(<<QUERY sed 's/#.*$//' | tr -d '\n'
  !(xPos >= -31 AND xPos <= 31 AND zPos >= -31 AND zPos <= 31) # Spawn island
  AND !(xPos >= 17 AND xPos <= 25 AND zPos >= 65 AND zPos <= 74) # Yami wither farm
  AND !(xPos >= -35 AND xPos <= -20 AND zPos >= 55 AND zPos <= 65) # mathisawesome wither farm
QUERY
)"

array_contains() {
  local -r item="${1?Item required}"
  shift
  local -r arr=( "${@}" )
  for other in "${arr[@]}"; do
    if [ "${item}" == "${other}" ]; then
      return 0
    fi
  done
  return 1
}


[ -d "${path}" ] || {
  echo "Unable to find region file dir"
  exit 1
}
regions_to_keep=()
for region_coords in "${region_coords_to_keep[@]}"; do
  regions_to_keep+=( "r.${region_coords}.mca" )
done

region_files="$(find "${path}" -maxdepth 1 -mindepth 1 -type f | grep "${region_regex}" )"
regions_to_delete=()

while read -r file; do
  if ! array_contains "${file##*/}" "${regions_to_keep[@]}"; then
    regions_to_delete+=( "${file}" )
  fi
done <<< "${region_files}"

[ "${#regions_to_delete[@]}" -gt 0 ] || {
  echo "No region files found for deletion"
  exit
}

mkdir -p "${dir}"

echo "Backing up $(wc -l <<< "${region_files}") region files to ${dir}"

while read -r file; do
  cp "${file}" "${dir}"
done <<< "${region_files}"

echo "Deleting "${#regions_to_delete[@]}" region files"

rm "${regions_to_delete[@]}"

if ! [ -f "${mcafile}" ]; then
  echo "Downloading mcaselector version ${mcaversion} to ${mcafile}"
  mkdir -p "$(dirname "${mcafile}")"
  wget -O "${mcafile}" "${mcaselector_release_url}"
fi

echo "Running mcaselector to trim it a bit more"
java -jar "${mcafile}" --headless --mode delete --region "${path}" --query "${mca_query}"

show_cmd() {
  printf 'docker-compose exec -T survival rcon-cli <<<"%s"\n' "${*}"
}

echo "To cleanup dynmap, run following commands after starting the server:"

show_cmd dynmap pause all
show_cmd dynmap purgemap world_the_end flat
show_cmd dynmap pause none
show_cmd dynmap fullrender world_the_end:flat
