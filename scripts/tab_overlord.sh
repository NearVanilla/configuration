#!/usr/bin/env bash

set -euo pipefail

# Usage: ./scripts/tab_overlord.sh | docker-compose exec -T survival rcon-cli

printf 'tellraw @a ["",{"text":"[TAB Overlord]","bold":true,"color":"red"},{"text":" %s"}]\n' "${1}"
