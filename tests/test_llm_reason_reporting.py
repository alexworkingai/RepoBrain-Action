from __future__ import annotations

from repobrain.github_flow import _runtime_override_reason_from_skip
from repobrain.output_md import render_answer_markdown


def test_markdown_includes_tkya_llm_reason_lines() -> None:
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "retrieved": 5,
            "selected": 1,
            "llm_used": False,
            "llm_skip_reason": "n/a",
            "execution_mode": "retrieval_only",
            "llm_decision_reason_short": "LLM not used: direct answer available from retrieved evidence.",
            "llm_decision_reason_code": "DIRECT_EVIDENCE_SUFFICIENT",
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "TKYA LLM decision: not used" in md
    assert "Reason: LLM not used: direct answer available from retrieved evidence." in md


def test_runtime_override_is_rendered_when_tkya_wanted_llm_but_runtime_blocked() -> None:
    override = _runtime_override_reason_from_skip("disabled")
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 20,
            "selected": 4,
            "llm_used": False,
            "llm_skip_reason": "disabled",
            "execution_mode": "retrieval_plus_llm",
            "llm_decision_reason_short": "LLM used: multi-source synthesis required after retrieval.",
            "llm_decision_reason_code": "MULTI_SOURCE_SYNTHESIS_REQUIRED",
            "llm_runtime_override_reason": override,
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "TKYA LLM decision: used" in md
    assert "Reason: LLM used: multi-source synthesis required after retrieval." in md
    assert "Runtime override: LLM blocked: disabled by runtime policy." in md
