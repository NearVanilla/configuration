# NearVanilla server configuration

This repo contains most of the configuration and most of the automation for NV Server.

For more information on working with it, checkout files in <docs/>.

## Website

`website/files` is a Git submodule of [NearVanilla/SvelteSite](https://github.com/NearVanilla/SvelteSite),
pinned to a commit by this repository. After pulling configuration updates, synchronize
the submodule URL and check out the pinned source:

```sh
git submodule sync -- website/files
git submodule update --init --recursive website/files
```

The website image installs dependencies from `bun.lock`, builds the static SvelteKit
site into `build/`, and serves it with the existing Caddy configuration:

```sh
docker compose build website
docker compose up -d --no-deps website
```
