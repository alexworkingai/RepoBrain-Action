from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


def build_audit_base(env_ctx: dict[str, Any]) -> dict[str, Any]:
    """Build a hash-only audit skeleton for one RepoBrain run."""
    return {
        "command": str(env_ctx.get("command", "")),
        "task_type": str(env_ctx.get("task_type", "")),
        "repo": str(env_ctx.get("repo", "")),
        "sha": str(env_ctx.get("sha", "")),
        "run_id": str(env_ctx.get("run_id", "")),
        "issue_number": env_ctx.get("issue_number"),
        "pr_number": env_ctx.get("pr_number"),
        "comment_id": env_ctx.get("comment_id"),
        "dry_run": bool(env_ctx.get("dry_run", False)),
        "posted": bool(env_ctx.get("posted", False)),
        "mode": str(env_ctx.get("mode", "")),
        "timings_ms": {},
        "security": {"blocked": False, "risk": "low", "signals": []},
        "index_source": "n/a",
        "config_loaded": False,
        "config_path": "<missing>",
        "config_remote_enabled": False,
        "config_allow_commands_count": 0,
        "config_allow_branches_count": 0,
        "config_allow_repos_count": 0,
        "tky_mode_requested": str(env_ctx.get("tky_mode_requested", "")),
        "tky_mode_used": "n/a",
        "tky_engine": "n/a",
        "remote_used": False,
        "remote_latency_ms": None,
        "remote_retry_count": 0,
        "remote_rate_limited": False,
        "remote_error_class": "n/a",
        "fallback_reason_code": "n/a",
        "remote_skipped_reason": "n/a",
        "tky_remote_status": None,
        "tky_fallback_reason": "n/a",
        "route_final": "",
        "pass_count": 0,
        "retrieved": 0,
        "selected": 0,
        "incremental_retrieval_used": False,
        "incremental_scope_mode": "fallback_full",
        "changed_files_considered": 0,
        "changed_regions_considered": 0,
        "unchanged_files_skipped": 0,
        "unchanged_chunks_skipped": 0,
        "retrieval_cache_hits": 0,
        "retrieval_cache_misses": 0,
        "incremental_fallback_reason": "none",
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
        "pr_segmentation_used": False,
        "pr_segment_count": 0,
        "pr_primary_segments": "none",
        "pr_support_segments": "none",
        "pr_cross_segment": False,
        "pr_segment_summary": "none",
        "pr_segment_file_counts": "none",
        "pr_segment_candidate_counts": "none",
        "pr_segmentation_fallback_reason": "not_applicable",
        "top_score_pass1": None,
        "top_score_pass2": None,
        "rd": {
            "rd_used": False,
            "rd_status": "n/a",
            "rd_template_id": "n/a",
            "rd_intent_hash": "n/a",
            "rd_policy_hash": "n/a",
            "rd_has_signature": False,
            "rd_has_attestation": False,
            "rd_error_count": 0,
            "rd_warning_count": 0,
            "rd_record_hash": "n/a",
        },
    }


def add_timing(audit: dict[str, Any], name: str, ms: float) -> None:
    """Add/update a timing entry in milliseconds."""
    timings = audit.setdefault("timings_ms", {})
    if isinstance(timings, dict):
        timings[name] = round(max(0.0, float(ms)), 3)


