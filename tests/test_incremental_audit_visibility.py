from __future__ import annotations

from pathlib import Path

import orjson

from repobrain.audit import build_audit_base, finalize_audit, write_audit
from repobrain.github_flow import (
    _build_review_markdown,
    _set_runtime_env_cfg,
    get_last_audit,
    run_github_flow,
)


class _SnapshotTestClient:
    repo = "owner/repo"
    token = "token"

    def get_pull(self, pull_number: int) -> dict[str, object]:
        return {
            "state": "open",
            "merged": False,
            "head": {"sha": "head-sha-1"},
            "base": {"sha": "base-sha-1"},
        }

    def get_pull_files(self, pull_number: int) -> list[dict[str, object]]:
        return [
            {
                "filename": "repobrain/github_flow.py",
                "status": "modified",
                "changes": 5,
                "additions": 3,
                "deletions": 2,
                "patch": "@@ -1 +1 @@\n+line",
            }
        ]


def test_audit_base_contains_incremental_observability_fields() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})

    assert "async_batch_used" in audit
    assert "batch_planner_used" in audit
    assert "batch_plan_mode" in audit
    assert "batch_count_planned" in audit
    assert "batch_primary_segments" in audit
    assert "batch_support_segments" in audit
    assert "batch_fallback_reason" in audit
    assert "async_batch_mode" in audit
    assert "async_batch_concurrency" in audit
    assert "async_batch_tasks_total" in audit
    assert "async_batch_tasks_completed" in audit
    assert "async_batch_fallback_reason" in audit
    assert "async_batch_order_preserved" in audit
    assert "async_batch_error_count" in audit
    assert "incremental_retrieval_used" in audit
    assert "incremental_scope_mode" in audit
    assert "changed_files_considered" in audit
    assert "changed_regions_considered" in audit
    assert "unchanged_files_skipped" in audit
    assert "unchanged_chunks_skipped" in audit
    assert "retrieval_cache_hits" in audit
    assert "retrieval_cache_misses" in audit
    assert "incremental_fallback_reason" in audit
    assert "retrieval_snapshot_cache_used" in audit
    assert "retrieval_snapshot_cache_hit" in audit
    assert "retrieval_snapshot_cache_key_kind" in audit
    assert "retrieval_snapshot_cache_miss_reason" in audit
    assert "retrieval_snapshot_cache_age_s" in audit
    assert "evidence_budget_used" in audit
    assert "evidence_budget_limit" in audit
    assert "evidence_budget_mode" in audit
    assert "evidence_budget_bucket_counts" in audit
    assert "evidence_budget_cutoffs" in audit
    assert "evidence_budget_overflow" in audit
    assert "evidence_budget_primary_selected" in audit
    assert "evidence_budget_support_selected" in audit
    assert "pr_segmentation_used" in audit
    assert "pr_segment_count" in audit
    assert "pr_primary_segments" in audit
    assert "pr_support_segments" in audit
    assert "pr_cross_segment" in audit
    assert "pr_segment_summary" in audit
    assert "pr_segment_file_counts" in audit
    assert "pr_segment_candidate_counts" in audit
    assert "pr_segmentation_fallback_reason" in audit
    assert "ultra_large_pr_mode_active" in audit
    assert "ultra_large_pr_mode_level" in audit
    assert "ultra_large_pr_mode_reason" in audit
    assert "ultra_large_pr_depth_strategy" in audit
    assert "ultra_large_pr_synthesis_window_cap" in audit
    assert "ultra_large_pr_primary_coverage_summary" in audit
    assert "ultra_large_pr_bounded_coverage_summary" in audit
    assert "ultra_large_pr_coverage_statement" in audit
    assert "ultra_large_pr_patch_governance_downgraded" in audit
    assert "ultra_large_pr_patch_governance_reason" in audit
    assert "review_delta_memory_active" in audit
    assert "review_delta_prior_state_available" in audit
    assert "review_delta_status" in audit
    assert "review_delta_matching_mode" in audit
    assert "review_delta_current_vs_prior_summary" in audit
    assert "review_delta_new_count" in audit
    assert "review_delta_persisted_count" in audit
    assert "review_delta_resolved_count" in audit
    assert "review_delta_reclassified_count" in audit
    assert "review_delta_uncertainty_level" in audit
    assert "runtime_provenance_status" in audit
    assert "runtime_provenance_reason_code" in audit
    assert "runtime_provenance_explanation" in audit
    assert "runtime_provenance_event_name" in audit
    assert "runtime_provenance_runtime_sha" in audit
    assert "runtime_provenance_pr_head_sha" in audit
    assert "runtime_provenance_sha_match" in audit
    assert "runtime_provenance_pr_state" in audit
    assert "runtime_provenance_same_repo_pr" in audit
    assert "llm_execution_profile_requested" in audit
    assert "llm_execution_profile_used" in audit
    assert "llm_execution_profile_reason_code" in audit
    assert "llm_execution_profile_reason_short" in audit
    assert "llm_budget_sensitivity" in audit
    assert "llm_latency_sensitivity" in audit
    assert "llm_profile_policy_outcome" in audit
    assert "llm_profile_override_applied" in audit
    assert "llm_profile_model_alignment" in audit


