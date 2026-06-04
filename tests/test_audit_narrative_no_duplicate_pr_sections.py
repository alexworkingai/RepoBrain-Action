from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_audit_markdown


def _section(markdown: str, heading: str) -> str:
    start = markdown.index(heading)
    tail = markdown[start + len(heading):]
    next_heading = tail.find("\n## ")
    if next_heading == -1:
        return tail.strip()
    return tail[:next_heading].strip()


def test_pr_audit_narrative_sections_are_distinct(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Narrative interpretation\n- Overall score is held back by governance and release hygiene.\n- Strongest signals remain testing and no-mutation safety.\n\n## PR impact\n- Changed files are documentation-heavy.\n- Runtime behavior stays bounded.\n- Validation impact is low.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 130,
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on this PR in the context of MCP product readiness.",
        tky_mode="local",
        github_context_seed={"event_name": "issue_comment", "is_pr": True, "pr_number": 41},
        narrative_requested=True,
    )

    assert "## Narrative interpretation" in markdown
    assert "## PR impact summary" in markdown
    overall = _section(markdown, "## Narrative interpretation")
    pr_impact = _section(markdown, "## PR impact summary")
    assert overall != pr_impact
    assert "Changed files" in markdown or "documentation-heavy" in pr_impact.lower()


def test_pr_audit_executive_sections_are_distinct(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Executive narrative\n- Overall repo readiness remains strong for partner-facing use.\n- Main caution remains governance follow-through.\n\n## PR impact\n- This PR is low risk and mostly docs-facing.\n- Validation should focus on comment UX and command wording.",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: audit executive narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_EXECUTIVE_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 110,
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on this PR for selected partner pilot readiness.",
        tky_mode="local",
        github_context_seed={"event_name": "issue_comment", "is_pr": True, "pr_number": 41},
        executive_requested=True,
    )

    assert "## Executive narrative" in markdown
    assert "## PR impact summary" in markdown
    overall = _section(markdown, "## Executive narrative")
    pr_impact = _section(markdown, "## PR impact summary")
    assert overall != pr_impact
