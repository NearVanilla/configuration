#!/usr/bin/env bash

set -euo pipefail

# Base config
ref="${1:-refs/heads/master}"

repo="pdinklag/MinecraftStats"
#repo="Prof-Bloodstone/MinecraftStats"

url="https://github.com/${repo}/archive/${ref}.zip"

webdir="files/public/awards"
award_scripts="scripts/awards/"

web_files=(
  font/
  img/
  js/
  localization/
  index.html
  style.css
  style.min.css
)

delete_web_files=(
  js/dev/
  js/minimize.sh
)

python_files=(
  mcstats/
  javaproperties.py
  makeconfig.py
  mojang.py
  update.py
)

delete_python_files=()

ignored_files=(
  .gitignore
  LICENSE.txt
  README.md
)



# Helper function
array_contains() {
  local -r item="${1?Item required}"
  shift
  local -r arr=( "${@}" )
  local other
  for other in "${arr[@]}"; do
    if [ "${item}" == "${other}" ]; then
      return 0
    fi
  done
  return 1
}

delete_relative_files() {
  local -r basedir="${1?}"
  shift
  local -r relative_files=( "${@}" )
  local file
  for file in "${relative_files[@]}"; do
    local full_file="${basedir}/${file}"
    [ -e "${full_file}" ] || {
      echo "File ${full_file} does not exist!"
      return 1
    }
    echo "Deleting ${full_file}..."
    rm --recursive "${full_file}"
  done
}

# Lets start
toplevel="$(git rev-parse --show-toplevel)"
website_dir="${toplevel}/website"

[ -d "${website_dir}" ] || {
  echo "Script ran from wrong repo?"
  exit 1
}

tempdir="$(mktemp --directory)"
trap 'rm -r ${tempdir}' EXIT

zip_file="${tempdir}/stats.zip"
unpacked_dir="${tempdir}/unpacked/"

curl --fail --location "${url}" --output "${zip_file}"
unzip "${zip_file}" -d "${unpacked_dir}"

# Delete old files
for directory in "${webdir}" "${award_scripts}"; do
  if [ -d "${directory}" ]; then
    echo "Removing old ${directory}..."
    rm --recursive "${directory}"
  fi
  mkdir "${directory}"
done

# Move files to proper dirs
for file in "${unpacked_dir}"/*/*; do # Double /*/*, cause first matches top level archive dir like MinecraftStats-master/
  filebase="$(basename "${file}")"
  if [ -d "${file}" ]; then
    # Add trailing slashes to directories
    file="${file}/"
    filebase="${filebase}/"
  fi
  if array_contains "${filebase}" "${web_files[@]}"; then
    cp --recursive "${file}" "${webdir}"
  elif array_contains "${filebase}" "${python_files[@]}"; then
    cp --recursive "${file}" "${award_scripts}"
  elif array_contains "${filebase}" "${ignored_files[@]}"; then
    : # Ignored
  else
    echo "I have no idea what to do with ${filebase}. Aborting."
    exit 1
  fi
done

echo "Removing unneeded files..."
delete_relative_files "${webdir}" "${delete_web_files[@]}" || exit $?
delete_relative_files "${award_scripts}" "${delete_python_files[@]}" || exit $?
