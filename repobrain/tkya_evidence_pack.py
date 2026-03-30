from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time
from typing import Any

import orjson

from repobrain.llm.model_adapter_contract import (
    MODEL_ADAPTER_CONTRACT_VERSION,
    build_model_adapter_metadata,
)

_SKIP_DIRS = {
    ".git",
    "artifacts",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}
_TRACE_HASH_KEYS: tuple[str, ...] = (
    "trace_query_hash",
    "trace_selected_hash",
    "trace_ranking_hash",
    "trace_github_scope_hash",
    "trace_zigzag_hash",
    "trace_morse_hash",
    "trace_inputs_hash",
)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "n/a") -> str:
    text = str(value or "").strip()
    return text or default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _repo_scale(repo_root: Path, audit: dict[str, Any]) -> dict[str, Any]:
    file_count = 0
    folder_count = 0
    total_size_bytes = 0
    skipped_dir_count = 0
    hidden_dirs_included_count = 0
    scan_error_count = 0

    for root, dirs, files in os.walk(repo_root):
        original_dirs = list(dirs)
        skipped_dir_count += sum(1 for d in original_dirs if d in _SKIP_DIRS)
        hidden_dirs_included_count += sum(
            1 for d in original_dirs if d.startswith(".") and d not in _SKIP_DIRS
        )
        dirs[:] = [d for d in original_dirs if d not in _SKIP_DIRS]
        folder_count += len(dirs)
        for name in files:
            path = Path(root) / name
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            file_count += 1
            try:
                total_size_bytes += int(path.stat().st_size)
            except OSError:
                scan_error_count += 1
                continue

    git_tracked_files_total = 0
    git_tracked_files_available = False
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(repo_root),
            capture_output=True,
            text=False,
            check=False,
        )
        if int(proc.returncode) == 0:
            blob = bytes(proc.stdout or b"")
            git_tracked_files_total = int(len([p for p in blob.split(b"\x00") if p]))
            git_tracked_files_available = True
    except Exception:
        git_tracked_files_total = 0
        git_tracked_files_available = False

    source_scope = "workspace_checkout_snapshot"
    source_explanation = (
        "Counts reflect files available in the current runtime workspace checkout, "
        "not an out-of-band full repository history scan."
    )

    return {
        "files_total": int(file_count),
        "folders_total": int(folder_count),
        "size_bytes_total": int(total_size_bytes),
        "skipped_dirs": sorted(_SKIP_DIRS),
        "skipped_dir_count": int(skipped_dir_count),
        "hidden_dirs_included_count": int(hidden_dirs_included_count),
        "scan_error_count": int(scan_error_count),
        "git_tracked_files_available": bool(git_tracked_files_available),
        "git_tracked_files_total": int(git_tracked_files_total),
        "scale_truth_scope": source_scope,
        "scale_truth_explanation": source_explanation,
        "workspace_path": repo_root.as_posix(),
        "event_name": _as_str(audit.get("runtime_provenance_event_name", "unknown")),
    }


def _trace_summary(audit: dict[str, Any]) -> dict[str, Any]:
    refs: dict[str, str] = {}
    for key in _TRACE_HASH_KEYS:
        value = _as_str(audit.get(key, ""), default="")
        if value:
            refs[key] = value
    return {
        "trace_schema_version": _as_str(audit.get("trace_schema_version", "n/a")),
        "trace_schema_policy": _as_str(audit.get("trace_schema_policy", "n/a")),
        "trace_schema_compatible": _as_bool(audit.get("trace_schema_compatible", False)),
        "trace_hash_refs": refs,
        "trace_hash_ref_count": len(refs),
        "hash_only_policy": {
            "raw_prompt_exposed": False,
            "raw_candidate_text_exposed": False,
            "raw_diff_payload_exposed": False,
        },
    }


def _execution_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": _as_str(audit.get("command", "n/a")),
        "task_type": _as_str(audit.get("task_type", "n/a")),
        "route_final": _as_str(audit.get("route_final", "n/a")),
        "execution_mode": _as_str(audit.get("execution_mode", "n/a")),
        "llm_intent": _as_str(audit.get("llm_intent", "n/a")),
        "llm_decision_reason_code": _as_str(audit.get("llm_decision_reason_code", "n/a")),
        "llm_decision_reason_short": _as_str(audit.get("llm_decision_reason_short", "n/a")),
        "tkya_backend": _as_str(audit.get("tkya_backend", "n/a")),
        "tky_engine": _as_str(audit.get("tky_engine", "n/a")),
        "selected_evidence_count": _as_int(audit.get("selected", 0)),
        "retrieved_candidates_count": _as_int(audit.get("retrieved", 0)),
        "selected_chunk_ids_count": _as_int(
            audit.get("tky_selected_chunk_ids_count", audit.get("selected", 0))
        ),
    }


