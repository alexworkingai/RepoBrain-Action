from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_audit_default_does_not_require_llm() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={},
        audit=audit,
    )

    assert "## Narrative interpretation" not in markdown
    assert "## Executive narrative" not in markdown


def test_audit_narrative_mode_adds_llm_summary_without_modifying_score(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "Narrative interpretation: strongest signals and priorities.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 120,
                "llm_model_downgrade_reason": "n/a",
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on product readiness.",
        tky_mode="local",
        github_context_seed={},
        audit=audit,
        narrative_requested=True,
    )

    assert "## Narrative interpretation" in markdown
    assert "Narrative interpretation: strongest signals and priorities." in markdown
    assert "- Score authority: `TopoCore contract`" in markdown
    assert "- Score modified by LLM: `no`" in markdown


def test_audit_executive_mode_adds_executive_section(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "- Executive summary bullet one.\n- Executive summary bullet two.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit executive narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_EXECUTIVE_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 90,
                "llm_model_downgrade_reason": "n/a",
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on partner readiness.",
        tky_mode="local",
        github_context_seed={},
        executive_requested=True,
    )

    assert "## Executive narrative" in markdown
    assert "Executive summary bullet one." in markdown
