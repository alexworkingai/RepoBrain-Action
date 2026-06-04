from __future__ import annotations

import pytest

from repobrain.evidence import EvidenceItem
from repobrain.output_md import (
    enforce_comment_limit,
    render_answer_markdown,
    render_patch_markdown,
    render_review_markdown,
)

@pytest.fixture(autouse=True)
def _enable_verbose_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")


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


def test_retrieval_snapshot_cache_fields_render_in_ask_diagnostics() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 6,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- Retrieval snapshot cache used: `yes`" in md
    assert "- Retrieval snapshot cache hit: `yes`" in md
    assert "- Retrieval snapshot key kind: `pr_number_head_sha`" in md
    assert "- Retrieval snapshot age (s): `6`" in md


def test_retrieval_snapshot_cache_fields_render_in_review_diagnostics() -> None:
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
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
            "retrieval_snapshot_cache_age_s": 0,
        },
    )

    assert "- Retrieval snapshot cache used: `yes`" in md
    assert "- Retrieval snapshot miss reason: `cache_key_miss`" in md


def test_ask_final_markdown_details_include_snapshot_cache_miss_and_hit_states() -> None:
    miss_md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
            "retrieval_snapshot_cache_age_s": 0,
        },
        next_steps="n/a",
        command="ask",
    )
    hit_md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 9,
        },
        next_steps="n/a",
        command="ask",
    )

    miss_primary = miss_md.split("<details>", 1)[0]
    hit_primary = hit_md.split("<details>", 1)[0]
    assert "### 🗃️ Retrieval snapshot cache" not in miss_primary
    assert "### 🗃️ Retrieval snapshot cache" not in hit_primary

    miss_details = miss_md.split("<details>", 1)[1]
    hit_details = hit_md.split("<details>", 1)[1]
    assert "### 🗃️ Retrieval snapshot cache" in miss_details
    assert "- Status: `miss`" in miss_details
    assert "- Reason: `cache_key_miss`" in miss_details
    assert "### 🗃️ Retrieval snapshot cache" in hit_details
    assert "- Status: `hit`" in hit_details
    assert "- Snapshot age (s): `9`" in hit_details


def test_review_final_markdown_details_include_snapshot_cache_status() -> None:
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
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 3,
        },
    )

    details_md = md.split("<details>", 1)[1]
    assert "### 🗃️ Retrieval snapshot cache" in details_md
    assert "- Status: `hit`" in details_md
    assert "- Key kind: `pr_number_head_sha`" in details_md


def test_ask_truncated_output_keeps_snapshot_cache_miss_then_hit_visible() -> None:
    miss_md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
            "retrieval_snapshot_cache_age_s": 0,
        },
        next_steps="n/a",
        command="ask",
    )
    hit_md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 7,
        },
        next_steps="n/a",
        command="ask",
    )

    miss_truncated, miss_cut = enforce_comment_limit(miss_md, max_bytes=220)
    hit_truncated, hit_cut = enforce_comment_limit(hit_md, max_bytes=220)

    assert miss_cut is True
    assert hit_cut is True
    assert "Retrieval snapshot cache" not in miss_truncated
    assert "Retrieval snapshot cache" not in hit_truncated
    assert "### 🤖 LLM" in miss_truncated
    assert "### 🛡️ Runtime and safety" in hit_truncated


