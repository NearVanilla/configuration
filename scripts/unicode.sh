#!/usr/bin/env bash

set -euo pipefail

escape='\u00A7'

c=0
while IFS='' read -r -n1 char ; do
  if [ "$char" == "&" ]; then
    c=7
  elif (( c-- <= 0 )); then
    printf '%s' "${char}"
  else 
    printf '%s%s' "${escape}" "${char}"
  fi
done
