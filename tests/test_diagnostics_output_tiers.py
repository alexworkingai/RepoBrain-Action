from __future__ import annotations

import pytest

from repobrain.output_md import render_answer_markdown


def _summary() -> dict[str, object]:
    return {
        "command": "ask",
        "route_final": "FAST",
        "requested_backend": "auto",
        "resolved_backend": "v6",
        "fallback_used": False,
        "fallback_reason": "none",
        "tky_mode_requested": "local",
        "tky_mode_used": "local",
        "tky_engine": "topocore_v6",
        "tkya_backend": "v6",
        "selected": 1,
        "verification_not_run_count": 1,
    }


def test_default_output_hides_raw_tky_tkya_fields() -> None:
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary=_summary(),
        next_steps="Check sources",
        command="ask",
    )

    assert "TKY mode requested" not in md
    assert "TKYA mode" not in md
    assert "retrieval snapshot cache" not in md.lower()
    assert "async batch orchestration" not in md.lower()


def test_verbose_mode_can_render_expanded_runtime_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary=_summary(),
        next_steps="Check sources",
        command="ask",
    )

    assert "TKY mode requested" in md
    assert "TKYA mode" in md
