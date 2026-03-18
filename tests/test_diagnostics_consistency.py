from __future__ import annotations

from repobrain.output_md import render_answer_markdown, render_patch_markdown, render_review_markdown


def test_retained_preferred_model_does_not_render_downgrade_budget_action() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_model_used": "openai/gpt-4.1",
            "llm_preferred_model_id": "openai/gpt-4.1",
            "llm_final_synthesis_model_id": "openai/gpt-4.1",
            "llm_retained_preferred_model_reason": "retained preferred model: complex ask/explain in estimate mode",
            "llm_budget_action": "model_downgraded_to_mini_estimate_mode",
        },
        next_steps="Validate",
        command="ask",
    )

    assert "AI Budget action: budget policy evaluated; preferred model retained" in md
    assert "model_downgraded_to_mini_estimate_mode" not in md


def test_fix_pr_context_diagnostics_keep_pr_metadata_counts_consistent() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "pr_changed_files_count": 9,
            "pr_metadata_used": True,
            "patch_target_files_total": 9,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": (
                "No patch generated: no sufficiently localized, evidence-backed patch target was found."
            ),
        },
    )

    assert "- PR changed files: `9`" in md
    assert "- PR metadata used: `yes`" in md


def test_patch_targeting_mode_none_is_meaningful_in_diagnostics() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "pr_changed_files_count": 4,
            "pr_metadata_used": True,
            "patch_target_files_total": 4,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
        },
    )

    assert "- Patch targeting mode: `none`" in md
    assert "undefined: Localized patch-target selection strategy outcome." not in md


def test_ask_diagnostics_do_not_include_review_only_rows() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "execution_mode": "retrieval_only",
            "command": "ask",
            "llm_used": False,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "Review confirmed findings" not in md
    assert "Review possible signals" not in md


def test_fix_diagnostics_do_not_include_review_only_rows() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence_backed_patch_target",
            "patch_grounding_mode": "pr_metadata",
        },
    )

    assert "Review confirmed findings" not in md
    assert "Review possible signals" not in md


def test_sprint38_observability_fields_render_for_fix() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_confirmed_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "hybrid_rerank_used": False,
            "retrieval_ranking_mode": "lexical",
            "evidence_filtered_count": 2,
            "evidence_filter_reason_codes": "docs_noise,duplicate_region",
            "signal_calibration_used": True,
            "patch_guard_triggered": True,
            "tldr_compressed": False,
        },
    )

    assert "- Hybrid rerank used: `no`" in md
    assert "- Retrieval ranking mode: `lexical`" in md
    assert "- Evidence filtered: `2`" in md
    assert "- Evidence filter reason codes: `docs_noise,duplicate_region`" in md
    assert "- Signal calibration used: `yes`" in md
    assert "- Patch guard triggered: `yes`" in md
    assert "- TL;DR compressed: `no`" in md


def test_check_publication_diagnostics_fields_render() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "check_run_attempted": False,
            "check_run_published": False,
            "check_run_status_code": "deferred",
            "check_run_failure_class": "deferred",
            "check_run_token_source": "workflow_run_github_token",
            "check_run_event_name": "issue_comment",
            "check_run_required_permissions_header": "n/a",
            "check_run_skip_reason": "deferred_workflow_publisher",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- Check-run attempted: `no`" in md
    assert "- Check-run status: `deferred`" in md
    assert "- Check-run token source: `workflow_run_github_token`" in md
    assert "- Check-run failure class: `deferred`" in md


def test_incremental_retrieval_diagnostics_fields_render() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "incremental_retrieval_used": True,
            "incremental_scope_mode": "changed_files_first",
            "changed_files_considered": 3,
            "changed_regions_considered": 7,
            "unchanged_files_skipped": 12,
            "unchanged_chunks_skipped": 64,
            "retrieval_cache_hits": 24,
            "retrieval_cache_misses": 3,
            "incremental_fallback_reason": "none",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- Incremental retrieval used: `yes`" in md
    assert "- Incremental scope mode: `changed_files_first`" in md
    assert "- Changed files considered: `3`" in md
    assert "- Unchanged chunks skipped: `64`" in md
    assert "- Retrieval cache hits: `24`" in md


