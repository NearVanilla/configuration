#!/usr/bin/env bash
set -euo pipefail

[[ "$#" -eq 2 ]] || (echo "Usage: $0 <old player name> <new player name>" >&2; exit 1)

old_name="$1"
new_name="$2"

if [ "${DEBUG:-}" == "true" ]; then
  set -x
fi

tmp_highscores="$(mktemp --tmpdir "merge_scores.highscores.XXXXXXXX.json")"
tmp_script="$(mktemp --tmpdir "merge_scores.script.XXXXXXXX.py")"
tmp_venv="$(mktemp --tmpdir --directory "merge_scores.venv.XXXXXXXX")"
tmp_scoreboard="$(mktemp --tmpdir "merge_scores.scoreboard.XXXXXXXX.dat")"

cleanup() {
  for tmp_file in tmp_highscores tmp_script tmp_venv tmp_scoreboard; do
    rm -rf "${!tmp_file}"
  done
}

trap cleanup EXIT

send_cmd() {
  local command="$1"
  printf 'CMD: %s\n' "${1}"
  docker-compose exec -T survival rcon-cli <<<"${1}"
}


echo "Checking player names validity"
uuid_resp="$(curl -s "https://api.mojang.com/users/profiles/minecraft/${new_name}")"
[ -n "${uuid_resp}" ] || (echo "Couldn't find such player ${new_name}"; exit 1)
uuid="$(jq -er '.id' <<< "${uuid_resp}")"
previous_names="$(curl -s "https://api.mojang.com/user/profiles/${uuid}/names")"
jq -e --arg OLD_NAME "${old_name}" '[.[] | .name == $OLD_NAME] | any' >/dev/null <<< "${previous_names}" || (echo "Couldn't find name ${old_name} in ${new_name}'s history!"; exit 1)

echo "Downloading scoreboard extracting script"

wget -nv -O "${tmp_script}" 'https://raw.githubusercontent.com/Prof-Bloodstone/Minecraft_scoreboard_exporter/master/mc_NBT_top_scores.py'
python3 -m venv "${tmp_venv}"
"${tmp_venv}/bin/python" -m pip install -r <(curl -s 'https://raw.githubusercontent.com/Prof-Bloodstone/Minecraft_scoreboard_exporter/master/requirements.txt')

echo "Downloading scoreboard.dat"
cp server-config/survival/world/data/scoreboard.dat "${tmp_scoreboard}"

echo "Extracting scores"
"${tmp_venv}/bin/python" "${tmp_script}" --input "${tmp_scoreboard}" --output "${tmp_highscores}"

# Get all players in scores:
player_names="$(jq -r '.scores | .[] | .scores | .[] | .playerName' "${tmp_highscores}" | sort | uniq)"

# Assert old name exists in scores

for name in "${old_name}"; do
  grep "^${name}$" <<< "${player_names}" >/dev/null || (echo "Couldn't find ${name} in highscores!"; exit 1)
done

jq -re --arg OLD_NAME "${old_name}" '.scores | to_entries | .[] | select(.value.scores | any(.playerName == $OLD_NAME)) | {key, "value": (.value.scores | [.[] | select(.playerName == $OLD_NAME)] | first | .score)} | [.key, .value] | @tsv' "${tmp_highscores}" | \
  while IFS=$'\t' read -r score_name score_value; do
    echo "${score_name}: ${score_value}"
    if [ "${score_value:0:1}" = '-' ]; then
      operation=remove
      score_value="${score_value:1}" # Delete leading negative sign
    else
      operation=add
    fi
    cmd="scoreboard players ${operation} ${new_name} ${score_name} ${score_value}"
    until send_cmd "${cmd}"; do
      echo "Failure sending command: ${cmd}"
      sleep 5
    done
    sleep 0.5
  done

# We have succeeded moving all the commands - time to delete the old player
cmd="scoreboard players reset ${old_name}"
until send_cmd "${cmd}"; do
  echo "Failure sending command: ${cmd}"
  sleep 5
done

echo "All done!"
