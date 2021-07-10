#!/usr/bin/env bash

set -euo pipefail

get_all_files() {
  git ls-tree -r --name-only HEAD
}

git_root() {
  git rev-parse --show-toplevel
}

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

cd "$(git_root)"

readonly whitelisted_extensions=(
  conf
  gitignore
  properties
  toml
  txt
  yaml
  yml
)

if [ "${#}" -eq 0 ]; then
  readarray -t files < <(get_all_files)
else
  files=( "${@}" )
fi
for file in "${files[@]}"; do
  # Don't modify symlinks
  [ -f "${file}" ] && ! [ -h ${file} ] || continue
  extension="${file##*.}"
  array_contains "${extension}" "${whitelisted_extensions[@]}" || {
    printf 'Skipping file since it does not have whitelisted extension: %s\n' "${file}"
    continue
  }
  pre_md5="$(md5sum "${file}")"
  # no sed -i because it doesn't work with symlinks
  #new_content="$(sed 's/\r//; s/[[:space:]]\+$//' "${file}")"
  #cat - <<<"${new_content}" >| "${file}"
  sed -i 's/\r//; s/[[:space:]]\+$//' "${file}"
  post_md5="$(md5sum "${file}")"
  if [ "${post_md5}" != "${pre_md5}" ]; then
    printf 'Fixed EOL for %s\n' "${file}"
  fi
done
