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

### docker and docker-compose

Required to actually run the server and necessary services.

Follow the guide at: <https://docs.docker.com/engine/install/ubuntu/>
Then install `docker-compose` through your package manager or pip.

### mineager

Tool by Prof_Bloodstone to check for plugin updates and download them.

```sh
pip install git+https://github.com/Prof-Bloodstone/Mineager.git
```

## Cloning the server configuration

Currently due to historical reasons, configuration is stored in different detached branches
in the same repository. To ensure proper permissions, you should clone the config manually:

```sh
for server in survival creative-spawn velocity; do
  git clone --branch config_"${server/-/_}" -- "$(git remote get-url origin)" server-config/"${server}"
done
```
