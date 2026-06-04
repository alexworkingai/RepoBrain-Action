from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_audit_narrative_quota_exhausted_preserves_topocore_authority(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            None,
            {
                "llm_used": False,
                "llm_skip_reason": "budget:llm_remaining_exhausted",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "LLM quota/limit exhausted; audit score is available and narrative layer was skipped until limits reset.",
                "llm_model_used": "not used",
                "llm_tokens_total": 0,
                "llm_model_downgrade_reason": "n/a",
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on product readiness.",
        tky_mode="local",
        github_context_seed={},
        narrative_requested=True,
    )

    assert "- Score authority: `TopoCore contract`" in markdown
    assert "- Score modified by LLM: `no`" in markdown
    assert "LLM quota/limit exhausted" in markdown