def test_review_truncated_output_keeps_snapshot_cache_miss_then_hit_visible() -> None:
    review = {
        "summary_text": "Review complete.",
        "risk_level": "low",
        "files_block": [],
        "confirmed_findings": [],
        "possible_signals": [],
        "informational_notes": [],
        "recommendations": [],
    }
    miss_md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pass_count": 1,
            "review_batch_mode": False,
            "review_batch_count": 1,
            "batch_planner_used": False,
            "batch_plan_mode": "not_applied",
            "batch_count_planned": 1,
            "batch_primary_segments": "none",
            "batch_support_segments": "none",
            "batch_fallback_reason": "not_applicable",
            "async_batch_used": False,
            "async_batch_mode": "sequential_disabled",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": 1,
            "async_batch_tasks_completed": 1,
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
            "async_batch_fallback_reason": "disabled",
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
            "retrieval_snapshot_cache_age_s": 0,
        },
    )
    hit_md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pass_count": 1,
            "review_batch_mode": False,
            "review_batch_count": 1,
            "batch_planner_used": False,
            "batch_plan_mode": "not_applied",
            "batch_count_planned": 1,
            "batch_primary_segments": "none",
            "batch_support_segments": "none",
            "batch_fallback_reason": "not_applicable",
            "async_batch_used": False,
            "async_batch_mode": "sequential_disabled",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": 1,
            "async_batch_tasks_completed": 1,
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
            "async_batch_fallback_reason": "disabled",
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 5,
        },
    )

    miss_truncated, miss_cut = enforce_comment_limit(miss_md, max_bytes=260)
    hit_truncated, hit_cut = enforce_comment_limit(hit_md, max_bytes=260)

    assert miss_cut is True
    assert hit_cut is True
    assert "Retrieval snapshot cache" not in miss_truncated
    assert "Retrieval snapshot cache" not in hit_truncated
    assert "### 🤖 LLM" in miss_truncated
    assert "### 🛡️ Runtime and safety" in hit_truncated


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


def test_async_batch_fields_render_in_dedicated_subsection_without_diagnostics_duplication() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "DEEP",
            "pass_count": 1,
            "async_batch_used": True,
            "async_batch_mode": "async",
            "async_batch_concurrency": 2,
            "async_batch_tasks_total": 3,
            "async_batch_tasks_completed": 3,
            "async_batch_fallback_reason": "none",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        },
    )

    assert "### Async batch orchestration" in md
    assert "- Used: `yes`" in md
    assert "- Mode: `async`" in md
    assert "- Concurrency: `2`" in md
    assert "- Tasks: `3/3`" in md
    assert "- Order preserved: `yes`" in md
    assert "- Async batch used: `yes`" not in md
    assert "- Async batch mode: `async`" not in md


def test_review_details_include_async_batch_subsection() -> None:
    review = {
        "summary_text": "Review complete.",
        "risk_level": "medium",
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
            "route_final": "DEEP",
            "llm_batch_used": True,
            "review_batch_mode": True,
            "review_batch_count": 4,
            "batch_planner_used": True,
            "batch_plan_mode": "segment_primary_first",
            "batch_count_planned": 4,
            "batch_primary_segments": "core_code",
            "batch_support_segments": "tests,docs",
            "batch_fallback_reason": "none",
            "async_batch_used": True,
            "async_batch_mode": "async",
            "async_batch_concurrency": 2,
            "async_batch_tasks_total": 4,
            "async_batch_tasks_completed": 4,
            "async_batch_fallback_reason": "none",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        },
    )

    assert "### Async batch orchestration" in md
    assert "- Planner used: `yes`" in md
    assert "- Plan mode: `segment_primary_first`" in md
    assert "- Planned batches: `4`" in md
    assert "- Used: `yes`" in md
    assert "- Mode: `async`" in md
    assert "- Tasks: `4/4`" in md


def test_review_fix_async_subsection_stays_visible_with_review_batch_only_signals() -> None:
    review_md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "DEEP",
            "review_batch_mode": True,
            "review_batch_count": 2,
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
            "patch_target_files_total": 1,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "review_batch_mode": True,
            "review_batch_count": 2,
        },
    )

    for md in (review_md, fix_md):
        assert "### Async batch orchestration" in md
        assert md.count("- Review batch mode: `yes`") == 1
        assert md.count("- Review batch count: `2`") == 1
        assert "- Async batch used: `yes`" not in md
        assert "- Batch planner used: `yes`" not in md


def test_review_fix_async_subsection_stays_visible_with_low_default_batch_values() -> None:
    review_md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "DEEP",
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
            "patch_target_files_total": 1,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
        },
    )

    for md in (review_md, fix_md):
        assert "### Async batch orchestration" in md
        assert "- Used: `no`" in md
        assert "- Mode: `sequential`" in md
        assert "- Tasks: `0/0`" in md
        assert "- Async batch used: `no`" not in md
        assert "- Batch planner used: `no`" not in md


