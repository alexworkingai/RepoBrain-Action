from __future__ import annotations

from repobrain.output_md import render_answer_markdown, render_patch_markdown, render_review_markdown


def _primary(md: str) -> str:
    return md.split("<details>", 1)[0]


def test_ask_primary_output_is_compact_and_segment_visible() -> None:
    md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "selected": 4,
            "answer_grounding_mode": "hybrid",
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=yes",
            "incremental_retrieval_used": True,
            "incremental_scope_mode": "changed_files_first",
            "evidence_budget_mode": "ask_dense_incremental",
            "evidence_budget_used": 9,
        },
        next_steps="Validate the proposed change list.",
        command="ask",
    )

    primary = _primary(md)
    assert "Run summary" in primary
    assert "- Segment summary: `primary=core_code:repobrain; support=tests:tests; cross_segment=yes`" in primary
    assert "Evidence (What I used)" not in primary
    assert "LLM" not in primary
    assert "### Embeddings" not in primary
    assert "Route details" not in primary
    assert "Runtime diagnostics" not in primary
    assert "<summary>Evidence and diagnostics</summary>" in md


def test_review_primary_output_is_tiered_and_non_duplicative() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review completed with focused risk assessment.",
            "risk_level": "medium",
            "files_block": ["- `repobrain/github_flow.py`", "- `docs/artifacts.md`"],
            "confirmed_findings": [],
            "possible_signals": ["Potential config drift"],
            "informational_notes": ["Docs updated"],
            "recommendations": ["Run CI", "Smoke test command flow"],
            "risk_drivers": ["workflow changes"],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=docs:docs; cross_segment=yes",
        },
    )

    primary = _primary(md)
    assert "PR Review" in primary
    assert "- Decision snapshot: findings `0` | signals `1` | notes `1`" in primary
    assert "- Segment summary: `primary=core_code:repobrain; support=docs:docs; cross_segment=yes`" in primary
    assert "Touched files" not in primary
    assert "Recommendations" in primary
    assert "LLM" not in primary
    assert "### Embeddings" not in primary
    assert "Runtime diagnostics" not in primary


def test_fix_primary_output_focuses_on_outcome_not_full_patch_dump() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="diff --git a/a.py b/a.py",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 5,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "localized_patch_evidence_count": 0,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=no",
        },
    )

    primary = _primary(md)
    assert "Patch result" in primary
    assert "- Result: `no_patch`" in primary
    assert "Patch targeting" not in primary
    assert "LLM" not in primary
    assert "### Embeddings" not in primary
    assert "Runtime diagnostics" not in primary


def test_ask_output_no_long_touched_files_duplication() -> None:
    md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "touched_files": [f"repobrain/file_{idx}.py" for idx in range(10)],
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=no",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "Touched files:" not in _primary(md)


def test_ask_primary_hides_next_steps_and_audit_anchors() -> None:
    md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "selected": 2,
            "answer_grounding_mode": "retrieval",
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=no",
        },
        next_steps="Do additional validation",
        command="ask",
    )
    primary = _primary(md)
    assert "Next steps" not in primary
    assert "Audit anchors" not in primary
    assert "<summary>Evidence and diagnostics</summary>" in md
    assert "Next steps" in md
    assert "Audit anchors" in md


def test_review_primary_hides_audit_anchors_but_keeps_them_in_details() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "low",
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": ["Run CI checks"],
            "files_block": ["- `repobrain/output_md.py`"],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"command": "review", "route_final": "FAST"},
    )
    primary = _primary(md)
    assert "Audit anchors" not in primary
    assert "<summary>Evidence and diagnostics</summary>" in md
    assert "Audit anchors" in md


def test_fix_primary_hides_audit_anchors_but_keeps_them_in_details() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "localized_patch_evidence_count": 0,
        },
    )
    primary = _primary(md)
    assert "Audit anchors" not in primary
    assert "<summary>Evidence and diagnostics</summary>" in md
    assert "Audit anchors" in md


def test_primary_surfaces_do_not_show_ultra_large_pr_mode_block() -> None:
    ask_md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "changed_files_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 10,
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests; bounded_files_est=40",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
        },
        next_steps="n/a",
        command="ask",
    )
    review_md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "low",
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
            "files_block": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "changed_regions_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 18,
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain",
            "ultra_large_pr_bounded_coverage_summary": "support=docs:docs; bounded_files_est=23",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
        },
    )
    fix_md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "cross_segment_spread_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 14,
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests; bounded_files_est=19",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
        },
    )

    assert "Ultra-large PR mode" not in _primary(ask_md)
    assert "Ultra-large PR mode" not in _primary(review_md)
    assert "Ultra-large PR mode" not in _primary(fix_md)


def test_review_delta_block_stays_in_details_not_primary() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "medium",
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
            "files_block": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "review_delta_memory_active": True,
            "review_delta_prior_state_available": True,
            "review_delta_status": "prior_state_present",
            "review_delta_matching_mode": "verdict_anchor_identity",
            "review_delta_current_vs_prior_summary": "new=1; persisted=1; resolved=0",
            "review_delta_new_count": 1,
            "review_delta_persisted_count": 1,
            "review_delta_resolved_count": 0,
            "review_delta_reclassified_count": 0,
            "review_delta_new_summary": "Unchecked env var usage",
            "review_delta_persisted_summary": "Merge conflict markers present",
            "review_delta_resolved_summary": "none",
            "review_delta_uncertainty_level": "low",
        },
    )
    assert "Review delta" not in _primary(md)
    assert "### 🔄 Review delta" in md
    assert "- Prior state available: `yes`" in md
    assert "- New findings: `1` (Unchecked env var usage)" in md

def test_runtime_provenance_and_decision_cards_render_in_details_only() -> None:
    review_md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "medium",
            "confirmed_findings": ["Merge conflict markers present"],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
            "files_block": [],
            "evidence_verdicts": [
                {
                    "claim": "Merge conflict markers present",
                    "evidence_anchors": ["repobrain/github_flow.py"],
                    "confidence": "high",
                    "impact": "high",
                    "patchability": "blocked",
                    "why_now": "Merge blockers must be resolved before release.",
                    "why_not": "Patch blocked until conflicting hunks are manually reconciled.",
                    "uncertainty": "low",
                }
            ],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "runtime_provenance_status": "governed_divergent",
            "runtime_provenance_reason_code": "same_repo_open_pr_runtime_sha_differs",
            "runtime_provenance_explanation": "Runtime SHA differs from PR head SHA; provenance is explicit.",
            "runtime_provenance_runtime_sha": "workflow-sha",
            "runtime_provenance_pr_head_sha": "pr-head-sha",
            "runtime_provenance_sha_match": False,
        },
    )
    review_primary = _primary(review_md)
    assert "Runtime provenance" not in review_primary
    assert "### 🧬 Runtime provenance" in review_md
    assert "### 🧩 Decision cards" in review_md
    assert "#### Verdict 1" in review_md

    fix_md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "localized_patch_evidence_count": 0,
            "runtime_provenance_status": "aligned",
            "runtime_provenance_reason_code": "runtime_sha_matches_pr_head",
            "runtime_provenance_explanation": "Runtime SHA matches PR head SHA for this PR command run.",
            "runtime_provenance_runtime_sha": "sha-a",
            "runtime_provenance_pr_head_sha": "sha-a",
            "runtime_provenance_sha_match": True,
        },
    )
    fix_primary = _primary(fix_md)
    assert "Runtime provenance" not in fix_primary
    assert "### 🧬 Runtime provenance" in fix_md
    assert "#### Patch governance decision" in fix_md
