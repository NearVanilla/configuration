#!/usr/bin/env bash

set -euo pipefail

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"

user="${1?User is required!}"

base_url=https://crafthead.net/

types=(
  avatar
  helm
  cube
)

dldir="${scriptdir}/avatars/${user}"

mkdir -p "${dldir}"

for type in "${types[@]}"; do
  curl -Ls "${base_url}/${type}/${user}" -o "${dldir}/${user,,}_${type////_}.png"
done
