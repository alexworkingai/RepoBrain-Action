from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def test_pr_audit_narrative_renders_pr_narrative_impact(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Narrative interpretation\n- Overall score remains strong.\n- Main drivers are documentation maturity and workflow clarity.\n\n## PR impact\n- Changed-file summary.\n- Runtime implications.\n- Reviewer-friendly risk summary.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 111,
                "llm_model_downgrade_reason": "n/a",
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
            "changed_files": ["docs/manual-smoke.md", "README.md"],
            "files": [
                {"filename": "docs/manual-smoke.md", "status": "modified"},
                {"filename": "README.md", "status": "modified"},
            ],
        },
        narrative_requested=True,
    )

    assert "## PR narrative impact" in markdown
    assert "## Narrative interpretation" in markdown
    assert "Runtime implications" in markdown
    assert "- Score modified by LLM: `no`" in markdown
