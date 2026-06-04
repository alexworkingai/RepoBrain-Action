from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_pr_audit_narrative_falls_back_to_canonical_pr_facts_on_contradiction(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Narrative interpretation\n- Repo remains solid.\n\n## PR impact summary\n- This PR is likely behavior-affecting.\n- Risk is moderate.\n- Security impact should be reviewed.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 111,
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on this PR in the context of MCP product readiness.",
        tky_mode="local",
        github_context_seed={
            "event_name": "issue_comment",
            "is_pr": True,
            "pr_number": 41,
            "changed_files": ["docs/repobrain_manual_pr_smoke.md"],
        },
        narrative_requested=True,
    )

    assert "## PR impact summary" in markdown
    assert "Change type: `docs-only`" in markdown
    assert "Behavior-affecting: `no`" in markdown
    assert "Risk level: `LOW`" in markdown
    assert "likely behavior-affecting" not in markdown.lower()
    assert "moderate" not in markdown.lower()

