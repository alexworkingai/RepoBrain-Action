from __future__ import annotations

from pathlib import Path

import orjson

from repobrain.tkya_evidence_pack import write_tkya_evidence_pack_artifacts


def _sample_audit() -> dict[str, object]:
    return {
        "run_id": "123",
        "repo": "owner/repo",
        "pr_number": 55,
        "issue_number": 55,
        "sha": "abc123",
        "command": "review",
        "task_type": "review",
        "route_final": "REVIEW",
        "execution_mode": "retrieval_plus_llm",
        "llm_intent": "review",
        "llm_decision_reason_code": "REVIEW_SYNTHESIS_REQUIRED",
        "llm_decision_reason_short": "LLM used: review synthesis required.",
        "llm_execution_profile_requested": "balanced",
        "llm_execution_profile_used": "balanced",
        "llm_execution_profile_reason_code": "profile_applied",
        "llm_execution_profile_reason_short": "Execution profile applied from configured request.",
        "llm_budget_sensitivity": "normal",
        "llm_latency_sensitivity": "low",
        "llm_profile_policy_outcome": "profile_applied",
        "llm_profile_override_applied": False,
        "llm_profile_model_alignment": "balanced_high_tier_selected",
        "tkya_backend": "v5",
        "tky_engine": "legacy_runtime_removed",
        "selected": 5,
        "retrieved": 21,
        "tky_selected_chunk_ids_count": 5,
        "topology_mode": "analytics_graph",
        "topology_complexity": "high",
        "topology_metric_count": 12,
        "huk_score": 0.73,
        "huk_bars_hash": "abcxyz",
        "zigzag_turning_points": 4,
        "zigzag_volatility": 0.21,
        "zigzag_trend": "up",
        "morse_risk": "medium",
        "morse_verify_required": True,
        "morse_confidence": 0.82,
        "morse_todo_count": 2,
        "morse_conflict_markers": True,
        "morse_secret_signal": False,
        "morse_workflow_risky": True,
        "morse_test_disable_signal": False,
        "morse_signals": ["workflow_risky_pattern", "conflict_markers"],
        "verification_overall": "WARN",
        "verification_pass_count": 2,
        "verification_fail_count": 1,
        "verification_pending_count": 0,
        "verification_not_run_count": 1,
        "verification_profile": "main",
        "verification_branch": "main",
        "verification_completeness": 0.5,
        "verification_gate_decision": "WARN",
        "verification_gate_reason": "required_checks_not_run",
        "verification_required_checks": ["security scan", "integration-tests"],
        "trace_schema_version": "1.1",
        "trace_schema_policy": "1.x",
        "trace_schema_compatible": True,
        "trace_query_hash": "q123",
        "trace_selected_hash": "s123",
        "trace_ranking_hash": "r123",
        "trace_github_scope_hash": "g123",
        "trace_zigzag_hash": "z123",
        "trace_morse_hash": "m123",
        "trace_inputs_hash": "i123",
        "evidence_budget_mode": "bounded",
        "evidence_budget_used": 18,
        "evidence_budget_limit": 20,
        "evidence_budget_overflow": 2,
        "ultra_large_pr_mode_active": True,
        "ultra_large_pr_mode_level": "ultra",
        "ultra_large_pr_mode_reason": "cross_segment_pressure",
        "ultra_large_pr_coverage_statement": "Bounded coverage active.",
        "review_delta_status": "prior_state_present",
        "review_delta_prior_state_available": True,
        "runtime_provenance_status": "aligned",
        "runtime_provenance_reason_code": "runtime_sha_matches_pr_head",
        "runtime_provenance_explanation": "Runtime SHA matches PR head SHA for this PR command run.",
        "runtime_provenance_event_name": "issue_comment",
        "runtime_provenance_runtime_sha": "abc123",
        "runtime_provenance_pr_head_sha": "abc123",
        "runtime_provenance_sha_match": True,
        "runtime_provenance_pr_state": "open",
        "runtime_provenance_same_repo_pr": True,
        "security_scope": "repo_analysis",
        "security_outcome": "allow",
        "security_reason_code": "allow_repo_analysis",
        "security_reason_short": "Repository analysis allowed.",
        "llm_used": True,
        "llm_provider": "github_models",
        "llm_policy_allowed": True,
        "llm_request_mode": "normal",
        "llm_primary_model_id": "openai/gpt-4.1",
        "llm_preferred_model_id": "openai/gpt-4.1",
        "llm_effective_model_id": "openai/gpt-4.1-mini",
        "llm_model_used": "openai/gpt-4.1",
        "llm_final_synthesis_model_id": "openai/gpt-4.1",
        "llm_intermediate_downgrade_occurred": True,
        "llm_intermediate_downgrade_reason": "quota_pressure",
        "llm_provider_http_status": 200,
        "llm_provider_error_type": "n/a",
        "llm_tokens_total": 1400,
    }


