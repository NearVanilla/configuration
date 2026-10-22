#!/usr/bin/env bash
# Replace the survival world with a freshly generated one.
#
# Why this exists: the per-dimension `world/dimensions/minecraft/*/paper-world.yml`
# files are tracked in git, so they must survive a world wipe untouched, and Paper
# crashes at startup when an overworld dimension directory exists without a
# `world_gen_settings.dat` (PaperMC/Paper#14066). So we:
#   1. generate a throwaway world (with the requested seed) in a scratch dir,
#   2. delete only git-ignored world data (`git clean -fdX world/`),
#   3. copy the generated world in, leaving every tracked file alone.
#
# The seed is never written to a tracked file. Pass it with --seed or NV_WORLD_SEED.
# Note: the scratch world uses Paper's default config, so the few chunks around
# spawn are generated with default feature seeds, not the ones in paper-world.yml.
#
# Usage: scripts/new_world.sh [--seed SEED] [--dry-run] [--yes] [--no-snapshot] [--heap SIZE]
set -euo pipefail

readonly scriptpath="$(realpath "${0}")"
readonly scriptdir="$(dirname "${scriptpath}")"
readonly gitroot="$(git -C "${scriptdir}" rev-parse --show-toplevel)"
readonly survival_dir="${gitroot}/server-config/survival"
readonly world_dir="${survival_dir}/world"
readonly image="server-manager"
readonly btrfs_volume="/btrfs/@nv-servers-survival"

usage() {
  cat >&2 <<'EOF'
Usage: scripts/new_world.sh [options]

  --seed SEED      World seed (any string; negative numbers: --seed=-123).
                   Defaults to $NV_WORLD_SEED, else a random seed.
  --dry-run        Generate and verify the scratch world, then stop. Deletes nothing.
  --yes            Do not ask for confirmation before wiping the world.
  --no-snapshot    Skip the btrfs snapshot taken before wiping.
  --heap SIZE      JVM heap for the scratch server (default 4G).
EOF
}

die() {
  printf 'ERROR: %s\n' "${*}" >&2
  exit 1
}

seed="${NV_WORLD_SEED-}"
dry_run=false
assume_yes=false
snapshot=true
heap=4G
while (( $# )); do
  case "${1}" in
    --seed) seed="${2?--seed needs a value}"; shift 2 ;;
    --seed=*) seed="${1#--seed=}"; shift ;;
    --dry-run) dry_run=true; shift ;;
    --yes) assume_yes=true; shift ;;
    --no-snapshot) snapshot=false; shift ;;
    --heap) heap="${2?--heap needs a value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; die "Unknown argument: ${1}" ;;
  esac
done

if [ -z "${seed}" ]; then
  seed="$(od -An -N8 -t d8 /dev/urandom | tr -d ' ')"
  echo "No seed given - using random seed ${seed}"
fi
[[ "${seed}" != *$'\n'* ]] || die "Seed must not contain newlines"

worktree_clean() {
  [ -z "$(git -C "${survival_dir}" status --porcelain --untracked-files=no)" ]
}

# --- Preflight -------------------------------------------------------------
[ -f "${survival_dir}/server.jar" ] || die "Missing ${survival_dir}/server.jar - start the server once so the jar gets downloaded"
[ -f "${survival_dir}/server.properties" ] || die "Missing ${survival_dir}/server.properties"
worktree_clean || die "survival worktree has tracked changes - fix them first (git -C ${survival_dir} status)"
if [ -n "$(cd "${gitroot}" && docker compose ps -q --status running survival)" ]; then
  die "survival is running - stop it first: docker compose stop survival"
fi
if ${snapshot} && ! ${dry_run}; then
  command -v btrfs >/dev/null || die "btrfs not found - install it or pass --no-snapshot"
  [ -e "${btrfs_volume}" ] || die "${btrfs_volume} not found - pass --no-snapshot if this host has no btrfs backup"
fi

# --- Generate the scratch world (before deleting anything) ---------------------
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