def _tkya_signals(audit: dict[str, Any], *, public_safe: bool) -> dict[str, Any]:
    signals = {
        "topology_mode": _as_str(audit.get("topology_mode", "not_available")),
        "topology_complexity": _as_str(audit.get("topology_complexity", "not_available")),
        "topology_metric_count": _as_int(audit.get("topology_metric_count", 0)),
        "huk_score": _as_float(audit.get("huk_score", 0.0)),
        "huk_bars_hash": _as_str(audit.get("huk_bars_hash", "n/a")),
        "zigzag_turning_points": _as_int(audit.get("zigzag_turning_points", 0)),
        "zigzag_volatility": _as_float(audit.get("zigzag_volatility", 0.0)),
        "zigzag_trend": _as_str(audit.get("zigzag_trend", "not_available")),
        "morse_risk": _as_str(audit.get("morse_risk", "not_available")),
        "morse_verify_required": _as_bool(audit.get("morse_verify_required", False)),
        "morse_confidence": _as_float(audit.get("morse_confidence", 0.0)),
        "morse_todo_count": _as_int(audit.get("morse_todo_count", 0)),
        "morse_conflict_markers": _as_bool(audit.get("morse_conflict_markers", False)),
        "morse_secret_signal": _as_bool(audit.get("morse_secret_signal", False)),
        "morse_workflow_risky": _as_bool(audit.get("morse_workflow_risky", False)),
        "morse_test_disable_signal": _as_bool(audit.get("morse_test_disable_signal", False)),
        "verification_completeness": _as_float(audit.get("verification_completeness", 0.0)),
        "verification_gate_decision": _as_str(audit.get("verification_gate_decision", "n/a")),
        "verification_gate_reason": _as_str(audit.get("verification_gate_reason", "n/a")),
    }

    morse_signals_raw = audit.get("morse_signals", [])
    morse_signals = (
        [str(item).strip() for item in morse_signals_raw if str(item).strip()]
        if isinstance(morse_signals_raw, list)
        else []
    )
    if public_safe:
        signals["morse_signal_count"] = len(morse_signals)
        signals["verification_required_checks_count"] = _as_int(
            len(audit.get("verification_required_checks", []))
            if isinstance(audit.get("verification_required_checks", []), list)
            else 0
        )
    else:
        signals["morse_signals"] = morse_signals
        required_checks = audit.get("verification_required_checks", [])
        signals["verification_required_checks"] = (
            [str(item).strip() for item in required_checks if str(item).strip()]
            if isinstance(required_checks, list)
            else []
        )

    return signals


def _verification_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall": _as_str(audit.get("verification_overall", "NOT_RUN")),
        "pass_count": _as_int(audit.get("verification_pass_count", 0)),
        "fail_count": _as_int(audit.get("verification_fail_count", 0)),
        "pending_count": _as_int(audit.get("verification_pending_count", 0)),
        "not_run_count": _as_int(audit.get("verification_not_run_count", 0)),
        "profile": _as_str(audit.get("verification_profile", "n/a")),
        "branch": _as_str(audit.get("verification_branch", "n/a")),
        "gate_decision": _as_str(audit.get("verification_gate_decision", "n/a")),
        "gate_reason": _as_str(audit.get("verification_gate_reason", "n/a")),
    }


def _boundedness_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_budget_mode": _as_str(audit.get("evidence_budget_mode", "not_applied")),
        "evidence_budget_used": _as_int(audit.get("evidence_budget_used", 0)),
        "evidence_budget_limit": _as_int(audit.get("evidence_budget_limit", 0)),
        "evidence_budget_overflow": _as_int(audit.get("evidence_budget_overflow", 0)),
        "ultra_large_pr_mode_active": _as_bool(audit.get("ultra_large_pr_mode_active", False)),
        "ultra_large_pr_mode_level": _as_str(audit.get("ultra_large_pr_mode_level", "normal")),
        "ultra_large_pr_mode_reason": _as_str(audit.get("ultra_large_pr_mode_reason", "none")),
        "ultra_large_pr_coverage_statement": _as_str(
            audit.get("ultra_large_pr_coverage_statement", "n/a")
        ),
        "review_delta_status": _as_str(audit.get("review_delta_status", "inactive")),
        "review_delta_prior_state_available": _as_bool(
            audit.get("review_delta_prior_state_available", False)
        ),
    }


