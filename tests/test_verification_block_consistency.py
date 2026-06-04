from __future__ import annotations

from repobrain.output_md import render_answer_markdown


def test_verification_block_not_run_is_consistent_without_counters() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "retrieved": 0,
            "selected": 0,
            "verification_overall": "NOT_RUN",
            "verification_pass_count": 0,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Next",
        command="ask",
    )

    assert "### 🔎 Verification" not in md
    assert "checks were not run." not in md
    assert "Counters: n/a" not in md


def test_verification_block_with_results_shows_real_counters() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "retrieved": 0,
            "selected": 0,
            "verification_pass_count": 2,
            "verification_fail_count": 1,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Next",
        command="ask",
    )

    assert "### 🔎 Verification" not in md
    assert "PASS: 2, WARN: 1, NOT_RUN: 0" not in md