def test_write_tkya_evidence_pack_artifacts_internal_and_public_contract(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    (repo_root / "src").mkdir()
    (repo_root / "src" / "a.py").write_text("print('ok')\n", encoding="utf-8")
    (repo_root / "src" / "b.py").write_text("x = 1\n", encoding="utf-8")

    result = write_tkya_evidence_pack_artifacts(repo_root=repo_root, audit=_sample_audit())

    internal_path = repo_root / "artifacts" / "evidence_pack" / "repobrain_tkya_evidence_pack_internal.json"
    public_path = repo_root / "artifacts" / "evidence_pack" / "repobrain_tkya_evidence_pack_public_safe.json"
    summary_path = repo_root / "artifacts" / "evidence_pack" / "repobrain_tkya_evidence_pack.md"

    assert Path(str(result["internal_path"])) == internal_path
    assert Path(str(result["public_safe_path"])) == public_path
    assert Path(str(result["summary_path"])) == summary_path
    assert internal_path.exists()
    assert public_path.exists()
    assert summary_path.exists()

    internal = orjson.loads(internal_path.read_bytes())
    public = orjson.loads(public_path.read_bytes())
    summary = summary_path.read_text(encoding="utf-8")

    assert internal["schema_version"] == "tkya_evidence_pack_v1"
    assert internal["artifact_kind"] == "internal"
    assert public["artifact_kind"] == "public_safe"
    assert internal["execution_summary"]["route_final"] == "REVIEW"
    assert internal["execution_summary"]["execution_profile_used"] == "balanced"
    assert internal["execution_summary"]["execution_profile_reason_code"] == "profile_applied"
    assert internal["tkya_signals"]["topology_mode"] == "analytics_graph"
    assert internal["tkya_signals"]["morse_signals"] == ["workflow_risky_pattern", "conflict_markers"]
    assert internal["tkya_signals"]["morse_todo_count"] == 2
    assert internal["tkya_signals"]["verification_required_checks"] == [
        "security scan",
        "integration-tests",
    ]

    assert public["tkya_signals"]["morse_signal_count"] == 2
    assert "morse_signals" not in public["tkya_signals"]
    assert public["tkya_signals"]["verification_required_checks_count"] == 2

    assert public["trace_summary"]["trace_schema_version"] == "1.1"
    assert public["trace_summary"]["trace_hash_ref_count"] >= 1
    assert public["trace_summary"]["hash_only_policy"]["raw_prompt_exposed"] is False
    assert public["model_summary"]["adapter_contract_version"] == "llm_model_adapter_v1"
    assert public["model_summary"]["llm_provider"] == "github_models"
    assert public["model_summary"]["llm_model_requested_id"] == "openai/gpt-4.1"
    assert public["model_summary"]["llm_model_selected_id"] == "openai/gpt-4.1-mini"
    assert public["model_summary"]["llm_model_final_id"] == "openai/gpt-4.1"
    assert public["model_summary"]["llm_model_family"] == "gpt-4.1"
    assert public["model_summary"]["llm_model_downgrade_occurred"] is True
    assert public["model_summary"]["llm_execution_profile_used"] == "balanced"
    assert public["model_summary"]["llm_profile_policy_outcome"] == "profile_applied"
    assert public["model_summary"]["llm_profile_override_applied"] is False
    assert public["provenance_summary"]["runtime_provenance_confidence"] == "high"
    assert public["repository_scale"]["scale_truth_scope"] == "workspace_checkout_snapshot"

    assert "RepoBrain TKYA Evidence Pack v1" in summary
    assert "Route: `REVIEW`" in summary
    assert "Runtime provenance status: `aligned`" in summary
    assert "Scope: `workspace_checkout_snapshot`" in summary


def test_public_safe_payload_does_not_emit_raw_content_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    (repo_root / "main.py").write_text("print('safe')\n", encoding="utf-8")

    result = write_tkya_evidence_pack_artifacts(repo_root=repo_root, audit=_sample_audit())
    public_payload = orjson.loads(Path(str(result["public_safe_path"])).read_bytes())

    hash_policy = public_payload["trace_summary"]["hash_only_policy"]
    assert hash_policy["raw_prompt_exposed"] is False
    assert hash_policy["raw_diff_payload_exposed"] is False
    assert hash_policy["raw_candidate_text_exposed"] is False

    flattened = str(public_payload).lower()
    assert "raw_prompt_text" not in flattened
    assert "raw_diff_text" not in flattened
