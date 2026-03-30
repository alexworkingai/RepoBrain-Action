from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any


def _latest_audit_path(audit_dir: Path) -> Path | None:
    candidates = sorted(
        audit_dir.glob("audit_*.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
    )
    return candidates[-1] if candidates else None


def _as_str(value: Any, default: str = "n/a") -> str:
    text = str(value or "").strip()
    return text or default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _build_payloads(audit: dict[str, Any], source_path: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base: dict[str, Any] = {
        "schema_version": "tkya_evidence_pack_v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_audit_path": source_path,
        "run_identity": {
            "run_id": _as_str(audit.get("run_id", "")),
            "repo": _as_str(audit.get("repo", "")),
            "issue_number": _as_int(audit.get("issue_number", 0)),
            "pr_number": _as_int(audit.get("pr_number", 0)),
            "sha": _as_str(audit.get("sha", "")),
        },
        "execution_summary": {
            "command": _as_str(audit.get("command", "")),
            "task_type": _as_str(audit.get("task_type", "")),
            "route_final": _as_str(audit.get("route_final", "")),
            "execution_mode": _as_str(audit.get("execution_mode", "")),
            "llm_intent": _as_str(audit.get("llm_intent", "")),
            "llm_decision_reason_code": _as_str(audit.get("llm_decision_reason_code", "")),
        },
        "verification_summary": {
            "verification_completeness": audit.get("verification_completeness", 0),
            "verification_gate_decision": _as_str(audit.get("verification_gate_decision", "")),
            "verification_gate_reason": _as_str(audit.get("verification_gate_reason", "")),
        },
        "boundedness_summary": {
            "evidence_budget_mode": _as_str(audit.get("evidence_budget_mode", "not_applied")),
            "ultra_large_pr_mode_active": _as_bool(audit.get("ultra_large_pr_mode_active", False)),
            "review_delta_status": _as_str(audit.get("review_delta_status", "inactive")),
        },
        "provenance_summary": {
            "runtime_provenance_status": _as_str(audit.get("runtime_provenance_status", "not_applicable")),
            "runtime_provenance_reason_code": _as_str(
                audit.get("runtime_provenance_reason_code", "not_applicable")
            ),
            "runtime_provenance_runtime_sha": _as_str(
                audit.get("runtime_provenance_runtime_sha", audit.get("sha", ""))
            ),
            "runtime_provenance_pr_head_sha": _as_str(audit.get("runtime_provenance_pr_head_sha", "")),
            "runtime_provenance_sha_match": _as_bool(audit.get("runtime_provenance_sha_match", False)),
        },
        "trace_summary": {
            "trace_schema_version": _as_str(audit.get("trace_schema_version", "")),
            "trace_schema_policy": _as_str(audit.get("trace_schema_policy", "")),
            "trace_schema_compatible": _as_bool(audit.get("trace_schema_compatible", False)),
            "trace_hash_refs": {
                "trace_query_hash": _as_str(audit.get("trace_query_hash", ""), ""),
                "trace_selected_hash": _as_str(audit.get("trace_selected_hash", ""), ""),
                "trace_ranking_hash": _as_str(audit.get("trace_ranking_hash", ""), ""),
                "trace_github_scope_hash": _as_str(audit.get("trace_github_scope_hash", ""), ""),
                "trace_zigzag_hash": _as_str(audit.get("trace_zigzag_hash", ""), ""),
                "trace_morse_hash": _as_str(audit.get("trace_morse_hash", ""), ""),
                "trace_inputs_hash": _as_str(audit.get("trace_inputs_hash", ""), ""),
            },
            "hash_only_policy": {
                "raw_prompt_exposed": False,
                "raw_candidate_text_exposed": False,
                "raw_diff_payload_exposed": False,
            },
        },
    }
    internal = {
        **base,
        "artifact_kind": "internal",
        "tkya_signals": {
            "topology_mode": _as_str(audit.get("topology_mode", "not_available")),
            "topology_complexity": _as_str(audit.get("topology_complexity", "not_available")),
            "huk_score": audit.get("huk_score", 0),
            "zigzag_turning_points": _as_int(audit.get("zigzag_turning_points", 0)),
            "zigzag_volatility": audit.get("zigzag_volatility", 0),
            "morse_risk": _as_str(audit.get("morse_risk", "not_available")),
            "morse_verify_required": _as_bool(audit.get("morse_verify_required", False)),
            "morse_signals": audit.get("morse_signals", [])
            if isinstance(audit.get("morse_signals", []), list)
            else [],
        },
    }
    public = {
        **base,
        "artifact_kind": "public_safe",
        "tkya_signals": {
            "topology_mode": _as_str(audit.get("topology_mode", "not_available")),
            "topology_complexity": _as_str(audit.get("topology_complexity", "not_available")),
            "morse_risk": _as_str(audit.get("morse_risk", "not_available")),
            "morse_verify_required": _as_bool(audit.get("morse_verify_required", False)),
            "morse_signal_count": len(audit.get("morse_signals", []))
            if isinstance(audit.get("morse_signals", []), list)
            else 0,
        },
    }
    return internal, public


def _build_markdown(public_payload: dict[str, Any]) -> str:
    run = public_payload.get("run_identity", {})
    execution = public_payload.get("execution_summary", {})
    verification = public_payload.get("verification_summary", {})
    provenance = public_payload.get("provenance_summary", {})
    lines = [
        "# RepoBrain TKYA Evidence Pack v1",
        "",
        "## Run",
        f"- Run id: `{_as_str(run.get('run_id', 'n/a'))}`",
        f"- PR: `{_as_int(run.get('pr_number', 0))}`",
        f"- Command: `{_as_str(execution.get('command', 'n/a'))}`",
        "",
        "## Decision",
        f"- Route: `{_as_str(execution.get('route_final', 'n/a'))}`",
        f"- Execution mode: `{_as_str(execution.get('execution_mode', 'n/a'))}`",
        f"- LLM intent: `{_as_str(execution.get('llm_intent', 'n/a'))}`",
        "",
        "## Verification",
        f"- Gate decision: `{_as_str(verification.get('verification_gate_decision', 'n/a'))}`",
        f"- Gate reason: `{_as_str(verification.get('verification_gate_reason', 'n/a'))}`",
        "",
        "## Provenance",
        f"- Runtime provenance status: `{_as_str(provenance.get('runtime_provenance_status', 'not_applicable'))}`",
        f"- SHA match: `{str(_as_bool(provenance.get('runtime_provenance_sha_match', False))).lower()}`",
        "",
        "Public-safe summary derived from canonical run audit.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", default="artifacts/audit")
    parser.add_argument("--output-dir", default="artifacts/evidence_pack")
    args = parser.parse_args()

    audit_dir = Path(args.audit_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    latest = _latest_audit_path(audit_dir)
    if latest is None:
        audit: dict[str, Any] = {}
        source_path = "n/a"
    else:
        source_path = latest.as_posix()
        try:
            loaded = json.loads(latest.read_text(encoding="utf-8"))
            audit = loaded if isinstance(loaded, dict) else {}
        except Exception:
            audit = {}

    internal, public = _build_payloads(audit, source_path)
    markdown = _build_markdown(public)

    internal_path = output_dir / "repobrain_tkya_evidence_pack_internal.json"
    public_path = output_dir / "repobrain_tkya_evidence_pack_public_safe.json"
    md_path = output_dir / "repobrain_tkya_evidence_pack.md"
    internal_path.write_text(json.dumps(internal, ensure_ascii=False, indent=2), encoding="utf-8")
    public_path.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")

    print(f"TKYA_EVIDENCE_PACK_AUDIT_SOURCE={source_path}")
    print(f"TKYA_EVIDENCE_PACK_INTERNAL_PATH={internal_path.as_posix()}")
    print(f"TKYA_EVIDENCE_PACK_PUBLIC_SAFE_PATH={public_path.as_posix()}")
    print(f"TKYA_EVIDENCE_PACK_MD_PATH={md_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
