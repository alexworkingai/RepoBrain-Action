from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_pr_audit_headings_are_not_duplicated(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Premium narrative\n- Overall score drivers.\n\n## PR impact summary\n- Docs-only change.\n- Validation remains lightweight.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: premium audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_PREMIUM_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1",
                "llm_tokens_total": 180,
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on this PR for selected partner pilot readiness.",
        tky_mode="local",
        github_context_seed={"event_name": "issue_comment", "is_pr": True, "pr_number": 41},
    )

    assert markdown.count("## Premium narrative") == 1
    assert markdown.count("## PR impact summary") == 1
    assert "## Narrative interpretation\n## Narrative interpretation" not in markdown
