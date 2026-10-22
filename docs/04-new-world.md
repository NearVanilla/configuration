# Replacing the survival world

Use `scripts/new_world.sh` on the host (from the repo root). Do **not** `rm -rf world` or
`git reset --hard` the world directory:

- `world/dimensions/minecraft/*/paper-world.yml` are tracked in git. Deleting them makes the
  worktree dirty, and the container entrypoint (`manage config patch`) refuses to run.
- Restoring them recreates an empty overworld directory, which crashes Paper at startup
  (PaperMC/Paper#14066: overworld dimension dir exists but `world_gen_settings.dat` does not).

```sh
docker compose stop survival
scripts/new_world.sh --dry-run --seed=<seed>   # generates + verifies the seed, deletes nothing
scripts/new_world.sh --seed=<seed>             # snapshots, wipes, installs the new world
docker compose up -d survival
```

- The seed comes from `--seed`, else `$NV_WORLD_SEED`, else a random one. It is never written to a
  tracked file. Use `NV_WORLD_SEED` if you do not want it in your shell history.
- The script generates the world in a scratch dir first and checks the seed, so a bad seed fails
  before anything is deleted.
- Only git-ignored world data is removed (`git clean -fdX`); datapacks and tracked files are kept.
- A read-only btrfs snapshot (`@nv-servers-survival_pre_newworld_<timestamp>`) is taken first.
  `--no-snapshot` skips it on hosts without btrfs.
- The scratch world uses Paper's default config, so the few chunks around spawn are generated with
  default feature seeds rather than the ones in `paper-world.yml`.
