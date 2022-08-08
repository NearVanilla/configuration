#!/usr/bin/env bash
# vim: ft=sh sw=2
set -euo pipefail
set -x

docker buildx build -t scoreboard-exporter 'https://github.com/Prof-Bloodstone/Minecraft_scoreboard_exporter.git'

scriptpath="$(realpath "${0}")"
scriptdir="$(dirname "${scriptpath}")"
gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"

highscore_file="${gitroot}/website/data/highscores.json"

run_args=(
  --rm
  --mount "type=bind,src=${highscore_file},dst=/site-data/highscores.json"
  --mount "type=bind,src=${gitroot}/server-config/survival,dst=/mc-data/,readonly"
  --mount "type=bind,src=${scriptdir}/config.json,dst=/config.json,readonly"
  --entrypoint "/mc_NBT_top_scores.py"
  scoreboard-exporter
  --config /config.json
)

[ -f "${highscore_file}" ] || cat - <<<'{}' > "${highscore_file}"

docker run "${run_args[@]}" 2>&1 | tee /tmp/highscores.log
