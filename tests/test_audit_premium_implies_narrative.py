from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_audit_premium_profile_implies_narrative_layer(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "- Premium narrative bullet one.\n- Premium narrative bullet two.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: premium audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_PREMIUM_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1",
                "llm_tokens_total": 140,
            },
        ),
    )
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on product readiness.",
        tky_mode="local",
        github_context_seed={},
    )

    assert "## Premium narrative" in markdown
    assert "- Audit narrative mode: `premium`" in markdown
    assert "- LLM: `used for narrative summary only`" in markdown
    assert "- Score modified by LLM: `no`" in markdown


def test_audit_premium_quota_exhaustion_preserves_score(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "",
            {
                "llm_used": False,
                "llm_skip_reason": "budget:remaining_exhausted",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM not used: quota exhausted.",
                "llm_decision_reason_code": "AUDIT_PREMIUM_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_tokens_total": 0,
            },
        ),
    )
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on partner readiness.",
        tky_mode="local",
        github_context_seed={},
    )

    assert "- Audit narrative mode: `premium`" in markdown
    assert "premium narrative skipped, TopoCore score preserved." in markdown
    assert "- Score modified by LLM: `no`" in markdown


def test_audit_premium_provider_unavailable_preserves_score(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "",
            {
                "llm_used": False,
                "llm_skip_reason": "llm_not_available:provider_unavailable",
                "llm_provider_error_type": "provider_unavailable",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM not used: provider unavailable.",
                "llm_decision_reason_code": "AUDIT_PREMIUM_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_tokens_total": 0,
            },
        ),
    )
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on product readiness.",
        tky_mode="local",
        github_context_seed={},
    )

    assert "- Audit narrative mode: `premium`" in markdown
    assert "provider unavailable" in markdown.lower()
    assert "- Score modified by LLM: `no`" in markdown