def test_final_review_fix_markdown_keeps_stable_async_subsection_without_diagnostics_duplication() -> None:
    review_md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"command": "review", "route_final": "DEEP"},
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
            "patch_target_files_total": 1,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
        },
    )
    ask_md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={"command": "ask", "route_final": "FAST"},
        next_steps="n/a",
        command="ask",
    )

    for md in (review_md, fix_md):
        detail_start = md.index("<summary>Evidence and diagnostics</summary>")
        detail_end = md.index("</details>", detail_start)
        details_md = md[detail_start:detail_end]
        assert "### Async batch orchestration" in details_md
        assert details_md.count("### Async batch orchestration") == 1
        assert details_md.index("### Async batch orchestration") < details_md.index("### 🧾 Runtime diagnostics")
        assert "- Async batch used:" not in details_md
        assert "- Async batch mode:" not in details_md
        assert "- Batch planner used:" not in details_md
        if "### Secondary diagnostics" in details_md and "### 🧾 Audit anchors" in details_md:
            secondary_start = details_md.index("### Secondary diagnostics")
            anchors_start = details_md.index("### 🧾 Audit anchors", secondary_start)
            secondary_md = details_md[secondary_start:anchors_start]
            assert "- Async batch used:" not in secondary_md
            assert "- Async batch mode:" not in secondary_md
            assert "- Batch planner used:" not in secondary_md
            assert "- Review batch mode:" not in secondary_md
            assert "- Review batch count:" not in secondary_md

    assert "### Async batch orchestration" not in ask_md


def test_fix_details_include_async_batch_subsection_for_sequential_fallback() -> None:
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
            "patch_grounding_mode": "pr_metadata",
            "llm_batch_used": True,
            "batch_planner_used": False,
            "batch_plan_mode": "fallback_original_order",
            "batch_count_planned": 3,
            "batch_primary_segments": "none",
            "batch_support_segments": "none",
            "batch_fallback_reason": "missing_segmentation_map",
            "async_batch_used": False,
            "async_batch_mode": "sequential_disabled",
            "async_batch_concurrency": 1,
            "async_batch_tasks_total": 3,
            "async_batch_tasks_completed": 3,
            "async_batch_fallback_reason": "disabled",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        },
    )

    assert "### Async batch orchestration" in md
    assert "- Planner used: `no`" in md
    assert "- Plan mode: `fallback_original_order`" in md
    assert "- Planner fallback reason: `missing_segmentation_map`" in md
    assert "- Used: `no`" in md
    assert "- Mode: `sequential_disabled`" in md
    assert "- Tasks: `3/3`" in md


def test_review_fix_generic_diagnostics_do_not_repeat_meaningful_async_rows() -> None:
    review_md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "DEEP",
            "llm_batch_used": True,
            "batch_planner_used": True,
            "batch_plan_mode": "segment_primary_first",
            "batch_count_planned": 4,
            "async_batch_used": True,
            "async_batch_mode": "async",
            "async_batch_concurrency": 2,
            "async_batch_tasks_total": 4,
            "async_batch_tasks_completed": 4,
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
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
            "llm_batch_used": True,
            "review_batch_mode": True,
            "review_batch_count": 2,
            "batch_planner_used": True,
            "batch_plan_mode": "segment_primary_first",
            "batch_count_planned": 2,
            "async_batch_used": True,
            "async_batch_mode": "async",
            "async_batch_concurrency": 2,
            "async_batch_tasks_total": 2,
            "async_batch_tasks_completed": 2,
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
        },
    )
    assert "### Async batch orchestration" in review_md
    assert "- Async batch used: `yes`" not in review_md
    assert "- Async batch mode: `async`" not in review_md
    assert "- Batch planner used: `yes`" not in review_md
    assert "- Review batch mode: `yes`" not in review_md
    assert "- Review batch count:" not in review_md

    assert "### Async batch orchestration" in fix_md
    assert "- Async batch used: `yes`" not in fix_md
    assert "- Async batch mode: `async`" not in fix_md
    assert "- Batch planner used: `yes`" not in fix_md
    assert fix_md.count("- Review batch mode: `yes`") == 1
    assert fix_md.count("- Review batch count: `2`") == 1


