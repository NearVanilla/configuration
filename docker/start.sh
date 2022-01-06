#!/usr/bin/env bash
# NOTE: We use bash for better readability and error handling here
# but it's not hard to make it work with regular shell
set -euo pipefail


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
# END OF SETTINGS

should_restart_on_crash() {
  case "${restart_on_crash,,}" in
    y|yes|true) return 0;;
    n|no|false) return 1;;
    *)
      printf 'ERROR: Invalid value for "restart_on_crash" variable: %s\n' "${restart_on_crash}" >&2
      exit 1
      ;;
  esac
}

# The arguments that will be passed to java:
readonly java_args=(
  -Xms"${heap_size}" # Set heap min size
  -Xmx"${heap_size}" # Set heap max size
  "${jvm_flags[@]}" # Use jvm flags specified above
  -jar "${server_jar}" # Run the server
)

# Remove restart flag, if it exists,
# so that we won't restart the server after first stop,
# unless restart script was called
rm "${restart_flag}" &>/dev/null || true

# Check if `restart_on_crash` has valid value
should_restart_on_crash || true

while :; do # Loop infinitely
  # Run server
  last_exit_code=0
  java "${java_args[@]}" || {
    last_exit_code="${?}"
    # Oops, server didn't exit gracefully
    printf 'Detected server crash (exit code: %s)\n' "${?}" >&2
    # Check if we should restart on crash or not
    if should_restart_on_crash; then
      touch "${restart_flag}"
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
