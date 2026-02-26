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
        "tky_mode_requested": str(env_ctx.get("tky_mode_requested", "")),
        "tky_mode_used": "n/a",
        "tky_remote_status": None,
        "tky_fallback_reason": "n/a",
        "route_final": "",
        "pass_count": 0,
        "retrieved": 0,
        "selected": 0,
        "top_score_pass1": None,
        "top_score_pass2": None,
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

    fallback_reason = str(normalized.get("tky_fallback_reason", "n/a") or "n/a")
    normalized["tky_fallback_reason"] = fallback_reason

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
