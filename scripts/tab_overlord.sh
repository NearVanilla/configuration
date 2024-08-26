#!/usr/bin/env bash

set -euo pipefail

# Usage: ./scripts/tab_overlord.sh | docker compose exec -T survival rcon-cli
# json_config='
# {
#   "text": "",
#   "extra": [
#     {
#       "text": "[",
#       "color": "dark_gray",
#       "extra": [
#         {
#           "text": "A",
#           "color": "",
#           "bold": true
#         }
#       ]
#     },
#     {
#       "text": "]",
#       "color": "dark_gray"
#     },
#     {
#       "text": " %s",
#       "color": "dark_green"
#     }
#   ]
# }
# '
json_config='
{
  "text": "",
  "extra": [
    {
      "text": "[",
      "color": "dark_gray",
      "extra": [
        {
          "text": "?",
          "bold": true
        }
      ]
    },
    {
      "text": "] ",
      "color": "dark_gray",
      "extra": [
        {
          "text": "TAB Overlord",
          "obfuscated": true
        }
      ]
    },
    {
      "text": ": %s"
    }
  ]
}
'
text="$(jq -r -c . <<<"${json_config}")"

printf 'tellraw @a '"${text}"'\n' "${1}"
