# Getting Started

## Installing tools

### pre-commit

pre-commit will automatically lint files and make sure you don't commit secrets.
Follow the guide: <https://pre-commit.com/#installation>

TL;DR:

```sh
pip install pre-commit
pre-commit install
```

### docker and docker compose

Required to actually run the server and necessary services.

Follow the guide at: <https://docs.docker.com/engine/install/ubuntu/>
Then install `docker compose` through your package manager or pip.

### mineager

Tool by Prof_Bloodstone to check for plugin updates and download them.

```sh
pip install git+https://github.com/Prof-Bloodstone/Mineager.git
```

## Running the servers

### Cloning the server configuration

Currently due to historical reasons, configuration is stored in different detached branches
in the same repository. To ensure proper permissions, you should clone the config manually:

```sh
for server in survival creative velocity; do
  git clone --branch config_"${server/-/_}" -- "$(git remote get-url origin)" server-config/"${server}"
done
```

### Preparing tools

There's a lot of `.env-*.example` files with values used by the containers to run.
You need to make a copy of each and every one of them without the `.example` suffix and fill with proper values.

### Running the services

You can use `docker compose up -d --build <SERVICE>` to start a service in the background.
It'll download latest changes, prepare configs and start the server.

To tweak how the startup/stopping should be handled,
create one of the files mentioned at the top of <../docker/entrypoint.sh>.

Run `docker compose stop <SERVICE>` to stop it.
