#!/usr/bin/env bash
# vim: sw=2

set -euo pipefail

: "${VERSION:=latest}"
PROJECT=paper
BASE_URL="https://papermc.io/api/v2/projects/${PROJECT}"

curl_json() {
  local -r url="${1?url missing}"
  local -r jq_query="${2?jq query missing}"
  curl -s "${url}" | jq -r "${jq_query}"
}

if [ "${VERSION}" == "latest" ]; then
  VERSION="$(curl_json "${BASE_URL}" '.versions|last')"
fi

VERSION_URL="${BASE_URL}/versions/${VERSION}"

BUILD="$(curl_json "${VERSION_URL}" '.builds|last')"
BUILD_URL="${VERSION_URL}/builds/${BUILD}"
BUILD_INFO="$(curl_json "${BUILD_URL}" '.')"
BUILD_TIME="$(<<<"${BUILD_INFO}" jq -r '.time')"
BUILD_CHANGES="$(<<<"${BUILD_INFO}" jq -r '.changes|.[].summary')"
JAR_NAME="$(<<<"${BUILD_INFO}" jq -r '.downloads.application.name')"
JAR_SHA="$(<<<"${BUILD_INFO}" jq -r '.downloads.application.sha256')"
JAR_URL="${BUILD_URL}/downloads/${JAR_NAME}"

printf 'Latest available build for %s is %s, released at %s\nChanges:\n%s\n' \
  "${VERSION}" "${BUILD}" "${BUILD_TIME}" "${BUILD_CHANGES}" >&2

if [ "${#}" -gt 0 ]; then 
  printf 'Will update %s servers...\n' "${#}" >&2
  sleep 3
  tmp_file="$(mktemp)"
  trap 'rm "${tmp_file}"' EXIT
  printf 'Downloading...\n' "${#}"
  wget --quiet -O "${tmp_file}" "${JAR_URL}"
  <<<"${JAR_SHA} ${tmp_file}" sha256sum --check --quiet --strict - || {
    printf 'Failed to compare checksum\n'
    exit 1
  }
  for path in "${@}"; do
    printf 'Updating %s\n' "${path}"
    cp "${tmp_file}" "${path}/server.jar"
  done
fi
