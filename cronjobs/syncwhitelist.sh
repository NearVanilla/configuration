#!/usr/bin/env bash

set -euo pipefail

toplevel="$(git rev-parse --show-toplevel)"
cd "${toplevel}"

cp -v server-config/survival/{whitelist.json,ban*.json} server-config/creative/

docker compose exec -T creative rcon-cli whitelist reload
