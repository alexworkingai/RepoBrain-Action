from __future__ import annotations

from repobrain.output_md import render_patch_markdown, render_review_markdown


def _primary(markdown: str) -> str:
    return markdown.split("<details>", 1)[0]


def _details(markdown: str) -> str:
    parts = markdown.split("<details>", 1)
    return parts[1] if len(parts) > 1 else ""


def test_review_default_omits_detailed_verification_counters() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Compact summary.",
            "risk_level": "low",
            "files_block": ["- `docs/example.md`"],
            "confirmed_findings": [],
            "possible_signals": ["Possible wording drift."],
            "informational_notes": ["Docs-only context."],
            "recommendations": ["Run CI."],
        },
        verification_report={
            "summary": "NOT_RUN",
            "trusted_context": False,
            "dynamic_verify": False,
            "ruff": "NOT_RUN",
            "pytest": "NOT_RUN",
        },
        audit_summary={"command": "review", "route_final": "REVIEW", "selected": 1},
    )

    assert "trusted_context" not in _primary(md)
    assert "dynamic_verify" not in _primary(md)
    assert "pytest" not in _primary(md)
    assert "Verification summary" in _primary(md)
    assert "trusted_context" not in _details(md)


def test_fix_default_omits_patch_validation_and_artifact_noise() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Compact proposal.", "risk_level": "low", "files_changed": [], "suggested_tests": []},
        verification_report={"summary": "NOT_RUN", "trusted_context": False, "dynamic_verify": False},
        patch_snippet="diff --git a/x b/x",
        patch_written=False,
        patch_apply_message="proposal-only mode",
        audit_summary={
            "command": "fix",
            "route_final": "FIX",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 0,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_patch",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
        },
    )

    primary = _primary(md)
    assert "Patch validation" not in primary
    assert "Patch artifact" not in primary
    assert "Apply status" not in primary
    assert "Verification summary" in primary
    assert "Patch validation" not in _details(md)