cp "${survival_dir}/server.jar" "${scratch}/server.jar"
SEED="${seed}" awk 'BEGIN { FS = OFS = "=" } /^level-seed=/ { print "level-seed=" ENVIRON["SEED"]; next } { print }' \
  "${survival_dir}/server.properties" > "${scratch}/server.properties"
grep -q '^level-seed=' "${scratch}/server.properties" || printf 'level-seed=%s\n' "${seed}" >> "${scratch}/server.properties"
echo 'eula=true' > "${scratch}/eula.txt"

echo "Generating scratch world (this takes a minute)..."
docker run --rm -i --user "$(id -u):$(id -g)" -e HEAP="${heap}" \
  -v "${scratch}:/server" -w /server --entrypoint bash "${image}" -s <<'EOF'
set -uo pipefail
mkfifo in
exec 3<>in
java -Xmx"${HEAP}" -jar server.jar --nogui <&3 >out.log 2>&1 &
pid=$!
wait_for() {
  until grep -q "${1}" out.log; do
    kill -0 "${pid}" 2>/dev/null || return 1
    sleep 1
  done
}
if ! wait_for 'Done ('; then
  echo "Scratch server exited before finishing startup:" >&2
  tail -n 50 out.log >&2
  exit 1
fi
echo seed >&3
wait_for 'Seed: \[' || true
echo stop >&3
wait "${pid}"
EOF

readonly generated="${scratch}/world"
[ -f "${generated}/level.dat" ] || die "Scratch world has no level.dat"
[ -f "${generated}/dimensions/minecraft/overworld/data/minecraft/world_gen_settings.dat" ] \
  || die "Scratch world has no overworld world_gen_settings.dat"

actual_seed="$(sed -n 's/.*Seed: \[\(-\{0,1\}[0-9]\{1,\}\)\].*/\1/p' "${scratch}/out.log" | tail -n1)"
[ -n "${actual_seed}" ] || die "Could not read the generated world's seed from the scratch server log"
if [[ "${seed}" =~ ^-?[0-9]+$ ]] && [ "${actual_seed}" != "${seed}" ]; then
  die "Seed mismatch: asked for ${seed}, scratch world has ${actual_seed}"
fi
echo "Scratch world OK - seed ${actual_seed}"

echo
echo "World data that will be deleted (git-ignored files only):"
git -C "${survival_dir}" clean -fdXn -- world/ ':(exclude)world/datapacks' | sed 's/^/  /'

if ${dry_run}; then
  echo "Dry run - nothing deleted."
  exit 0
fi

if ! ${assume_yes}; then
  read -r -p "Delete the survival world and install the new one? [y/N] " answer
  [[ "${answer}" =~ ^[Yy]$ ]] || die "Aborted"
fi

# --- Snapshot, wipe, install -----------------------------------------------------
if ${snapshot}; then
  snapshot_path="${btrfs_volume}_pre_newworld_$(date -u +%Y-%m-%d-%H%M%S)"
  sudo btrfs subvolume snapshot -r "${btrfs_volume}" "${snapshot_path}"
  echo "Snapshot: ${snapshot_path}"
fi

git -C "${survival_dir}" clean -fdX -- world/ ':(exclude)world/datapacks'
mkdir -p "${world_dir}"
[ ! -e "${world_dir}/level.dat" ] || die "world/level.dat still exists after cleaning"

tar -C "${generated}" --exclude=paper-world.yml --exclude=datapacks --exclude=session.lock -cf - . \
  | tar -C "${world_dir}" -xf -

worktree_clean || die "survival worktree is dirty after installing the world - do not start the server (git -C ${survival_dir} status)"
[ -f "${world_dir}/dimensions/minecraft/overworld/data/minecraft/world_gen_settings.dat" ] \
  || die "Installed world is missing world_gen_settings.dat"

echo "Done - new world installed with seed ${actual_seed}."
echo "Start it with: docker compose up -d survival"
