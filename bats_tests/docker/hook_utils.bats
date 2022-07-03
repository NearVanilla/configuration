setup() {
    load '../test_helper/common-setup'
    _common_setup

    source "${PROJECT_ROOT}/docker/hook_utils.sh"
}

teardown() {
    if [ -n "${BATS_RUN_COMMAND:-}" ]; then
        printf 'RAN: %s\n' "${BATS_RUN_COMMAND}" >&2
    fi
}


run_matches_single_cron() {
    assert [ "${#@}" -eq 2 ]
    run matches_single_cron "${@}"
}

assert_single_cron() {
    run_matches_single_cron "${@}"
    assert_success
}

refute_single_cron() {
    run_matches_single_cron "${@}"
    assert_failure
}

run_matches_cron() {
    assert [ "${#@}" -eq 2 ]
    run matches_cron "${@}"
}

assert_cron() {
    run_matches_cron "${@}"
    assert_success
}

refute_cron() {
    run_matches_cron "${@}"
    assert_failure
}

@test "Test single cron glob" {
    for value in 1 2 3 4 5 10 12; do
        assert_single_cron '*' "${value}"
    done
}

@test "Test single cron exact" {
    for value in 1 2 3 4 5 10 12; do
        assert_single_cron "${value}" "${value}"
        refute_single_cron "${value}" 6
    done
}

@test "Test single cron exact list" {
    list='1,2,3,7'
    for value in 1 2 3 7; do
        assert_single_cron "${list}" "${value}"
    done
    for value in 4 5 6 8 9 10; do
        refute_single_cron "${list}" "${value}"
    done
}

@test "Test single cron range" {
    range="3-7"
    for value in 3 4 5 6 7; do
        assert_single_cron "${range}" "${value}"
    done
    for value in 1 2 8 9 10; do
        refute_single_cron "${range}" "${value}"
    done
}

@test "Test single cron step" {
    step="5/2"
    for value in 5 7 9 11 13; do
        assert_single_cron "${step}" "${value}"
    done
    for value in 1 2 3 4 6 8 10 12; do
        refute_single_cron "${step}" "${value}"
    done
}

@test "Test single cron complex" {
    spec='1,4-6,9/2'
    for value in 1 4 5 6 9 11; do
        assert_single_cron "${spec}" "${value}"
    done
    for value in 2 3 7 8 10 12; do
        refute_single_cron "${spec}" "${value}"
    done
}

@test "Test single cron number edge cases" {
    assert_single_cron 01 1
    assert_single_cron 1 01
    assert_single_cron 01 01
}

@test "Test single cron step edge cases" {
    assert_single_cron "*/2" 0
    refute_single_cron "*/2" 1
    assert_single_cron "*/2" 2
}

@test "Test cron exact date" {
    ts="$(date --date "2022-01-08 21:37" +%s)" # Saturday
    # m h dom mon dow
    # List of positive cron specs which should match the above timestamp
    positive=(
        "* * * * *"
        "37 21 08 01 6"
        "37 * * * *"
        "* 21 * * *"
        "* * 8 * *"
        "* * * 1 *"
        "* * * * 6"
        "* * */2 * *"
        "7,37 * * * *"
    )
    # List of negative cron specs which should NOT match the above timestamp
    negative=(
        "1 1 1 1 1"
    )
    for spec in "${positive[@]}"; do
        assert_cron "${spec}" "${ts}"
        read -r h m dom mon dow <<<"${spec}"
        negative+=(
            "3 ${m} ${dom} ${mon} ${dow}"
            "${h} 3 ${dom} ${mon} ${dow}"
            "${h} ${m} 3 ${mon} ${dow}"
            "${h} ${m} ${dom} 3 ${dow}"
            "${h} ${m} ${dom} ${mon} 3"
        )
    done
    for spec in "${negative[@]}"; do
        refute_cron "${spec}" "${ts}"
    done
}
