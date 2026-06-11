from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _build_audit_markdown


def test_pr_premium_output_renders_complete_deterministic_pr_impact_block(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Premium narrative\n"
            "- High-level premium summary.\n\n"
            "## PR impact summary\n"
            "- Changed files: `docs/repobrain_manual_pr_smoke.md`\n"
            "- This PR remains docs oriented.\n"
            "- Validation remains lightweight.\n",
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
        query="Focus on this docs-only PR for partner-readiness review.",
        tky_mode="local",
        github_context_seed={
            "event_name": "issue_comment",
            "is_pr": True,
            "pr_number": 41,
            "changed_files": ["docs/repobrain_manual_pr_smoke.md"],
        },
    )

    assert "## PR impact summary" in markdown
    assert "- Changed files: `docs/repobrain_manual_pr_smoke.md`" in markdown
    assert "- Change type: `docs-only`" in markdown
    assert "- Behavior-affecting: `no`" in markdown
    assert "- Architecture/runtime impact: no direct impact" in markdown
    assert "- Security impact: no direct impact" in markdown
    assert "- Validation needed: docs accuracy review plus optional docs checks" in markdown
    assert "- Production readiness effect: neutral or minor positive documentation polish" in markdown
    assert "- Partner-pilot effect: neutral or minor positive documentation clarity" in markdown
    assert "- Risk level: `LOW`" in markdown
    assert "- Limitations: PR-scoped assessment only; not a merge, security, legal, or production approval." in markdown
    assert markdown.index("## PR impact summary") < markdown.index("## Executive summary")
    assert "Changed files: 1 (`docs/repobrain_manual_pr" not in markdown
    assert "### Reviewer notes" not in markdown
    assert "- Score modified by LLM: `no`" in markdown


def test_pr_premium_overlong_llm_narrative_fallback_preserves_deterministic_pr_block(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")
    giant_premium = " ".join(["premium"] * 20000)

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Premium narrative\n"
            + giant_premium
            + "\n\n## PR impact summary\n- This PR might affect behavior.\n- Risk is moderate.\n",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": "LLM used: premium audit narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_PREMIUM_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1",
                "llm_tokens_total": 8000,
            },
        ),
    )

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on this docs-only PR for partner-readiness review.",
        tky_mode="local",
        github_context_seed={
            "event_name": "issue_comment",
            "is_pr": True,
            "pr_number": 41,
            "changed_files": ["docs/repobrain_manual_pr_smoke.md"],
        },
    )

    assert "_Output truncated to keep GitHub comment size safe._" not in markdown
    assert "## PR impact summary" in markdown
    assert "- Changed files: `docs/repobrain_manual_pr_smoke.md`" in markdown
    assert "- Change type: `docs-only`" in markdown
    assert "- Risk level: `LOW`" in markdown
    assert markdown.index("## PR impact summary") < markdown.index("## Executive summary")
    assert "### Reviewer notes" not in markdown
    assert "might affect behavior" not in markdown.lower()
    assert "moderate" not in markdown.lower()
    assert "- Score modified by LLM: `no`" in markdown
