#!/usr/bin/env bash

set -euo pipefail

mysql() {
  command mysql -uroot -p"${MARIADB_ROOT_PASSWORD?Root pass missing}"
}

# Create luckperms db

printf 'Initializing LuckPerms database\n' >&2
mysql <<LUCKPERMS
CREATE DATABASE IF NOT EXISTS luckperms COMMENT 'LuckPerms';
CREATE USER IF NOT EXISTS 'luckperms'@'%' IDENTIFIED BY '${MARIADB_LUCKPERMS_PASSWORD?Luckperms pass missing}';
GRANT ALL PRIVILEGES ON luckperms.* TO 'luckperms'@'%';
LUCKPERMS


printf 'Initializing Prism database\n' >&2
mysql <<PRISM
CREATE DATABASE IF NOT EXISTS prism COMMENT 'Prism';
CREATE USER IF NOT EXISTS 'prism'@'%' IDENTIFIED BY '${MARIADB_PRISM_PASSWORD?Prism pass missing}';
GRANT ALL PRIVILEGES ON prism.* TO 'prism'@'%';
PRISM


# Flush privileges
mysql <<FLUSH
FLUSH PRIVILEGES;
FLUSH

printf 'DB INITIALIZED\n' >&2
