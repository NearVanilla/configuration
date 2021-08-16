#!/usr/bin/env bash

set -euo pipefail

objective="${1}"

secret_file='.secret'
current_secret_val="$(cat "${secret_file}")"

new_secret_val="$((current_secret_val + 1))"

objective_description="$(<<<"${objective}" sed -e 's/minecraft\.//g' -e 's/[.:_]/ /g' -e 's/.*/\L&/; s/[a-z]*/\u&/g' )"

cat <<EOF
scoreboard objectives add secret_${new_secret_val} ${objective} "Secret objective #${new_secret_val} - ${objective_description}"
scoreboard objectives setdisplay list secret_${new_secret_val}
EOF

if [[ -t 1 ]]; then
  printf 'Stdout is a tty - skipping update of %s number\n' "${secret_file}" >&2
  printf 'To update, run: ./scripts/update_secret.sh | docker-compose exec -T survival rcon-cli\n' >&2
else
  printf 'Stdout is NOT a tty - updating %s number\n' "${secret_file}" >&2
  printf '%d' "${new_secret_val}" >| "${secret_file}"
fi