def test_finalize_audit_preserves_incremental_observability_values() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})
    audit.update(
        {
            "async_batch_used": True,
            "batch_planner_used": True,
            "batch_plan_mode": "segment_primary_first",
            "batch_count_planned": 5,
            "batch_primary_segments": "core_code",
            "batch_support_segments": "tests,docs",
            "batch_fallback_reason": "none",
            "async_batch_mode": "async",
            "async_batch_concurrency": 3,
            "async_batch_tasks_total": 5,
            "async_batch_tasks_completed": 5,
            "async_batch_fallback_reason": "none",
            "async_batch_order_preserved": True,
            "async_batch_error_count": 0,
            "incremental_retrieval_used": True,
            "incremental_scope_mode": "changed_regions_first",
            "changed_files_considered": 5,
            "changed_regions_considered": 18,
            "unchanged_files_skipped": 40,
            "unchanged_chunks_skipped": 320,
            "retrieval_cache_hits": 120,
            "retrieval_cache_misses": 15,
            "incremental_fallback_reason": "none",
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 4,
            "evidence_budget_used": 14,
            "evidence_budget_limit": 18,
            "evidence_budget_mode": "ask_dense_incremental",
            "evidence_budget_bucket_counts": (
                "changed_primary:8,changed_secondary:2,support_context:3,tests:1,docs:0,workflow_config:0"
            ),
            "evidence_budget_cutoffs": "dropped_docs,budget_exhausted",
            "evidence_budget_overflow": 6,
            "evidence_budget_primary_selected": 10,
            "evidence_budget_support_selected": 4,
            "pr_segmentation_used": True,
            "pr_segment_count": 3,
            "pr_primary_segments": "core_code:repobrain/github_flow",
            "pr_support_segments": "tests:tests, docs:docs",
            "pr_cross_segment": True,
            "pr_segment_summary": "primary=core_code:repobrain/github_flow; support=tests:tests, docs:docs; cross_segment=yes",
            "pr_segment_file_counts": "core_code=4; docs=1; tests=2",
            "pr_segment_candidate_counts": "core_code=3; tests=1",
            "pr_segmentation_fallback_reason": "none",
            "ultra_large_pr_mode_active": True,
            "ultra_large_pr_mode_level": "large",
            "ultra_large_pr_mode_reason": "changed_files_threshold",
            "ultra_large_pr_depth_strategy": "primary_first_capped",
            "ultra_large_pr_synthesis_window_cap": 18,
            "ultra_large_pr_primary_coverage_summary": "deep_primary=core_code:repobrain/github_flow",
            "ultra_large_pr_bounded_coverage_summary": "support=tests:tests, docs:docs; bounded_files_est=71",
            "ultra_large_pr_coverage_statement": "Bounded coverage active.",
            "ultra_large_pr_patch_governance_downgraded": True,
            "ultra_large_pr_patch_governance_reason": "scale_bounded_localization_gap",
            "review_delta_memory_active": True,
            "review_delta_prior_state_available": True,
            "review_delta_status": "prior_state_present",
            "review_delta_matching_mode": "verdict_anchor_identity",
            "review_delta_current_vs_prior_summary": "new=1; persisted=2; resolved=0; reclassified=0",
            "review_delta_new_count": 1,
            "review_delta_persisted_count": 2,
            "review_delta_resolved_count": 0,
            "review_delta_reclassified_count": 0,
            "review_delta_prior_run_id": "123",
            "review_delta_prior_head_sha": "abc123",
            "review_delta_new_summary": "Unchecked env var usage",
            "review_delta_persisted_summary": "Merge conflict markers present",
            "review_delta_resolved_summary": "none",
            "review_delta_reclassified_summary": "none",
            "review_delta_uncertainty_level": "low",
            "runtime_provenance_status": "aligned",
            "runtime_provenance_reason_code": "runtime_sha_matches_pr_head",
            "runtime_provenance_explanation": "Runtime SHA matches PR head SHA for this PR command run.",
            "runtime_provenance_event_name": "issue_comment",
            "runtime_provenance_runtime_sha": "abc123",
            "runtime_provenance_pr_head_sha": "abc123",
            "runtime_provenance_sha_match": True,
            "runtime_provenance_pr_state": "open",
            "runtime_provenance_same_repo_pr": True,
        }
    )
    finalized = finalize_audit(audit)

    assert finalized["async_batch_used"] is True
    assert finalized["batch_planner_used"] is True
    assert finalized["batch_plan_mode"] == "segment_primary_first"
    assert finalized["batch_count_planned"] == 5
    assert finalized["batch_primary_segments"] == "core_code"
    assert finalized["batch_support_segments"] == "tests,docs"
    assert finalized["batch_fallback_reason"] == "none"
    assert finalized["async_batch_mode"] == "async"
    assert finalized["async_batch_concurrency"] == 3
    assert finalized["async_batch_tasks_total"] == 5
    assert finalized["async_batch_tasks_completed"] == 5
    assert finalized["async_batch_fallback_reason"] == "none"
    assert finalized["async_batch_order_preserved"] is True
    assert finalized["async_batch_error_count"] == 0
    assert finalized["incremental_retrieval_used"] is True
    assert finalized["incremental_scope_mode"] == "changed_regions_first"
    assert finalized["changed_files_considered"] == 5
    assert finalized["changed_regions_considered"] == 18
    assert finalized["unchanged_files_skipped"] == 40
    assert finalized["unchanged_chunks_skipped"] == 320
    assert finalized["retrieval_cache_hits"] == 120
    assert finalized["retrieval_cache_misses"] == 15
    assert finalized["incremental_fallback_reason"] == "none"
    assert finalized["retrieval_snapshot_cache_used"] is True
    assert finalized["retrieval_snapshot_cache_hit"] is True
    assert finalized["retrieval_snapshot_cache_key_kind"] == "pr_number_head_sha"
    assert finalized["retrieval_snapshot_cache_miss_reason"] == "none"
    assert finalized["retrieval_snapshot_cache_age_s"] == 4
    assert finalized["evidence_budget_used"] == 14
    assert finalized["evidence_budget_limit"] == 18
    assert finalized["evidence_budget_mode"] == "ask_dense_incremental"
    assert finalized["evidence_budget_bucket_counts"].startswith("changed_primary:")
    assert finalized["evidence_budget_cutoffs"] == "dropped_docs,budget_exhausted"
    assert finalized["evidence_budget_overflow"] == 6
    assert finalized["evidence_budget_primary_selected"] == 10
    assert finalized["evidence_budget_support_selected"] == 4
    assert finalized["pr_segmentation_used"] is True
    assert finalized["pr_segment_count"] == 3
    assert finalized["pr_primary_segments"] == "core_code:repobrain/github_flow"
    assert finalized["pr_support_segments"] == "tests:tests, docs:docs"
    assert finalized["pr_cross_segment"] is True
    assert finalized["pr_segmentation_fallback_reason"] == "none"
    assert finalized["ultra_large_pr_mode_active"] is True
    assert finalized["ultra_large_pr_mode_level"] == "large"
    assert finalized["ultra_large_pr_mode_reason"] == "changed_files_threshold"
    assert finalized["ultra_large_pr_depth_strategy"] == "primary_first_capped"
    assert finalized["ultra_large_pr_synthesis_window_cap"] == 18
    assert finalized["ultra_large_pr_primary_coverage_summary"] == "deep_primary=core_code:repobrain/github_flow"
    assert finalized["ultra_large_pr_patch_governance_downgraded"] is True
    assert finalized["ultra_large_pr_patch_governance_reason"] == "scale_bounded_localization_gap"
    assert finalized["review_delta_memory_active"] is True
    assert finalized["review_delta_prior_state_available"] is True
    assert finalized["review_delta_status"] == "prior_state_present"
    assert finalized["review_delta_matching_mode"] == "verdict_anchor_identity"
    assert finalized["review_delta_new_count"] == 1
    assert finalized["review_delta_persisted_count"] == 2
    assert finalized["review_delta_resolved_count"] == 0
    assert finalized["review_delta_reclassified_count"] == 0
    assert finalized["review_delta_uncertainty_level"] == "low"
    assert finalized["runtime_provenance_status"] == "aligned"
    assert finalized["runtime_provenance_reason_code"] == "runtime_sha_matches_pr_head"
    assert finalized["runtime_provenance_runtime_sha"] == "abc123"
    assert finalized["runtime_provenance_pr_head_sha"] == "abc123"
    assert finalized["runtime_provenance_sha_match"] is True
    assert finalized["runtime_provenance_pr_state"] == "open"
    assert finalized["runtime_provenance_same_repo_pr"] is True


