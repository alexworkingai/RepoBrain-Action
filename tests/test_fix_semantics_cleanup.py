from __future__ import annotations

from repobrain.github_flow import _normalize_fix_semantics
from repobrain.output_md import render_patch_markdown


def test_fix_semantics_maps_review_reason_to_patch_reason() -> None:
    intent, code, short = _normalize_fix_semantics(
        execution_mode="retrieval_plus_llm",
        llm_intent="review",
        reason_code="REVIEW_SYNTHESIS_REQUIRED",
        reason_short="LLM used: review synthesis required for PR analysis.",
    )

    assert intent == "patch"
    assert code == "PATCH_SYNTHESIS_REQUIRED"
    assert "patch synthesis required" in short.lower()


def test_render_patch_markdown_uses_patch_specific_sections() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch synthesis summary"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-x\n+y",
        patch_written=True,
        patch_apply_message="auto-apply disabled",
        audit_summary={
            "patch_generation_result": "valid_patch",
            "patch_validation_result": "valid_patch",
            "patch_validation_reason": "Patch validated.",
            "patch_target_files_count": 2,
            "patch_target_files_selected": 2,
            "patch_target_files_total": 3,
            "patch_targeting_mode": "localized",
            "patch_targeting_reason": "patch_target_narrowed_to_localized_subset",
            "patch_grounding_mode": "pr_metadata",
            "route_final": "FAST",
            "pass_count": 1,
            "command": "fix",
        },
    )

    assert "### 🧾 Patch result" in md
    assert "### 🎯 Patch targeting" in md
    assert "### ✅ Patch validation" in md
    assert "Patch generation result: `valid_patch`" in md
    assert "Patch target files selected: 2" in md
    assert "### ⚠️ Confirmed findings" not in md
    assert "### 🟡 Possible signals" not in md
