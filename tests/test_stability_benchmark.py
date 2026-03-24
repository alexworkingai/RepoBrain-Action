from __future__ import annotations

from pathlib import Path

import orjson

from repobrain.stability_benchmark import write_stability_benchmark_artifacts


def _write_audit(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))


def _snapshot_fields(status: str) -> dict[str, object]:
    normalized = str(status).strip().lower()
    if normalized == "hit":
        return {
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": True,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "none",
            "retrieval_snapshot_cache_age_s": 5,
        }
    if normalized == "miss":
        return {
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_key_kind": "pr_number_head_sha",
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
            "retrieval_snapshot_cache_age_s": 0,
        }
    return {
        "retrieval_snapshot_cache_used": False,
        "retrieval_snapshot_cache_hit": False,
        "retrieval_snapshot_cache_key_kind": "not_applicable",
        "retrieval_snapshot_cache_miss_reason": "not_applicable",
        "retrieval_snapshot_cache_age_s": 0,
    }


def test_stability_benchmark_artifacts_capture_core_contracts(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    _write_audit(
        audit_dir / "audit_001_1.json",
        {
            "command": "ask",
            "run_id": "001",
            "route_final": "FAST",
            "retrieved": 4,
            "selected": 2,
            "pr_changed_files_count": 2,
            "pr_metadata_used": True,
            "answer_grounding_mode": "hybrid",
            **_snapshot_fields("miss"),
        },
    )
    _write_audit(
        audit_dir / "audit_002_1.json",
        {
            "command": "ask",
            "run_id": "002",
            "route_final": "FAST",
            "retrieved": 4,
            "selected": 2,
            "pr_changed_files_count": 2,
            "pr_metadata_used": True,
            "answer_grounding_mode": "hybrid",
            **_snapshot_fields("hit"),
        },
    )
    _write_audit(
        audit_dir / "audit_003_1.json",
        {
            "command": "review",
            "run_id": "003",
            "route_final": "REVIEW",
            "retrieved": 8,
            "selected": 6,
            **_snapshot_fields("miss"),
        },
    )
    _write_audit(
        audit_dir / "audit_004_1.json",
        {
            "command": "review",
            "run_id": "004",
            "route_final": "REVIEW",
            "retrieved": 8,
            "selected": 6,
            **_snapshot_fields("hit"),
        },
    )
    _write_audit(
        audit_dir / "audit_005_1.json",
        {
            "command": "fix",
            "run_id": "005",
            "route_final": "REVIEW",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            **_snapshot_fields("miss"),
        },
    )

    output_json = tmp_path / "benchmarks" / "repobrain_stability_benchmark.json"
    output_md = tmp_path / "benchmarks" / "repobrain_stability_benchmark.md"
    payload = write_stability_benchmark_artifacts(
        audit_dir=audit_dir,
        output_json_path=output_json,
        output_markdown_path=output_md,
    )

    assert output_json.exists()
    assert output_md.exists()
    assert payload["scenarios"]["ask_snapshot_transition"]["status"] == "pass"
    assert payload["scenarios"]["review_snapshot_transition"]["status"] == "pass"
    assert payload["scenarios"]["ask_truth_binding_contract"]["status"] == "pass"
    assert payload["scenarios"]["review_async_subsection_contract"]["status"] == "pass"
    assert payload["scenarios"]["fix_no_patch_contract"]["status"] == "pass"
    assert payload["scenarios"]["evidence_context_label_contract"]["status"] == "pass"
    markdown = output_md.read_text(encoding="utf-8")
    assert "Ask snapshot transition (miss -> hit): **PASS**" in markdown
    assert "Review snapshot transition (miss -> hit): **PASS**" in markdown
    assert "Fix safe no_patch contract: **PASS**" in markdown


def test_stability_benchmark_marks_missing_data_when_repeated_runs_absent(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    _write_audit(
        audit_dir / "audit_001_1.json",
        {
            "command": "ask",
            "run_id": "001",
            "route_final": "FAST",
            "retrieved": 3,
            "selected": 1,
            "pr_changed_files_count": 0,
            "pr_metadata_used": False,
            "answer_grounding_mode": "retrieval",
            **_snapshot_fields("miss"),
        },
    )

    output_json = tmp_path / "benchmarks" / "repobrain_stability_benchmark.json"
    output_md = tmp_path / "benchmarks" / "repobrain_stability_benchmark.md"
    payload = write_stability_benchmark_artifacts(
        audit_dir=audit_dir,
        output_json_path=output_json,
        output_markdown_path=output_md,
    )

    assert payload["scenarios"]["ask_snapshot_transition"]["status"] == "not_enough_data"
    assert payload["scenarios"]["review_snapshot_transition"]["status"] == "not_enough_data"
    assert "NEEDS_DATA" in output_md.read_text(encoding="utf-8")


def test_stability_benchmark_distinguishes_skipped_from_needs_data_for_closed_pr_runs(
    tmp_path: Path,
) -> None:
    audit_dir = tmp_path / "audit"
    _write_audit(
        audit_dir / "audit_001_7.json",
        {
            "command": "review",
            "run_id": "001",
            "route_final": "WAIT",
            "skip_reason_code": "pr_closed_or_merged_review",
            "skip_reason_short": "Skipped: `/repobrain review` runs only on open PRs.",
            "pr_state": "closed",
            "pr_merged": True,
            **_snapshot_fields("not_applicable"),
        },
    )
    _write_audit(
        audit_dir / "audit_002_7.json",
        {
            "command": "fix",
            "run_id": "002",
            "route_final": "WAIT",
            "skip_reason_code": "pr_closed_or_merged_fix",
            "skip_reason_short": "Skipped: `/repobrain fix` runs only on open PRs with an active diff context.",
            "pr_state": "closed",
            "pr_merged": True,
            **_snapshot_fields("not_applicable"),
        },
    )

    output_json = tmp_path / "benchmarks" / "repobrain_stability_benchmark.json"
    output_md = tmp_path / "benchmarks" / "repobrain_stability_benchmark.md"
    payload = write_stability_benchmark_artifacts(
        audit_dir=audit_dir,
        output_json_path=output_json,
        output_markdown_path=output_md,
    )

    assert payload["scenarios"]["review_snapshot_transition"]["status"] == "skipped"
    assert payload["scenarios"]["review_snapshot_transition"]["reason"] == "pr_closed_or_merged_review"
    assert payload["scenarios"]["review_async_subsection_contract"]["status"] == "skipped"
    assert payload["scenarios"]["fix_no_patch_contract"]["status"] == "skipped"
    assert payload["scenarios"]["ask_snapshot_transition"]["status"] == "not_enough_data"
    assert payload["latest"]["review"]["status"] == "skipped"
    assert payload["latest"]["fix"]["status"] == "skipped"
    markdown = output_md.read_text(encoding="utf-8")
    assert "Review snapshot transition (miss -> hit): **SKIPPED** (`pr_closed_or_merged_review`)" in markdown
    assert "Review async subsection contract: **SKIPPED** (`pr_closed_or_merged_review`)" in markdown
    assert "Fix safe no_patch contract: **SKIPPED** (`pr_closed_or_merged_fix`)" in markdown
    assert "### REVIEW" in markdown
    assert "- Skipped: `pr_closed_or_merged_review`" in markdown
    assert "### FIX" in markdown
    assert "- Skipped: `pr_closed_or_merged_fix`" in markdown
