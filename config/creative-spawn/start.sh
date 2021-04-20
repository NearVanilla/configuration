#!/usr/bin/env bash

MEM='3G'

#wget 'https://papermc.io/api/v1/paper/1.15.2/latest/download' -O paperclip.jar

java -Xms"${MEM}" -Xmx"${MEM}" -jar server.jar nogui
