from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _public_readiness_next_step, _read_public_readiness_status


ROOT = Path(__file__).resolve().parents[1]


def test_product_status_after_pr119_merge_is_not_stale() -> None:
    status = _read_public_readiness_status(ROOT)

    assert status == "SPRINT_92F_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING"
    next_step = _public_readiness_next_step(status)
    assert "live retest" in next_step.lower() or "partner onboarding" in next_step.lower()
