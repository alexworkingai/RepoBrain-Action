from __future__ import annotations

from pathlib import Path

import yaml

from repobrain.github_flow import _build_verify_markdown, run_github_flow
from repobrain.output_md import render_answer_markdown, render_review_markdown


_ROOT = Path(__file__).resolve().parents[1]


def _load_workflow_yaml() -> dict[str, object]:
    return yaml.safe_load((_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8"))


def test_issue_comment_action_step_exports_effective_topocore_backend_env() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    action_step = next(step for step in steps if step.get("uses") == "./.")

    env_expr = action_step["env"]["RB_TOPOCORE_BACKEND"]
    with_expr = action_step["with"]["topocore_backend"]

    assert "github.event_name == 'workflow_dispatch'" in env_expr
    assert "github.event.inputs.topocore_backend" in env_expr
    assert "'auto'" in env_expr
    assert "'v5'" not in env_expr
    assert with_expr == env_expr


def test_action_prefers_explicit_workflow_backend_env_before_input_default() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_BACKEND: ${{ env.RB_TOPOCORE_BACKEND || inputs.topocore_backend }}" in action_text


def test_pr_ask_markdown_renders_topocore_backend_evidence() -> None:
    markdown = render_answer_markdown(
        answer_text="PR summary.",
        evidence=[],
        audit_summary={
            "route_final": "REVIEW",
            "repobrain_version": "test",
            "tkya_backend": "v5",
            "tky_engine": "topocore_v6",
            "tky_mode_requested": "local",
            "tky_mode_used": "local",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "backend_mode": "auto",
            "fallback_used": False,
            "fallback_reason": "none",
            "pr_metadata_used": True,
            "pr_changed_files_count": 3,
            "selected": 0,
            "verification_pass_count": 0,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Inspect the PR evidence.",
        command="ask",
    )

    assert "### 🛡️ Runtime and safety" in markdown
    assert "- Backend: `auto -> v6`" in markdown
    assert "TopoCore backend requested" not in markdown


def test_pr_review_markdown_renders_topocore_backend_evidence() -> None:
    markdown = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "medium",
            "files_block": ["repobrain/github_flow.py"],
            "confirmed_findings": [],
            "possible_signals": [],
            "recommendations": ["Run the relevant PR checks."],
            "informational_notes": ["Scoped observation run."],
            "risk_drivers": ["PR-path TopoCore evidence."],
        },
        verification_report={"summary": "Verification WARN", "overall": "WARN"},
        audit_summary={
            "route_final": "REVIEW",
            "repobrain_version": "test",
            "tkya_backend": "v5",
            "tky_engine": "topocore_v6",
            "tky_mode_requested": "local",
            "tky_mode_used": "local",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "backend_mode": "auto",
            "fallback_used": False,
            "fallback_reason": "none",
            "selected": 0,
            "verification_pass_count": 0,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
    )

    assert "### 🛡️ Runtime and safety" in markdown
    assert "- Backend: `auto -> v6`" in markdown
    assert "TopoCore backend requested" not in markdown


def test_pr_verify_emits_explicit_scoped_backend_diagnostics() -> None:
    audit: dict[str, object] = {}

    markdown = _build_verify_markdown(
        tky_mode="local",
        is_pull_request=True,
        issue_number=87,
        dry_run=True,
        client=None,
        audit=audit,
    )

    assert "Runtime and safety" in markdown
    assert "verification report" in markdown
    assert "verify_report_only" not in markdown
    assert audit["requested_backend"] == "auto"
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["scope_status"] == "verify_report_only"


def test_issue_only_review_is_explicitly_scoped(capsys) -> None:
    status = run_github_flow(
        repo_root=_ROOT,
        dry_run=True,
        comment_text="/repobrain review Summarize the current risks.",
        issue_number=None,
        tky_mode="local",
    )
    output = capsys.readouterr().out

    assert status == "DRY_RUN_OK"
    assert "Scoped command not available" in output
    assert "unsupported in issue-only context" in output or "pull-request scoped" in output
    assert "Scope status" in output
    assert "unsupported_issue_context" in output


def test_issue_only_fix_is_explicitly_scoped_and_patch_safe(capsys) -> None:
    status = run_github_flow(
        repo_root=_ROOT,
        dry_run=True,
        comment_text="/repobrain fix Summarize fix-lite governance status without applying patches.",
        issue_number=None,
        tky_mode="local",
    )
    output = capsys.readouterr().out

    assert status == "DRY_RUN_OK"
    assert "Scoped command not available" in output
    assert "pull-request scoped" in output
    assert "no patch/autofix" in output
    assert "no branch/commit/PR created" in output
    assert "Scope status: `unsupported_issue_context`" in output