def test_ask_evidence_lines_include_context_role_labels_without_changing_truth_binding() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[
            EvidenceItem(file_path="docs/guide.md", line_start=1, line_end=5, score=0.9),
            EvidenceItem(file_path="repobrain/ask.py", line_start=10, line_end=20, score=0.6),
            EvidenceItem(file_path="tests/test_pr_review.py", line_start=3, line_end=9, score=0.5),
        ],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "selected": 3,
            "touched_files": ["docs/guide.md"],
            "evidence_budget_bucket_counts": (
                "changed_primary:1,changed_secondary:0,support_context:1,tests:1,docs:0,workflow_config:0"
            ),
        },
        next_steps="n/a",
        command="ask",
    )

    assert "- [Changed in PR]" in md
    assert "- [Support context]" in md
    assert "- [Test context]" in md
    assert "### 🏷️ Evidence context" not in md
    assert "### 🔎 Verification" not in md
    assert "### Async batch orchestration" not in md


def test_review_touched_files_show_changed_vs_support_context_labels() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "low",
            "files_block": [
                "- `repobrain/github_flow.py` (+4 -2)",
                "- `tests/test_pr_review.py` (+12 -0)",
                "- `repobrain/ask.py` (+3 -1)",
            ],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "selected": 3,
            "touched_files": ["repobrain/github_flow.py", "tests/test_pr_review.py"],
            "evidence_budget_bucket_counts": (
                "changed_primary:2,changed_secondary:0,support_context:1,tests:1,docs:0,workflow_config:0"
            ),
        },
    )

    assert "- [Changed in PR] `repobrain/github_flow.py` (+4 -2)" in md
    assert "- [Changed in PR] `tests/test_pr_review.py` (+12 -0)" in md
    assert "- [Support context] `repobrain/ask.py` (+3 -1)" in md
    assert "### Async batch orchestration" in md


def test_fix_details_include_evidence_context_summary_labels() -> None:
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
            "patch_grounding_mode": "pr_metadata",
            "touched_files": ["repobrain/github_flow.py", "repobrain/output_md.py"],
            "selected": 2,
            "evidence_budget_bucket_counts": (
                "changed_primary:2,changed_secondary:0,support_context:1,tests:0,docs:0,workflow_config:1"
            ),
        },
    )

    assert "### 🏷️ Evidence context" in md
    assert "- Changed in PR: `2`" in md
    assert "- Support context: `1`" in md
    assert "- Reference: `1`" in md
    assert "### Async batch orchestration" in md


def test_ask_ultra_large_pr_mode_renders_in_details_only_when_active() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "changed_files_threshold,cross_segment_spread_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 10,
            "evidence_budget_mode": "ultra_large_ask_capped",
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain/github_flow",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests, docs:docs; bounded_files_est=67",
            "ultra_large_pr_coverage_statement": (
                "Bounded coverage active: deep focus on primary segments; secondary/support treated as bounded context."
            ),
        },
        next_steps="n/a",
        command="ask",
    )

    primary = md.split("<details>", 1)[0]
    details = md.split("<details>", 1)[1]
    assert "### 🧱 Ultra-large PR mode" not in primary
    assert "### 🧱 Ultra-large PR mode" in details
    assert "- Status: `active`" in details
    assert "- Evidence budget mode: `ultra_large_ask_capped`" in details


def test_review_ultra_large_pr_mode_renders_coverage_block_when_active() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review complete.",
            "risk_level": "medium",
            "files_block": [],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "extreme",
            "ultra_large_pr_mode_reason": "changed_files_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_extreme_cap",
            "ultra_large_pr_synthesis_window_cap": 14,
            "evidence_budget_mode": "ultra_large_review_capped",
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain/github_flow",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests; bounded_files_est=122",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
        },
    )

    details = md.split("<details>", 1)[1]
    assert "### 🧱 Ultra-large PR mode" in details
    assert "- Level: `extreme`" in details
    assert "- Synthesis window cap: `14`" in details


def test_fix_ultra_large_pr_mode_renders_scale_governance_downgrade_reason() -> None:
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
            "patch_target_files_total": 120,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "changed_regions_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 14,
            "evidence_budget_mode": "ultra_large_fix_capped",
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain/github_flow",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests; bounded_files_est=106",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
            "ultra_large_pr_patch_governance_downgraded": True,
            "ultra_large_pr_patch_governance_reason": "scale_bounded_localization_gap",
        },
    )

    details = md.split("<details>", 1)[1]
    assert "### 🧱 Ultra-large PR mode" in details
    assert "- Patch governance downgraded: `yes`" in details
    assert "- Patch governance reason: `scale_bounded_localization_gap`" in details
