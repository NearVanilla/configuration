#!/usr/bin/env bash
set -euo pipefail

wget -O - https://apt.corretto.aws/corretto.key | gpg --dearmor -o - | base64 > ./corretto.key