def write_audit(audit: dict[str, Any], path: Path) -> Path:
    """Write audit JSON using orjson with indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = orjson.dumps(audit, option=orjson.OPT_INDENT_2)
    path.write_bytes(payload)
    return path


def finalize_audit(audit: dict[str, Any]) -> dict[str, Any]:
    """Normalize audit fields to stable enums/types (no empty strings in key diagnostics)."""
    normalized = dict(audit)

    valid_index_sources = {"cache_hit", "artifact_present", "rebuilt", "n/a"}
    index_source = str(normalized.get("index_source", "n/a") or "n/a")
    normalized["index_source"] = index_source if index_source in valid_index_sources else "n/a"

    tky_mode_used = str(normalized.get("tky_mode_used", "n/a") or "n/a")
    normalized["tky_mode_used"] = tky_mode_used

    tky_engine = str(normalized.get("tky_engine", "n/a") or "n/a")
    normalized["tky_engine"] = tky_engine

    fallback_reason = str(normalized.get("tky_fallback_reason", "n/a") or "n/a")
    normalized["tky_fallback_reason"] = fallback_reason

    normalized["remote_used"] = bool(normalized.get("remote_used", False))
    normalized["remote_rate_limited"] = bool(normalized.get("remote_rate_limited", False))

    try:
        normalized["remote_retry_count"] = int(normalized.get("remote_retry_count", 0) or 0)
    except (TypeError, ValueError):
        normalized["remote_retry_count"] = 0

    remote_latency = normalized.get("remote_latency_ms", None)
    if remote_latency in {"", "n/a"}:
        normalized["remote_latency_ms"] = None
    elif remote_latency is None:
        normalized["remote_latency_ms"] = None
    else:
        try:
            normalized["remote_latency_ms"] = round(max(0.0, float(remote_latency)), 3)
        except (TypeError, ValueError):
            normalized["remote_latency_ms"] = None

    normalized["remote_error_class"] = str(normalized.get("remote_error_class", "n/a") or "n/a")
    normalized["fallback_reason_code"] = str(normalized.get("fallback_reason_code", "n/a") or "n/a")
    normalized["remote_skipped_reason"] = str(normalized.get("remote_skipped_reason", "n/a") or "n/a")
    normalized["config_loaded"] = bool(normalized.get("config_loaded", False))
    normalized["config_path"] = str(normalized.get("config_path", "<missing>") or "<missing>")
    normalized["config_remote_enabled"] = bool(normalized.get("config_remote_enabled", False))
    try:
        normalized["config_allow_commands_count"] = int(
            normalized.get("config_allow_commands_count", 0) or 0
        )
    except (TypeError, ValueError):
        normalized["config_allow_commands_count"] = 0
    try:
        normalized["config_allow_branches_count"] = int(
            normalized.get("config_allow_branches_count", 0) or 0
        )
    except (TypeError, ValueError):
        normalized["config_allow_branches_count"] = 0
    try:
        normalized["config_allow_repos_count"] = int(
            normalized.get("config_allow_repos_count", 0) or 0
        )
    except (TypeError, ValueError):
        normalized["config_allow_repos_count"] = 0

    remote_status = normalized.get("tky_remote_status", None)
    if remote_status in {"", "n/a"}:
        normalized["tky_remote_status"] = None
    elif isinstance(remote_status, bool):
        normalized["tky_remote_status"] = int(remote_status)
    elif isinstance(remote_status, int):
        normalized["tky_remote_status"] = remote_status
    else:
        try:
            normalized["tky_remote_status"] = int(remote_status)
        except (TypeError, ValueError):
            normalized["tky_remote_status"] = None

    try:
        normalized["evidence_budget_used"] = int(normalized.get("evidence_budget_used", 0) or 0)
    except (TypeError, ValueError):
        normalized["evidence_budget_used"] = 0
    try:
        normalized["evidence_budget_limit"] = int(normalized.get("evidence_budget_limit", 0) or 0)
    except (TypeError, ValueError):
        normalized["evidence_budget_limit"] = 0
    normalized["evidence_budget_mode"] = str(
        normalized.get("evidence_budget_mode", "not_applied") or "not_applied"
    )
    normalized["evidence_budget_bucket_counts"] = str(
        normalized.get(
            "evidence_budget_bucket_counts",
            "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
        )
        or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
    )
    normalized["evidence_budget_cutoffs"] = str(
        normalized.get("evidence_budget_cutoffs", "no_cutoff") or "no_cutoff"
    )
    try:
        normalized["evidence_budget_overflow"] = int(normalized.get("evidence_budget_overflow", 0) or 0)
    except (TypeError, ValueError):
        normalized["evidence_budget_overflow"] = 0
    try:
        normalized["evidence_budget_primary_selected"] = int(
            normalized.get("evidence_budget_primary_selected", 0) or 0
        )
    except (TypeError, ValueError):
        normalized["evidence_budget_primary_selected"] = 0
    try:
        normalized["evidence_budget_support_selected"] = int(
            normalized.get("evidence_budget_support_selected", 0) or 0
        )
    except (TypeError, ValueError):
        normalized["evidence_budget_support_selected"] = 0
    normalized["pr_segmentation_used"] = bool(normalized.get("pr_segmentation_used", False))
    try:
        normalized["pr_segment_count"] = int(normalized.get("pr_segment_count", 0) or 0)
    except (TypeError, ValueError):
        normalized["pr_segment_count"] = 0
    normalized["pr_primary_segments"] = str(normalized.get("pr_primary_segments", "none") or "none")
    normalized["pr_support_segments"] = str(normalized.get("pr_support_segments", "none") or "none")
    normalized["pr_cross_segment"] = bool(normalized.get("pr_cross_segment", False))
    normalized["pr_segment_summary"] = str(normalized.get("pr_segment_summary", "none") or "none")
    normalized["pr_segment_file_counts"] = str(normalized.get("pr_segment_file_counts", "none") or "none")
    normalized["pr_segment_candidate_counts"] = str(
        normalized.get("pr_segment_candidate_counts", "none") or "none"
    )
    normalized["pr_segmentation_fallback_reason"] = str(
        normalized.get("pr_segmentation_fallback_reason", "not_applicable") or "not_applicable"
    )

    rd_raw = normalized.get("rd", {})
    rd_payload: dict[str, Any] = dict(rd_raw) if isinstance(rd_raw, dict) else {}

    def _clean_str(key: str, default: str = "n/a") -> str:
        value = rd_payload.get(key, default)
        text = str(value).strip() if value is not None else ""
        return text or default

    def _clean_bool(key: str, default: bool = False) -> bool:
        value = rd_payload.get(key, default)
        return bool(value)

    def _clean_int(key: str, default: int = 0) -> int:
        value = rd_payload.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    allowed_status = {
        "n/a",
        "disabled",
        "ok",
        "blocked_validation",
        "unavailable",
        "error",
    }
    rd_status = _clean_str("rd_status", "n/a").lower()
    if rd_status not in allowed_status:
        rd_status = "n/a"

    normalized["rd"] = {
        "rd_used": _clean_bool("rd_used", False),
        "rd_status": rd_status,
        "rd_template_id": _clean_str("rd_template_id", "n/a"),
        "rd_intent_hash": _clean_str("rd_intent_hash", "n/a"),
        "rd_policy_hash": _clean_str("rd_policy_hash", "n/a"),
        "rd_has_signature": _clean_bool("rd_has_signature", False),
        "rd_has_attestation": _clean_bool("rd_has_attestation", False),
        "rd_error_count": _clean_int("rd_error_count", 0),
        "rd_warning_count": _clean_int("rd_warning_count", 0),
        "rd_record_hash": _clean_str("rd_record_hash", "n/a"),
    }

    timings = normalized.get("timings_ms", {})
    if isinstance(timings, dict):
        normalized_timings: dict[str, float] = {}
        for key, value in timings.items():
            try:
                normalized_timings[str(key)] = round(max(0.0, float(value)), 3)
            except (TypeError, ValueError):
                continue
        normalized["timings_ms"] = normalized_timings

    return normalized
