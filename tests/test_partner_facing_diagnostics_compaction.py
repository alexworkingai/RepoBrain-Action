from __future__ import annotations

import pytest

from repobrain.output_md import render_answer_markdown


def test_default_issue_mode_output_is_compact() -> None:
    md = render_answer_markdown(
        answer_text="Operational answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "execution_mode": "retrieval_only",
            "llm_used": False,
            "llm_skip_reason": "issue_comment_policy_disabled",
            "llm_runtime_override_reason": "LLM blocked: issue_comment policy disabled.",
            "retrieval_ranking_mode": "lexical",
            "hybrid_rerank_used": False,
            "remote_skipped_reason": "n/a",
            "tky_fallback_reason": "none",
        },
        next_steps="Validate the workflow settings.",
        command="ask",
    )

    assert "Runtime diagnostics" not in md
    assert "### Secondary diagnostics" not in md
    assert "### Async batch orchestration" not in md
    assert "- LLM: not called" in md
    assert "policy disabled" in md


def test_verbose_mode_restores_partner_facing_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_answer_markdown(
        answer_text="Operational answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "execution_mode": "retrieval_only",
            "llm_used": False,
            "llm_skip_reason": "issue_comment_policy_disabled",
            "llm_runtime_override_reason": "LLM blocked: issue_comment policy disabled.",
            "retrieval_ranking_mode": "lexical",
            "hybrid_rerank_used": False,
            "remote_skipped_reason": "n/a",
            "tky_fallback_reason": "none",
        },
        next_steps="Validate the workflow settings.",
        command="ask",
    )

    assert "<summary>Evidence and diagnostics</summary>" in md
    assert "LLM used: no (issue_comment_policy_disabled)" in md
    assert "### Secondary diagnostics" in md
