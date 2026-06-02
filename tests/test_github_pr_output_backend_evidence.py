from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_verify_markdown
from repobrain.output_md import (
    render_answer_markdown,
    render_review_markdown,
    render_scoped_command_markdown,
)


_ROOT = Path(__file__).resolve().parents[1]


def _gate_one_v6_audit() -> dict[str, object]:
    return {
        "route_final": "REVIEW",
        "repobrain_version": "test",
        "pr_metadata_used": True,
        "pr_changed_files_count": 3,
        "tky_mode_requested": "local",
        "tky_mode_used": "local",
        "tky_engine": "topocore_v6",
        "tkya_backend": "v5",
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
    }


def _gate_zero_v5_audit() -> dict[str, object]:
    return {
        "route_final": "FAST",
        "repobrain_version": "test",
        "pr_metadata_used": True,
        "pr_changed_files_count": 2,
        "tky_mode_requested": "auto",
        "tky_mode_used": "baseline",
        "tkya_backend": "v5",
        "tky_engine": "baseline-policy",
        "requested_backend": "v5",
        "resolved_backend": "v5",
        "backend_mode": "v5",
        "fallback_used": False,
        "fallback_reason": "none",
        "selected": 0,
        "verification_pass_count": 0,
        "verification_fail_count": 0,
        "verification_pending_count": 0,
        "verification_not_run_count": 0,
    }


def test_pr_ask_output_uses_compact_runtime_and_llm_blocks_by_default() -> None:
    markdown = render_answer_markdown(
        answer_text="PR summary.",
        evidence=[],
        audit_summary=_gate_one_v6_audit(),
        next_steps="Inspect the PR evidence.",
        command="ask",
    )

    assert "### 🛡️ Runtime and safety" in markdown
    assert "- Backend: `auto -> v6`" in markdown
    assert "- Runtime: `retrieval-only`" in markdown
    assert "- LLM: not called" in markdown
    assert "TKY mode requested" not in markdown
    assert "TKYA mode" not in markdown


def test_pr_review_output_stays_compact_without_merge_claims() -> None:
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
        audit_summary=_gate_one_v6_audit(),
    )

    assert "### 🛡️ Runtime and safety" in markdown
    assert "- Backend: `auto -> v6`" in markdown
    assert "TKY mode requested" not in markdown
    assert "safe-to-merge" not in markdown.lower()
    assert "security-approved" not in markdown.lower()


def test_pr_verify_output_uses_compact_report_only_scope() -> None:
    audit: dict[str, object] = {}

    markdown = _build_verify_markdown(
        tky_mode="local",
        is_pull_request=True,
        issue_number=87,
        dry_run=True,
        client=None,
        audit=audit,
    )

    assert "### 🛡️ Runtime and safety" in markdown
    assert "- Scope: `verification report`" in markdown
    assert "- Runtime: `report-only`" in markdown
    assert "verify_report_only" not in markdown
    assert "TopoCore backend requested" not in markdown
    assert "safe-to-merge" not in markdown.lower()
    assert "approved" not in markdown.lower()


def test_backend_evidence_renderer_handles_missing_fields_safely() -> None:
    markdown = render_answer_markdown(
        answer_text="PR summary.",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "pr_metadata_used": True,
            "pr_changed_files_count": 1,
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
    assert "- Backend: `not applicable`" in markdown
    assert "- Fallback: `not applicable`" in markdown


def test_gate_zero_backend_evidence_can_show_v5_compactly() -> None:
    markdown = render_answer_markdown(
        answer_text="Issue summary.",
        evidence=[],
        audit_summary=_gate_zero_v5_audit(),
        next_steps="Inspect the runtime state.",
        command="ask",
    )

    assert "- Backend: `v5 -> v5`" in markdown
    assert "TKY mode requested" not in markdown
    assert "TKYA mode" not in markdown


def test_scoped_unsupported_issue_fix_preserves_scope_and_patch_safety() -> None:
    markdown = render_scoped_command_markdown(
        title="### Scoped command not available",
        message="Fix is unsupported in issue-only context.",
        audit_summary={
            "route_final": "WAIT",
            "tky_mode_requested": "local",
            "tky_mode_used": "local",
            "tkya_mode": "scoped_unsupported",
            "requested_backend": "auto",
            "resolved_backend": "not_applicable",
            "fallback_used": "not_applicable",
            "fallback_reason": "unsupported_issue_context",
            "scope_status": "unsupported_issue_context",
            "patch_authorized": False,
            "patch_applied": False,
        },
        next_steps=["Run the command from a supported context."],
    )

    assert "unsupported_issue_context" in markdown
    assert "- Backend: `auto -> not_applicable`" in markdown
    assert "- Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created." in markdown


def test_changed_paths_do_not_introduce_runtime_patch_or_pr_side_effects() -> None:
    changed_files = [
        _ROOT / "repobrain" / "output_md.py",
        _ROOT / "repobrain" / "github_flow.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in changed_files)

    assert "gh pr create" not in combined
    assert "git push" not in combined
    assert "git commit" not in combined


def test_changed_paths_do_not_introduce_decide_raw_call() -> None:
    changed_files = [
        _ROOT / "repobrain" / "output_md.py",
        _ROOT / "repobrain" / "github_flow.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in changed_files)

    assert "decide_raw(" not in combined
