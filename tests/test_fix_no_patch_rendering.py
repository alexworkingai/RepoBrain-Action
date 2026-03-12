from __future__ import annotations

from repobrain.output_md import render_patch_markdown


def test_fix_no_patch_is_rendered_as_intentional_safe_outcome() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Generic review summary that should not dominate fix output."},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome: no sufficiently localized target",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": (
                "No patch generated: no sufficiently localized, evidence-backed patch target was found."
            ),
            "patch_target_files_total": 12,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
        },
    )

    assert "Summary: No patch generated: no sufficiently localized, evidence-backed patch target was found." in md
    assert "### 🧾 Patch result" in md
    assert "### 🎯 Patch targeting" in md
    assert "### ✅ Patch validation" in md
    assert "Outcome: safe no_patch (no grounded localized target)." in md
    assert "No patch generated (safe outcome)." in md
    assert "### ✅ PR Review" not in md
