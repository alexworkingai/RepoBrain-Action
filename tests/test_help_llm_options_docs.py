from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import HELP_TEXT


def test_help_includes_issue_llm_and_audit_narrative_modes() -> None:
    assert "/repobrain audit --narrative" in HELP_TEXT
    assert "/repobrain audit --executive" in HELP_TEXT
    assert "/repobrain audit --profile premium" in HELP_TEXT
    assert "RB_REPOBRAIN_ENABLE_ISSUE_LLM=1" in HELP_TEXT


def test_command_docs_cover_quota_fallback_and_score_authority() -> None:
    command_docs = Path("docs/commands/REPOBRAIN_COMMANDS.md").read_text(encoding="utf-8")
    assert "quota" in command_docs.lower()
    assert "TopoCore" in command_docs
    assert "does not change final score" in command_docs
