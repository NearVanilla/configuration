setup() {
    load '../test_helper/common-setup'
    _common_setup

    script="${PROJECT_ROOT}/docker/run_hooks.sh"
    source "${script}"
}

teardown() {
    if [ -n "${BATS_RUN_COMMAND:-}" ]; then
        printf 'RAN: %s\n' "${BATS_RUN_COMMAND}" >&2
    fi
}


@test "Ran hook has available hook_utils" {
  hook="$BATS_TEST_TMPDIR/hook.sh"
  local hook_utils="${PROJECT_ROOT}/docker/hook_utils.sh"
  local function_list
  function_list="$(sed -n 's/^\([[:alpha:]_]\+\)() .*/\1/p' "${hook_utils}")"
  export function_list
  cat >| "${hook}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [ -z "${function_list:-}" ]; then
  echo "Empty function_list!"
  exit 1
fi
while read -r function_name; do
  if [ -z "${function_name:-}" ]; then
    echo "Read empty function name!"
    exit 1
  fi
  if type="$(LC_ALL=C type -t "${function_name}")"; then
    if [ "${type}" != function ]; then
      echo "Expected ${function_name} to be a function, not ${type}"
      exit 1
    fi
  else
    echo "Unable to find function ${function_name}"
    exit 1
  fi
done <<<"${function_list}"
EOF
  chmod +x "${hook}"
  run run_hook "${hook}"
  assert_success
}