def test_incremental_retrieval_fields_render_in_review_diagnostics() -> None:
    review = {
        "summary_text": "Review complete.",
        "risk_level": "low",
        "files_block": [],
        "confirmed_findings": [],
        "possible_signals": [],
        "informational_notes": [],
        "recommendations": [],
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pass_count": 1,
            "incremental_retrieval_used": False,
            "incremental_scope_mode": "not_applicable",
            "changed_files_considered": 0,
            "changed_regions_considered": 0,
            "unchanged_files_skipped": 0,
            "unchanged_chunks_skipped": 0,
            "retrieval_cache_hits": 0,
            "retrieval_cache_misses": 0,
            "incremental_fallback_reason": "not_applicable",
        },
    )

    assert "- Incremental retrieval used: `no`" in md
    assert "- Incremental scope mode: `not_applicable`" in md
    assert "- Retrieval cache misses: `0`" in md


def test_incremental_retrieval_fields_render_in_fix_diagnostics() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "incremental_retrieval_used": False,
            "incremental_scope_mode": "not_applicable",
            "changed_files_considered": 0,
            "changed_regions_considered": 0,
            "unchanged_files_skipped": 0,
            "unchanged_chunks_skipped": 0,
            "retrieval_cache_hits": 0,
            "retrieval_cache_misses": 0,
            "incremental_fallback_reason": "not_applicable",
        },
    )

    assert "- Incremental retrieval used: `no`" in md
    assert "- Incremental scope mode: `not_applicable`" in md
    assert "- Incremental fallback reason: `not_applicable`" in md


def test_evidence_budget_fields_render_in_diagnostics() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "pass_count": 2,
            "evidence_budget_used": 11,
            "evidence_budget_limit": 18,
            "evidence_budget_mode": "ask_dense_incremental",
            "evidence_budget_bucket_counts": (
                "changed_primary:6,changed_secondary:2,support_context:2,tests:1,docs:0,workflow_config:0"
            ),
            "evidence_budget_cutoffs": "dropped_docs,budget_exhausted",
            "evidence_budget_overflow": 9,
            "evidence_budget_primary_selected": 8,
            "evidence_budget_support_selected": 3,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- Evidence budget used: `11`" in md
    assert "- Evidence budget limit: `18`" in md
    assert "- Evidence budget mode: `ask_dense_incremental`" in md
    assert (
        "- Evidence budget bucket counts: "
        "`changed_primary:6,changed_secondary:2,support_context:2,tests:1,docs:0,workflow_config:0`"
    ) in md
    assert "- Evidence budget cutoffs: `dropped_docs,budget_exhausted`" in md
    assert "- Evidence budget overflow: `9`" in md


def test_evidence_budget_fields_are_not_classified_as_undefined() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "evidence_budget_used": 0,
            "evidence_budget_limit": 0,
            "evidence_budget_mode": "not_applied",
            "evidence_budget_bucket_counts": (
                "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
            ),
            "evidence_budget_cutoffs": "no_cutoff",
            "evidence_budget_overflow": 0,
            "evidence_budget_primary_selected": 0,
            "evidence_budget_support_selected": 0,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- Evidence budget mode: `not_applied`" in md
    assert "undefined: Adaptive evidence-budget profile applied for this run." not in md


def test_evidence_budget_fields_render_in_review_diagnostics() -> None:
    review = {
        "summary_text": "Review complete.",
        "risk_level": "low",
        "files_block": [],
        "confirmed_findings": [],
        "possible_signals": [],
        "informational_notes": [],
        "recommendations": [],
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pass_count": 1,
            "evidence_budget_used": 16,
            "evidence_budget_limit": 24,
            "evidence_budget_mode": "review_risk_weighted_incremental",
            "evidence_budget_bucket_counts": (
                "changed_primary:8,changed_secondary:3,support_context:2,tests:1,docs:1,workflow_config:1"
            ),
            "evidence_budget_cutoffs": "dropped_docs,budget_exhausted",
            "evidence_budget_overflow": 12,
            "evidence_budget_primary_selected": 11,
            "evidence_budget_support_selected": 5,
        },
    )

    assert "- Evidence budget used: `16`" in md
    assert "- Evidence budget mode: `review_risk_weighted_incremental`" in md
    assert "- Evidence budget cutoffs: `dropped_docs,budget_exhausted`" in md
    assert "undefined: Adaptive evidence-budget profile applied for this run." not in md


