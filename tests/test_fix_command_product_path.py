from __future__ import annotations

from repobrain.github_flow import _analyze_fix_request
from repobrain.output_md import render_patch_markdown, render_scoped_command_markdown


def test_pr_fix_renders_product_governance_section_with_visible_safety_markers() -> None:
    md = render_patch_markdown(
        review={
            "summary_text": "Clarify the pilot setup note so the no-patch policy is explicit.",
            "risk_level": "low",
            "risks": ["Workflow guidance is missing the no-patch clarification."],
            "notes": ["Add one sentence to the pilot note describing the disabled patch/apply path."],
            "files_changed": [
                {"path": "docs/repobrain_fix_fixture.md"},
                {"path": "docs/repobrain_fix_notes.md"},
            ],
            "suggested_tests": ["Review the docs wording manually."],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="proposal-only mode: patch application disabled; auto-pr disabled",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "selected": 2,
            "pr_metadata_used": True,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 2,
            "patch_targeting_mode": "localized",
            "patch_targeting_reason": "docs_only_change",
            "localized_patch_evidence_count": 2,
            "patch_grounding_mode": "pr_metadata",
            "patch_authorized": False,
            "patch_applied": False,
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "fallback_used": False,
            "fallback_reason": "none",
        },
    )

    assert "### 🛠️ Fix proposal / governance" in md
    assert "- Status: `PROPOSAL_READY`" in md
    assert "- Scope: `pull_request`" in md
    assert "Affected files:" in md
    assert "`docs/repobrain_fix_fixture.md`" in md
    assert "### 🛡️ Runtime and safety" in md
    assert "- Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created." in md
    assert "safe to merge" not in md.lower()
    assert "security approved" not in md.lower()


def test_pr_fix_can_block_unsafe_mutation_request_safely() -> None:
    md = render_patch_markdown(
        review={
            "summary_text": "Do not mutate the repository from RepoBrain.",
            "risk_level": "medium",
            "risks": ["Mutation was requested from the product fix path."],
            "notes": [],
            "files_changed": [{"path": "docs/repobrain_fix_fixture.md"}],
            "suggested_tests": ["Apply any change manually outside RepoBrain."],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="proposal-only mode: patch application disabled",
        audit_summary={
            "command": "fix",
            "route_final": "WAIT",
            "selected": 1,
            "pr_metadata_used": True,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "Patch/autofix is disabled.",
            "patch_target_files_total": 1,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "unsafe_mutation_request",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
            "patch_authorized": False,
            "patch_applied": False,
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
            "fix_request_requires_mutation": True,
            "fix_status": "BLOCKED_BY_SAFETY",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "fallback_used": False,
            "fallback_reason": "none",
        },
    )

    assert "- Status: `BLOCKED_BY_SAFETY`" in md
    assert "Patch/autofix is disabled." in md
    assert "### 🛡️ Runtime and safety" in md
    assert "- Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created." in md
    assert "patch applied and pushed" not in md.lower()


def test_issue_fix_scope_can_render_full_no_mutation_markers() -> None:
    md = render_scoped_command_markdown(
        title="### ⏳ Scoped command not available",
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
            "files_modified": False,
            "branch_created": False,
            "commit_created": False,
            "pr_created": False,
        },
        next_steps=["Run the command from a PR if you want PR-scoped fix governance."],
    )

    assert "unsupported_issue_context" in md
    assert "### 🛡️ Runtime and safety" in md
    assert "- Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created." in md


def test_fix_request_analysis_detects_unsafe_and_vague_prompts() -> None:
    unsafe = _analyze_fix_request("Apply the patch and commit the changes.")
    unsafe_short = _analyze_fix_request("Apply a patch and commit it.")
    vague = _analyze_fix_request("Fix this.")

    assert unsafe["requests_mutation"] is True
    assert "apply the patch" in unsafe["matched_unsafe_markers"]
    assert unsafe_short["requests_mutation"] is True
    assert "apply a patch" in unsafe_short["matched_unsafe_markers"]
    assert "commit it" in unsafe_short["matched_unsafe_markers"]
    assert vague["is_vague"] is True
