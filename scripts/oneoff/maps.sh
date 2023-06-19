#!/usr/bin/env bash

initial="${1?}"

to_give=9

max_n=66

for (( i=0; i<max_n; i++ )); do
  if (( i % to_give == 0 )); then
    if (( i != 0 )); then
      read -n 1 -p "Press any key to continue";
    fi
    echo "clear Prof_Bloodstone" >&3
  fi
  echo "give Prof_Bloodstone minecraft:filled_map{map:$((i+initial))}" >&3
done 3> >(docker-compose exec -T creative-spawn rcon-cli)
