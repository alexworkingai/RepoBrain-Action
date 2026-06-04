from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _maybe_refine_operational_ask_answer


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_pr_ask_assessment_stays_pr_scoped_for_docs_only_change(tmp_path: Path) -> None:
    _write(tmp_path / ".github" / "workflows" / "repobrain.yml", "name: RepoBrain\n")

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question=(
            "Assess this PR in the context of the MCP product. Does this change affect product functionality, "
            "architecture, runtime behavior, security posture, tests, documentation quality, production readiness, "
            "or partner-pilot readiness? Identify risk level, touched modules, required validation, and whether the change is docs-only or behavior-affecting."
        ),
        answer_text="placeholder",
        next_steps="placeholder",
        audit_summary={"route_final": "REVIEW", "llm_used": True},
        github_context={
            "repository": "owner/consumer-repo",
            "is_pr": True,
            "pr_number": 41,
            "files": [
                {"filename": "docs/repobrain_pr_smoke_fixture.md", "status": "modified"},
                {"filename": "README.md", "status": "modified"},
            ],
        },
    )

    assert "PR impact summary:" in answer_text
    assert "Change type:" in answer_text
    assert "`docs-only`" in answer_text
    assert "Behavior-affecting: `no`" in answer_text
    assert "Architecture/runtime impact:" in answer_text
    assert "- no direct impact" in answer_text
    assert "Security posture impact:" in answer_text
    assert "Risk level:" in answer_text and "`LOW`" in answer_text
    assert "RepoBrain-Action currently looks like" not in answer_text
    assert audit_summary["route_final"] == "ASK"
    assert audit_summary["operational_ask_kind"] == "pr_impact_assessment"
    assert next_steps.startswith("Review the changed files")