def test_evidence_budget_fields_render_in_fix_diagnostics() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "evidence_budget_used": 9,
            "evidence_budget_limit": 12,
            "evidence_budget_mode": "fix_localized_strict_incremental",
            "evidence_budget_bucket_counts": (
                "changed_primary:6,changed_secondary:1,support_context:1,tests:0,docs:0,workflow_config:1"
            ),
            "evidence_budget_cutoffs": "budget_exhausted",
            "evidence_budget_overflow": 4,
            "evidence_budget_primary_selected": 7,
            "evidence_budget_support_selected": 2,
        },
    )

    assert "- Evidence budget used: `9`" in md
    assert "- Evidence budget limit: `12`" in md
    assert "- Evidence budget mode: `fix_localized_strict_incremental`" in md
    assert "- Evidence budget overflow: `4`" in md


def test_pr_segmentation_fields_render_in_ask_diagnostics() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "pass_count": 2,
            "pr_segmentation_used": True,
            "pr_segment_count": 3,
            "pr_primary_segments": "core_code:repobrain/github_flow",
            "pr_support_segments": "tests:tests, docs:docs",
            "pr_cross_segment": True,
            "pr_segment_summary": "primary=core_code:repobrain/github_flow; support=tests:tests, docs:docs; cross_segment=yes",
            "pr_segment_file_counts": "core_code=4; docs=1; tests=2",
            "pr_segment_candidate_counts": "core_code=3; tests=1",
            "pr_segmentation_fallback_reason": "none",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- PR segmentation used: `yes`" in md
    assert "- PR segment count: `3`" in md
    assert "- PR primary segments: `core_code:repobrain/github_flow`" in md
    assert "- PR cross-segment: `yes`" in md
    assert "- PR segment file counts: `core_code=4; docs=1; tests=2`" in md


def test_pr_segmentation_fields_render_in_review_diagnostics() -> None:
    review = {
        "summary_text": "Review complete.",
        "risk_level": "low",
        "files_block": [],
        "confirmed_findings": [],
        "possible_signals": [],
        "informational_notes": [],
        "recommendations": [],
    }
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pass_count": 1,
            "pr_segmentation_used": True,
            "pr_segment_count": 2,
            "pr_primary_segments": "core_code:repobrain/github_flow",
            "pr_support_segments": "workflow_ci:.github/workflows",
            "pr_cross_segment": True,
            "pr_segment_summary": "primary=core_code:repobrain/github_flow; support=workflow_ci:.github/workflows; cross_segment=yes",
            "pr_segment_file_counts": "core_code=2; workflow_ci=1",
            "pr_segment_candidate_counts": "core_code=2; workflow_ci=1",
            "pr_segmentation_fallback_reason": "none",
        },
    )

    assert "- PR segmentation used: `yes`" in md
    assert "- PR segment count: `2`" in md
    assert "- PR support segments: `workflow_ci:.github/workflows`" in md


def test_pr_segmentation_fields_render_in_fix_diagnostics() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "pass_count": 1,
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "pr_segmentation_used": True,
            "pr_segment_count": 2,
            "pr_primary_segments": "core_code:repobrain/github_flow",
            "pr_support_segments": "tests:tests",
            "pr_cross_segment": False,
            "pr_segment_summary": "primary=core_code:repobrain/github_flow; support=tests:tests; cross_segment=no",
            "pr_segment_file_counts": "core_code=2; tests=1",
            "pr_segment_candidate_counts": "core_code=1",
            "pr_segmentation_fallback_reason": "none",
        },
    )

    assert "- PR segmentation used: `yes`" in md
    assert "- PR segment summary: `primary=core_code:repobrain/github_flow; support=tests:tests; cross_segment=no`" in md
