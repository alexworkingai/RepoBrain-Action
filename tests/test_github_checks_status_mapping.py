from __future__ import annotations

from repobrain.checks_md import map_check_conclusion


def test_fix_valid_patch_maps_to_success() -> None:
    conclusion = map_check_conclusion(
        cmd="fix",
        audit={"patch_generation_result": "valid_patch", "route_final": "FAST"},
        base_conclusion="neutral",
    )
    assert conclusion == "success"


def test_fix_no_patch_maps_to_neutral() -> None:
    conclusion = map_check_conclusion(
        cmd="fix",
        audit={"patch_generation_result": "no_patch", "route_final": "FAST"},
        base_conclusion="success",
    )
    assert conclusion == "neutral"


def test_fix_provider_failed_maps_to_failure() -> None:
    conclusion = map_check_conclusion(
        cmd="fix",
        audit={"patch_generation_result": "provider_failed", "route_final": "FAST"},
        base_conclusion="neutral",
    )
    assert conclusion == "failure"


def test_closed_or_merged_skip_maps_to_neutral() -> None:
    conclusion = map_check_conclusion(
        cmd="review",
        audit={
            "route_final": "WAIT",
            "skip_reason_code": "pr_closed_or_merged_review",
            "skip_reason_short": "Skipped on closed PR.",
        },
        base_conclusion="success",
    )
    assert conclusion == "neutral"


def test_ask_completed_keeps_success() -> None:
    conclusion = map_check_conclusion(
        cmd="ask",
        audit={"route_final": "FAST"},
        base_conclusion="success",
    )
    assert conclusion == "success"
