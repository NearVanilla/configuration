#!/usr/bin/env bash
# NOTE: We use bash for better readability and error handling here
# but it's not hard to make it work with regular shell
set -euo pipefail

[ -z "${TRACE:-}" ] || set -x

# SETTINGS
# Path to file used to communicate from restart script
readonly restart_flag='.restart_flag'
# How long (in seconds) to wait before restarting
readonly restart_delay=10
# Whether to restart on crash or not
# The `settings.restart-on-crash` setting in spigot.yml doesn't always work
# but also sometimes server might not return proper exit code,
# so it's best to keep both options enabled
# Accepted values: y/yes/true/n/no/false
readonly restart_on_crash='yes'
# The name of your server jar
readonly server_jar="${SERVER_JAR:-server.jar}"
readonly heap_size="${MEMORY?}"
readarray -t jvm_flags <<<"${JVM_FLAGS?}"
readonly direct_exec="${DIRECT_EXEC:-false}"
# END OF SETTINGS

# The arguments that will be passed to java:
readonly java_args=(
  -Xms"${heap_size}" # Set heap min size
  -Xmx"${heap_size}" # Set heap max size
  "${jvm_flags[@]}" # Use jvm flags specified above
  -jar "${server_jar}" # Run the server
)

readonly mc_runner_args=(
  --stop-duration "${STOP_DURATION:-120s}"
)

is_true() {
  local -r arg_name="${1?}"
  case "${!arg_name,,}" in
    y|yes|true) return 0;;
    n|no|false) return 1;;
    *)
      printf 'ERROR: Invalid value for "%s" variable: %s\n' "${arg_name}" "${!arg_name}" >&2
      exit 1
      ;;
  esac
}

should_restart_on_crash() {
  is_true restart_on_crash
}

should_direct_exec() {
  is_true direct_exec
}

trap 'echo "It is a TRAP!"' SIGINT SIGTERM

# Remove restart flag, if it exists,
# so that we won't restart the server after first stop,
# unless restart script was called
rm "${restart_flag}" &>/dev/null || true

# Check if `restart_on_crash` has valid value
should_restart_on_crash || true
should_direct_exec || true

while :; do # Loop infinitely
  # Run server
  last_exit_code=0
  {
    if should_direct_exec; then
      java "${java_args[@]}"
    else
      mc-server-runner "${mc_runner_args[@]}" java "${java_args[@]}"
    fi
  } || {
    last_exit_code="${?}"
    if (( last_exit_code > 128 )); then
      printf 'Server was terminated with a signal %s (exit code: %s)\n' "$(( last_exit_code - 128 ))" "${last_exit_code}" >&2
      last_exit_code=0
    else
      # Oops, server didn't exit gracefully
      printf 'Detected server crash (exit code: %s)\n' "${last_exit_code}" >&2
      # Check if we should restart on crash or not
      if should_restart_on_crash; then
        touch "${restart_flag}"
      fi
    fi
  }
  # Check if restart file exists or exit
  if [ -e "${restart_flag}" ]; then
    # The flag exists - try to remove it
    rm "${restart_flag}" || {
      # If we can't remove it (permissions?), then exit to avoid endless restart loop
      printf 'Error removing restart flag (exit code: %s) - cowardly exiting\n' "${?}" >&2
      exit 1
    }
  else
    break # Flag doesn't exist, so break out of the loop
  fi
  printf 'Restarting server in 10 seconds, press Ctrl+C to abort.\n' >&2
  sleep "${restart_delay}" || break # Exit if sleep is interrupted (for example Ctrl+C)
done

printf 'Server stopped\n' >&2
exit "${last_exit_code}"
