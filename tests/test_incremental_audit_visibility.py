from __future__ import annotations

from pathlib import Path

import orjson

from repobrain.audit import build_audit_base, finalize_audit, write_audit
from repobrain.github_flow import _build_review_markdown, get_last_audit, run_github_flow


def test_audit_base_contains_incremental_observability_fields() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})

    assert "async_batch_used" in audit
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


def test_finalize_audit_preserves_incremental_observability_values() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})
    audit.update(
        {
            "async_batch_used": True,
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
        }
    )
    finalized = finalize_audit(audit)

    assert finalized["async_batch_used"] is True
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
    assert "async_batch_used" in audit
    assert "async_batch_mode" in audit
    assert "async_batch_concurrency" in audit
    assert "async_batch_tasks_total" in audit
    assert "async_batch_tasks_completed" in audit
    assert "async_batch_fallback_reason" in audit
    assert "async_batch_order_preserved" in audit
    assert "async_batch_error_count" in audit

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
    assert "async_batch_used" in payload
    assert "async_batch_mode" in payload
    assert "async_batch_concurrency" in payload
    assert "async_batch_tasks_total" in payload
    assert "async_batch_tasks_completed" in payload
    assert "async_batch_fallback_reason" in payload
    assert "async_batch_order_preserved" in payload
    assert "async_batch_error_count" in payload


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
        assert "async_batch_used" in audit
        assert "async_batch_mode" in audit
        assert "async_batch_concurrency" in audit
        assert "async_batch_tasks_total" in audit
        assert "async_batch_tasks_completed" in audit
        assert "async_batch_fallback_reason" in audit
        assert "async_batch_order_preserved" in audit
        assert "async_batch_error_count" in audit
