from __future__ import annotations

from repobrain.audit import build_audit_base, finalize_audit


def test_audit_base_contains_incremental_observability_fields() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})

    assert "incremental_retrieval_used" in audit
    assert "incremental_scope_mode" in audit
    assert "changed_files_considered" in audit
    assert "changed_regions_considered" in audit
    assert "unchanged_files_skipped" in audit
    assert "unchanged_chunks_skipped" in audit
    assert "retrieval_cache_hits" in audit
    assert "retrieval_cache_misses" in audit
    assert "incremental_fallback_reason" in audit


def test_finalize_audit_preserves_incremental_observability_values() -> None:
    audit = build_audit_base({"repo": "owner/repo", "sha": "abc", "run_id": "1"})
    audit.update(
        {
            "incremental_retrieval_used": True,
            "incremental_scope_mode": "changed_regions_first",
            "changed_files_considered": 5,
            "changed_regions_considered": 18,
            "unchanged_files_skipped": 40,
            "unchanged_chunks_skipped": 320,
            "retrieval_cache_hits": 120,
            "retrieval_cache_misses": 15,
            "incremental_fallback_reason": "none",
        }
    )
    finalized = finalize_audit(audit)

    assert finalized["incremental_retrieval_used"] is True
    assert finalized["incremental_scope_mode"] == "changed_regions_first"
    assert finalized["changed_files_considered"] == 5
    assert finalized["changed_regions_considered"] == 18
    assert finalized["unchanged_files_skipped"] == 40
    assert finalized["unchanged_chunks_skipped"] == 320
    assert finalized["retrieval_cache_hits"] == 120
    assert finalized["retrieval_cache_misses"] == 15
    assert finalized["incremental_fallback_reason"] == "none"
