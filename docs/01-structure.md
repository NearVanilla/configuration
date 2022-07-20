# Structure

`manage.py` and `server_manager/` - code used to manage the servers.
Responsible for updating plugins and downloading them on startup, templating config etc.

`Dockerfile` and `docker/` - used to create custom image to run the servers in.

`docker-compose.yml` - definition of the servers.

`server-config/` - place where server files are stored.

`scripts/` - manual-use scripts - either to perform some tasks on the server or manage code.

`bats_tests/` - tests for shell scripts.

`cronjobs/` - scripts meant to be automatically triggered periodically.

`plugins/` - place for jar files from which the updates are being taken for updating the config and upload.

`docs/` - document some of the things that you should know to use this repo.