def _provenance_summary(audit: dict[str, Any]) -> dict[str, Any]:
    status = _as_str(audit.get("runtime_provenance_status", "not_applicable"))
    if status == "aligned":
        confidence = "high"
    elif status == "governed_divergent":
        confidence = "bounded"
    else:
        confidence = "not_applicable"
    return {
        "runtime_provenance_status": status,
        "runtime_provenance_reason_code": _as_str(
            audit.get("runtime_provenance_reason_code", "not_applicable")
        ),
        "runtime_provenance_explanation": _as_str(
            audit.get("runtime_provenance_explanation", "not_applicable")
        ),
        "runtime_provenance_event_name": _as_str(
            audit.get("runtime_provenance_event_name", "unknown")
        ),
        "runtime_provenance_runtime_sha": _as_str(
            audit.get("runtime_provenance_runtime_sha", audit.get("sha", "n/a"))
        ),
        "runtime_provenance_pr_head_sha": _as_str(audit.get("runtime_provenance_pr_head_sha", "n/a")),
        "runtime_provenance_sha_match": _as_bool(audit.get("runtime_provenance_sha_match", False)),
        "runtime_provenance_pr_state": _as_str(audit.get("runtime_provenance_pr_state", "unknown")),
        "runtime_provenance_same_repo_pr": _as_bool(audit.get("runtime_provenance_same_repo_pr", False)),
        "runtime_provenance_confidence": confidence,
    }


def _model_summary(audit: dict[str, Any]) -> dict[str, Any]:
    adapter = build_model_adapter_metadata(
        audit,
        provider_hint=_as_str(audit.get("llm_provider", ""), default=""),
    )
    return {
        "adapter_contract_version": MODEL_ADAPTER_CONTRACT_VERSION,
        "llm_used": bool(adapter.llm_used),
        "llm_provider": adapter.provider,
        "llm_provider_class": adapter.provider_class,
        "llm_request_mode": adapter.request_mode,
        "llm_execution_mode": adapter.execution_mode,
        "llm_intent": adapter.llm_intent,
        "llm_policy_allowed": bool(adapter.policy_allowed),
        "llm_model_requested_id": adapter.requested_model_id,
        "llm_model_preferred_id": adapter.preferred_model_id,
        "llm_model_selected_id": adapter.selected_model_id,
        "llm_model_final_id": adapter.final_model_id,
        "llm_model_family": adapter.model_family,
        "llm_model_downgrade_occurred": bool(adapter.downgrade_occurred),
        "llm_model_downgrade_reason": adapter.downgrade_reason,
        "llm_provider_http_status": adapter.provider_http_status,
        "llm_provider_error_type": adapter.provider_error_type,
        "llm_model_used": _as_str(audit.get("llm_model_used", "not_used")),
        "llm_final_synthesis_model_id": _as_str(
            audit.get("llm_final_synthesis_model_id", "not_used")
        ),
        "llm_tokens_total": _as_int(audit.get("llm_tokens_total", 0)),
    }


def _base_payload(audit: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": "tkya_evidence_pack_v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_identity": {
            "run_id": _as_str(audit.get("run_id", "n/a")),
            "repo": _as_str(audit.get("repo", "n/a")),
            "issue_number": _as_int(audit.get("issue_number", 0)),
            "pr_number": _as_int(audit.get("pr_number", 0)),
            "sha": _as_str(audit.get("sha", "n/a")),
        },
        "repository_scale": _repo_scale(repo_root, audit),
        "execution_summary": _execution_summary(audit),
        "verification_summary": _verification_summary(audit),
        "boundedness_summary": _boundedness_summary(audit),
        "provenance_summary": _provenance_summary(audit),
        "model_summary": _model_summary(audit),
        "security_summary": {
            "security_scope": _as_str(audit.get("security_scope", "n/a")),
            "security_outcome": _as_str(audit.get("security_outcome", "n/a")),
            "security_reason_code": _as_str(audit.get("security_reason_code", "n/a")),
            "security_reason_short": _as_str(audit.get("security_reason_short", "n/a")),
        },
        "trace_summary": _trace_summary(audit),
        "legacy_runtime_status": {
            "legacy_generation_active": False,
            "legacy_generation_reason": "removed_from_active_runtime",
        },
    }


