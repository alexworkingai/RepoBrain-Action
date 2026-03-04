from repobrain.rd_rollout import canary_enabled, resolve_rollout_mode


def test_canary_bounds() -> None:
    assert canary_enabled(percent=0, key="repo-a") is False
    assert canary_enabled(percent=100, key="repo-a") is True


def test_resolve_rollout_mode_falls_back_when_canary_misses() -> None:
    mode = resolve_rollout_mode(
        requested_mode="rd",
        canary_percent=0,
        canary_key="repo-a",
        fallback_mode="lite",
    )
    assert mode == "lite"