def test_run_github_flow_ask_audit_contains_budget_fields(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Where is provider selection implemented?",
        issue_number=None,
        tky_mode="baseline",
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert "evidence_budget_used" in audit
    assert "evidence_budget_limit" in audit
    assert "evidence_budget_mode" in audit
    assert "evidence_budget_bucket_counts" in audit
    assert "evidence_budget_cutoffs" in audit
    assert "evidence_budget_overflow" in audit
    assert "evidence_budget_primary_selected" in audit
    assert "evidence_budget_support_selected" in audit
    assert "pr_segmentation_used" in audit
    assert "pr_segment_count" in audit
    assert "pr_primary_segments" in audit
    assert "pr_support_segments" in audit
    assert "pr_cross_segment" in audit
    assert "pr_segment_summary" in audit
    assert "pr_segment_file_counts" in audit
    assert "pr_segment_candidate_counts" in audit
    assert "pr_segmentation_fallback_reason" in audit
    assert "ultra_large_pr_mode_active" in audit
    assert "ultra_large_pr_mode_level" in audit
    assert "ultra_large_pr_mode_reason" in audit
    assert "ultra_large_pr_depth_strategy" in audit
    assert "ultra_large_pr_synthesis_window_cap" in audit
    assert "ultra_large_pr_primary_coverage_summary" in audit
    assert "ultra_large_pr_bounded_coverage_summary" in audit
    assert "ultra_large_pr_coverage_statement" in audit
    assert "ultra_large_pr_patch_governance_downgraded" in audit
    assert "ultra_large_pr_patch_governance_reason" in audit
    assert "async_batch_used" in audit
    assert "batch_planner_used" in audit
    assert "batch_plan_mode" in audit
    assert "batch_count_planned" in audit
    assert "batch_primary_segments" in audit
    assert "batch_support_segments" in audit
    assert "batch_fallback_reason" in audit
    assert "async_batch_mode" in audit
    assert "async_batch_concurrency" in audit
    assert "async_batch_tasks_total" in audit
    assert "async_batch_tasks_completed" in audit
    assert "async_batch_fallback_reason" in audit
    assert "async_batch_order_preserved" in audit
    assert "async_batch_error_count" in audit
    assert "retrieval_snapshot_cache_used" in audit
    assert "retrieval_snapshot_cache_hit" in audit
    assert "retrieval_snapshot_cache_key_kind" in audit
    assert "retrieval_snapshot_cache_miss_reason" in audit
    assert "retrieval_snapshot_cache_age_s" in audit

    audit_path = tmp_path / "audit.json"
    write_audit(audit, audit_path)
    payload = orjson.loads(audit_path.read_bytes())
    assert "evidence_budget_used" in payload
    assert "evidence_budget_limit" in payload
    assert "evidence_budget_mode" in payload
    assert "evidence_budget_bucket_counts" in payload
    assert "evidence_budget_cutoffs" in payload
    assert "evidence_budget_overflow" in payload
    assert "evidence_budget_primary_selected" in payload
    assert "evidence_budget_support_selected" in payload
    assert "pr_segmentation_used" in payload
    assert "pr_segment_count" in payload
    assert "pr_primary_segments" in payload
    assert "pr_support_segments" in payload
    assert "pr_cross_segment" in payload
    assert "pr_segment_summary" in payload
    assert "pr_segment_file_counts" in payload
    assert "pr_segment_candidate_counts" in payload
    assert "pr_segmentation_fallback_reason" in payload
    assert "ultra_large_pr_mode_active" in payload
    assert "ultra_large_pr_mode_level" in payload
    assert "ultra_large_pr_mode_reason" in payload
    assert "ultra_large_pr_depth_strategy" in payload
    assert "ultra_large_pr_synthesis_window_cap" in payload
    assert "ultra_large_pr_primary_coverage_summary" in payload
    assert "ultra_large_pr_bounded_coverage_summary" in payload
    assert "ultra_large_pr_coverage_statement" in payload
    assert "ultra_large_pr_patch_governance_downgraded" in payload
    assert "ultra_large_pr_patch_governance_reason" in payload
    assert "async_batch_used" in payload
    assert "batch_planner_used" in payload
    assert "batch_plan_mode" in payload
    assert "batch_count_planned" in payload
    assert "batch_primary_segments" in payload
    assert "batch_support_segments" in payload
    assert "batch_fallback_reason" in payload
    assert "async_batch_mode" in payload
    assert "async_batch_concurrency" in payload
    assert "async_batch_tasks_total" in payload
    assert "async_batch_tasks_completed" in payload
    assert "async_batch_fallback_reason" in payload
    assert "async_batch_order_preserved" in payload
    assert "async_batch_error_count" in payload
    assert "retrieval_snapshot_cache_used" in payload
    assert "retrieval_snapshot_cache_hit" in payload
    assert "retrieval_snapshot_cache_key_kind" in payload
    assert "retrieval_snapshot_cache_miss_reason" in payload
    assert "retrieval_snapshot_cache_age_s" in payload


def test_review_and_fix_runtime_audit_include_budget_fields() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    for cmd in ("review", "fix"):
        audit: dict[str, object] = {}
        _build_review_markdown(
            repo_root=repo_root,
            cmd=cmd,
            query="",
            is_pull_request=True,
            issue_number=1,
            dry_run=True,
            client=None,
            tky_mode="baseline",
            remote_url="",
            api_key="",
            hmac_secret="",
            enable_hmac=False,
            audit=audit,
        )
        assert "evidence_budget_used" in audit
        assert "evidence_budget_limit" in audit
        assert "evidence_budget_mode" in audit
        assert "evidence_budget_bucket_counts" in audit
        assert "evidence_budget_cutoffs" in audit
        assert "evidence_budget_overflow" in audit
        assert "evidence_budget_primary_selected" in audit
        assert "evidence_budget_support_selected" in audit
        assert "pr_segmentation_used" in audit
        assert "pr_segment_count" in audit
        assert "pr_primary_segments" in audit
        assert "pr_support_segments" in audit
        assert "pr_cross_segment" in audit
        assert "pr_segment_summary" in audit
        assert "pr_segment_file_counts" in audit
        assert "pr_segment_candidate_counts" in audit
        assert "pr_segmentation_fallback_reason" in audit
        assert "ultra_large_pr_mode_active" in audit
        assert "ultra_large_pr_mode_level" in audit
        assert "ultra_large_pr_mode_reason" in audit
        assert "ultra_large_pr_depth_strategy" in audit
        assert "ultra_large_pr_synthesis_window_cap" in audit
        assert "ultra_large_pr_primary_coverage_summary" in audit
        assert "ultra_large_pr_bounded_coverage_summary" in audit
        assert "ultra_large_pr_coverage_statement" in audit
        assert "ultra_large_pr_patch_governance_downgraded" in audit
        assert "ultra_large_pr_patch_governance_reason" in audit
        assert "async_batch_used" in audit
        assert "batch_planner_used" in audit
        assert "batch_plan_mode" in audit
        assert "batch_count_planned" in audit
        assert "batch_primary_segments" in audit
        assert "batch_support_segments" in audit
        assert "batch_fallback_reason" in audit
        assert "async_batch_mode" in audit
        assert "async_batch_concurrency" in audit
        assert "async_batch_tasks_total" in audit
        assert "async_batch_tasks_completed" in audit
        assert "async_batch_fallback_reason" in audit
        assert "async_batch_order_preserved" in audit
        assert "async_batch_error_count" in audit
        assert "retrieval_snapshot_cache_used" in audit
        assert "retrieval_snapshot_cache_hit" in audit
        assert "retrieval_snapshot_cache_key_kind" in audit
        assert "retrieval_snapshot_cache_miss_reason" in audit
        assert "retrieval_snapshot_cache_age_s" in audit
        assert "runtime_provenance_status" in audit
        assert "runtime_provenance_reason_code" in audit
        assert "runtime_provenance_explanation" in audit
        assert "runtime_provenance_runtime_sha" in audit
        assert "runtime_provenance_pr_head_sha" in audit
        assert "runtime_provenance_sha_match" in audit
        assert "llm_execution_profile_requested" in audit
        assert "llm_execution_profile_used" in audit
        assert "llm_execution_profile_reason_code" in audit
        assert "llm_profile_policy_outcome" in audit


def test_review_repeated_run_shows_snapshot_miss_then_hit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    _set_runtime_env_cfg(None)  # noqa: SLF001
    first_audit: dict[str, object] = {}
    second_audit: dict[str, object] = {}
    client = _SnapshotTestClient()

    first_markdown = _build_review_markdown(
        repo_root=tmp_path,
        cmd="review",
        query="",
        is_pull_request=True,
        issue_number=1,
        dry_run=False,
        client=client,  # type: ignore[arg-type]
        tky_mode="baseline",
        remote_url="",
        api_key="",
        hmac_secret="",
        enable_hmac=False,
        github_context_seed={"is_pr": True, "pr_number": 1},
        audit=first_audit,
    )
    second_markdown = _build_review_markdown(
        repo_root=tmp_path,
        cmd="review",
        query="",
        is_pull_request=True,
        issue_number=1,
        dry_run=False,
        client=client,  # type: ignore[arg-type]
        tky_mode="baseline",
        remote_url="",
        api_key="",
        hmac_secret="",
        enable_hmac=False,
        github_context_seed={"is_pr": True, "pr_number": 1},
        audit=second_audit,
    )

    assert first_audit["retrieval_snapshot_cache_used"] is True
    assert first_audit["retrieval_snapshot_cache_hit"] is False
    assert first_audit["review_delta_memory_active"] is True
    assert first_audit["review_delta_prior_state_available"] is False
    assert first_audit["review_delta_status"] == "first_run"
    assert second_audit["retrieval_snapshot_cache_used"] is True
    assert second_audit["retrieval_snapshot_cache_hit"] is True
    assert second_audit["review_delta_memory_active"] is True
    assert second_audit["review_delta_prior_state_available"] is True
    assert second_audit["review_delta_status"] == "prior_state_present"
    assert first_audit["llm_adapter_provider"] == "github_models"
    assert first_audit["llm_adapter_provider_class"] == "github_models_chat_completions"
    assert first_audit["llm_provider"] == "github_models"
    assert second_audit["llm_adapter_provider"] == "github_models"
    assert second_audit["llm_adapter_provider_class"] == "github_models_chat_completions"
    assert second_audit["llm_provider"] == "github_models"
    assert second_audit["llm_execution_profile_requested"] in {"cheap", "balanced", "premium"}
    assert second_audit["llm_execution_profile_used"] in {"cheap", "balanced", "premium"}
    assert second_audit["runtime_provenance_status"] in {"aligned", "governed_divergent"}
    assert "runtime_provenance_reason_code" in second_audit
    _set_runtime_env_cfg(None)  # noqa: SLF001
    assert "Retrieval snapshot cache" not in first_markdown
    assert "Retrieval snapshot cache" not in second_markdown
    assert "Runtime provenance" not in second_markdown
    assert "Review delta" not in first_markdown
    assert "Review delta" not in second_markdown
    assert "<summary>Evidence and diagnostics</summary>" in first_markdown
    assert "<summary>Evidence and diagnostics</summary>" in second_markdown