def _build_internal_payload(audit: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    payload = _base_payload(audit, repo_root)
    payload["artifact_kind"] = "internal"
    payload["tkya_signals"] = _tkya_signals(audit, public_safe=False)
    return payload


def _build_public_payload(audit: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    payload = _base_payload(audit, repo_root)
    payload["artifact_kind"] = "public_safe"
    payload["tkya_signals"] = _tkya_signals(audit, public_safe=True)
    return payload


def _render_markdown_summary(public_payload: dict[str, Any]) -> str:
    run_identity = public_payload.get("run_identity", {}) if isinstance(public_payload, dict) else {}
    execution = public_payload.get("execution_summary", {}) if isinstance(public_payload, dict) else {}
    tkya = public_payload.get("tkya_signals", {}) if isinstance(public_payload, dict) else {}
    verification = public_payload.get("verification_summary", {}) if isinstance(public_payload, dict) else {}
    boundedness = public_payload.get("boundedness_summary", {}) if isinstance(public_payload, dict) else {}
    provenance = public_payload.get("provenance_summary", {}) if isinstance(public_payload, dict) else {}
    scale = public_payload.get("repository_scale", {}) if isinstance(public_payload, dict) else {}

    lines = [
        "# RepoBrain TKYA Evidence Pack v1",
        "",
        "## Run",
        f"- Run id: `{_as_str(run_identity.get('run_id', 'n/a'))}`",
        f"- Repo: `{_as_str(run_identity.get('repo', 'n/a'))}`",
        f"- PR: `{_as_int(run_identity.get('pr_number', 0))}`",
        f"- Command: `{_as_str(execution.get('command', 'n/a'))}`",
        "",
        "## Decision",
        f"- Route: `{_as_str(execution.get('route_final', 'n/a'))}`",
        f"- Execution mode: `{_as_str(execution.get('execution_mode', 'n/a'))}`",
        f"- LLM intent: `{_as_str(execution.get('llm_intent', 'n/a'))}`",
        f"- Topology mode: `{_as_str(tkya.get('topology_mode', 'not_available'))}`",
        f"- Topology complexity: `{_as_str(tkya.get('topology_complexity', 'not_available'))}`",
        f"- Morse risk: `{_as_str(tkya.get('morse_risk', 'not_available'))}`",
        f"- Verification gate: `{_as_str(verification.get('gate_decision', 'n/a'))}`",
        "",
        "## Boundedness",
        f"- Evidence budget: `{_as_str(boundedness.get('evidence_budget_mode', 'not_applied'))}`",
        f"- Budget usage: `{_as_int(boundedness.get('evidence_budget_used', 0))}/{_as_int(boundedness.get('evidence_budget_limit', 0))}`",
        f"- Ultra-large PR mode active: `{str(_as_bool(boundedness.get('ultra_large_pr_mode_active', False))).lower()}`",
        f"- Coverage statement: `{_as_str(boundedness.get('ultra_large_pr_coverage_statement', 'n/a'))}`",
        "",
        "## Provenance",
        f"- Runtime provenance status: `{_as_str(provenance.get('runtime_provenance_status', 'not_applicable'))}`",
        f"- Runtime provenance confidence: `{_as_str(provenance.get('runtime_provenance_confidence', 'not_applicable'))}`",
        f"- SHA match: `{str(_as_bool(provenance.get('runtime_provenance_sha_match', False))).lower()}`",
        f"- Runtime SHA: `{_as_str(provenance.get('runtime_provenance_runtime_sha', 'n/a'))}`",
        f"- PR head SHA: `{_as_str(provenance.get('runtime_provenance_pr_head_sha', 'n/a'))}`",
        f"- Provenance reason: `{_as_str(provenance.get('runtime_provenance_reason_code', 'not_applicable'))}`",
        "",
        "## Repository Scale",
        f"- Files scanned: `{_as_int(scale.get('files_total', 0))}`",
        f"- Folders scanned: `{_as_int(scale.get('folders_total', 0))}`",
        f"- Approx size bytes: `{_as_int(scale.get('size_bytes_total', 0))}`",
        f"- Scope: `{_as_str(scale.get('scale_truth_scope', 'workspace_checkout_snapshot'))}`",
        f"- Git tracked files available: `{str(_as_bool(scale.get('git_tracked_files_available', False))).lower()}`",
        f"- Git tracked files total: `{_as_int(scale.get('git_tracked_files_total', 0))}`",
        "",
        "This summary is public-safe and derived from canonical audit truth.",
    ]
    return "\n".join(lines) + "\n"


def write_tkya_evidence_pack_artifacts(
    *,
    repo_root: Path,
    audit: dict[str, Any],
    output_dir: Path | None = None,
) -> dict[str, Any]:
    target_dir = output_dir or (repo_root / "artifacts" / "evidence_pack")
    target_dir.mkdir(parents=True, exist_ok=True)

    internal_path = target_dir / "repobrain_tkya_evidence_pack_internal.json"
    public_path = target_dir / "repobrain_tkya_evidence_pack_public_safe.json"
    summary_path = target_dir / "repobrain_tkya_evidence_pack.md"

    internal_payload = _build_internal_payload(audit, repo_root)
    public_payload = _build_public_payload(audit, repo_root)
    summary_markdown = _render_markdown_summary(public_payload)

    internal_path.write_bytes(
        orjson.dumps(internal_payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    public_path.write_bytes(
        orjson.dumps(public_payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    summary_path.write_text(summary_markdown, encoding="utf-8")

    return {
        "schema_version": "tkya_evidence_pack_v1",
        "internal_path": internal_path.as_posix(),
        "public_safe_path": public_path.as_posix(),
        "summary_path": summary_path.as_posix(),
        "route": _as_str(audit.get("route_final", "n/a")),
    }
