from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

import orjson

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown, render_review_markdown


@dataclass(frozen=True)
class AuditEntry:
    path: str
    mtime_s: float
    command: str
    run_id: str
    audit: dict[str, Any]


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _run_id_int(value: str) -> int:
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return 0


def _skip_meta(audit: dict[str, Any]) -> tuple[str, str] | None:
    reason_code = str(audit.get("skip_reason_code", "") or "").strip().lower()
    if not reason_code or reason_code == "n/a":
        return None
    reason_short = str(audit.get("skip_reason_short", "") or "").strip()
    return reason_code, (reason_short or reason_code)


def _snapshot_status(audit: dict[str, Any]) -> str:
    used = bool(audit.get("retrieval_snapshot_cache_used", False))
    hit = bool(audit.get("retrieval_snapshot_cache_hit", False))
    if used and hit:
        return "hit"
    if used:
        return "miss"
    return "not_applicable"


def _timing_total_ms(audit: dict[str, Any]) -> float:
    timings = audit.get("timings_ms", {})
    if not isinstance(timings, dict):
        return 0.0
    total = 0.0
    for value in timings.values():
        try:
            total += max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    return round(total, 3)


def _load_audit_entries(audit_dir: Path) -> list[AuditEntry]:
    entries: list[AuditEntry] = []
    if not audit_dir.exists():
        return entries
    for path in sorted(audit_dir.glob("audit_*.json")):
        try:
            payload = orjson.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        command = str(payload.get("command", "") or "").strip().lower()
        run_id = str(payload.get("run_id", "") or "").strip()
        try:
            mtime_s = float(path.stat().st_mtime)
        except OSError:
            mtime_s = 0.0
        entries.append(
            AuditEntry(
                path=path.as_posix(),
                mtime_s=mtime_s,
                command=command,
                run_id=run_id,
                audit=dict(payload),
            )
        )
    entries.sort(key=lambda item: (item.mtime_s, item.path))
    return entries


def _load_history_entries(history_path: Path) -> list[AuditEntry]:
    if not history_path.exists():
        return []
    try:
        payload = orjson.loads(history_path.read_bytes())
    except (OSError, ValueError):
        return []
    records = payload.get("entries", []) if isinstance(payload, dict) else []
    if not isinstance(records, list):
        return []
    entries: list[AuditEntry] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        audit_raw = item.get("audit", {})
        audit = dict(audit_raw) if isinstance(audit_raw, dict) else {}
        command = str(item.get("command", "") or "").strip().lower()
        run_id = str(item.get("run_id", "") or "").strip()
        path = str(item.get("path", "") or "").strip()
        if not path:
            path = f"history:{run_id or 'na'}:{command or 'na'}"
        mtime_s = 0.0
        try:
            mtime_s = float(item.get("mtime_s", 0.0) or 0.0)
        except (TypeError, ValueError):
            mtime_s = 0.0
        entries.append(
            AuditEntry(
                path=path,
                mtime_s=mtime_s,
                command=command,
                run_id=run_id,
                audit=audit,
            )
        )
    entries.sort(key=lambda item: (_run_id_int(item.run_id), item.mtime_s, item.path))
    return entries


def _entry_key(entry: AuditEntry) -> tuple[str, str, int, int]:
    return (
        str(entry.run_id or ""),
        str(entry.command or ""),
        _as_int(entry.audit.get("pr_number", 0)),
        _as_int(entry.audit.get("issue_number", 0)),
    )


def _merge_entries(existing: list[AuditEntry], current: list[AuditEntry]) -> list[AuditEntry]:
    merged: dict[tuple[str, str, int, int], AuditEntry] = {}
    for entry in existing + current:
        key = _entry_key(entry)
        prior = merged.get(key)
        if prior is None:
            merged[key] = entry
            continue
        if (
            _run_id_int(entry.run_id),
            entry.mtime_s,
            entry.path,
        ) >= (
            _run_id_int(prior.run_id),
            prior.mtime_s,
            prior.path,
        ):
            merged[key] = entry
    result = list(merged.values())
    result.sort(key=lambda item: (_run_id_int(item.run_id), item.mtime_s, item.path))
    return result


def _write_history_entries(history_path: Path, entries: list[AuditEntry], *, keep_last: int = 400) -> None:
    bounded = list(entries[-keep_last:])
    payload = {
        "schema_version": 1,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": [
            {
                "path": entry.path,
                "mtime_s": float(entry.mtime_s),
                "command": entry.command,
                "run_id": entry.run_id,
                "audit": entry.audit,
            }
            for entry in bounded
        ],
    }
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))


def _scope_entries_to_current_pr(entries: list[AuditEntry], current_entries: list[AuditEntry]) -> list[AuditEntry]:
    if not entries:
        return []
    if not current_entries:
        return list(entries)
    latest_current = current_entries[-1]
    latest_audit = latest_current.audit
    target_repo = str(latest_audit.get("repo", "") or "").strip().lower()
    target_pr = _as_int(latest_audit.get("pr_number", 0))
    target_issue = _as_int(latest_audit.get("issue_number", 0))

    scoped = list(entries)
    if target_repo:
        repo_scoped = [
            item
            for item in scoped
            if str(item.audit.get("repo", "") or "").strip().lower() == target_repo
        ]
        if repo_scoped:
            scoped = repo_scoped
    if target_pr > 0:
        pr_scoped = [item for item in scoped if _as_int(item.audit.get("pr_number", 0)) == target_pr]
        if pr_scoped:
            scoped = pr_scoped
    elif target_issue > 0:
        issue_scoped = [item for item in scoped if _as_int(item.audit.get("issue_number", 0)) == target_issue]
        if issue_scoped:
            scoped = issue_scoped

    scoped.sort(key=lambda item: (_run_id_int(item.run_id), item.mtime_s, item.path))
    return scoped


def _latest_for(entries: list[AuditEntry], command: str) -> AuditEntry | None:
    filtered = [entry for entry in entries if entry.command == command]
    return filtered[-1] if filtered else None


def _transition_for(entries: list[AuditEntry], command: str) -> dict[str, Any]:
    filtered = [entry for entry in entries if entry.command == command]
    if filtered:
        latest = filtered[-1]
        skip = _skip_meta(latest.audit)
        if skip is not None:
            reason_code, reason_short = skip
            return {
                "status": "skipped",
                "reason": reason_code,
                "skip_reason_short": reason_short,
                "first_status": "not_applicable",
                "second_status": "not_applicable",
                "run_ids": [latest.run_id],
                "paths": [latest.path],
            }
    if len(filtered) < 2:
        return {
            "status": "not_enough_data",
            "reason": "need_two_runs",
            "first_status": "not_applicable",
            "second_status": "not_applicable",
            "run_ids": [],
            "paths": [],
        }
    first, second = filtered[-2], filtered[-1]
    first_status = _snapshot_status(first.audit)
    second_status = _snapshot_status(second.audit)
    ok = first_status == "miss" and second_status == "hit"
    return {
        "status": "pass" if ok else "fail",
        "reason": "ok" if ok else "expected_miss_then_hit",
        "first_status": first_status,
        "second_status": second_status,
        "run_ids": [first.run_id, second.run_id],
        "paths": [first.path, second.path],
    }


def _ask_truth_binding_contract(entries: list[AuditEntry]) -> dict[str, Any]:
    latest = _latest_for(entries, "ask")
    if latest is None:
        return {"status": "not_enough_data", "reason": "ask_missing"}
    skip = _skip_meta(latest.audit)
    if skip is not None:
        reason_code, reason_short = skip
        return {
            "status": "skipped",
            "reason": reason_code,
            "skip_reason_short": reason_short,
        }
    audit = latest.audit
    pr_changed_count = int(audit.get("pr_changed_files_count", 0) or 0)
    if pr_changed_count <= 0:
        return {
            "status": "not_applicable",
            "reason": "ask_not_pr_metadata_context",
            "pr_changed_files_count": pr_changed_count,
        }
    pr_metadata_used = bool(audit.get("pr_metadata_used", False))
    grounding_mode = str(audit.get("answer_grounding_mode", "retrieval") or "retrieval")
    ok = pr_metadata_used and grounding_mode in {"pr_metadata", "hybrid"}
    return {
        "status": "pass" if ok else "fail",
        "reason": "ok" if ok else "pr_metadata_truth_binding_missing",
        "pr_changed_files_count": pr_changed_count,
        "pr_metadata_used": pr_metadata_used,
        "answer_grounding_mode": grounding_mode,
    }


def _review_async_subsection_contract(entries: list[AuditEntry]) -> dict[str, Any]:
    latest = _latest_for(entries, "review")
    if latest is None:
        return {"status": "not_enough_data", "reason": "review_missing"}
    skip = _skip_meta(latest.audit)
    if skip is not None:
        reason_code, reason_short = skip
        return {
            "status": "skipped",
            "reason": reason_code,
            "skip_reason_short": reason_short,
        }
    rendered = render_review_markdown(
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
        audit_summary=dict(latest.audit),
    )
    ok = (
        (
            "<summary>Changed files</summary>" in rendered
            or "<summary>Evidence and diagnostics</summary>" in rendered
        )
        and "### Async batch orchestration" not in rendered
    )
    return {
        "status": "pass" if ok else "fail",
        "reason": "ok" if ok else "default_output_not_compacted",
    }


def _fix_no_patch_contract(entries: list[AuditEntry]) -> dict[str, Any]:
    latest = _latest_for(entries, "fix")
    if latest is None:
        return {"status": "not_enough_data", "reason": "fix_missing"}
    skip = _skip_meta(latest.audit)
    if skip is not None:
        reason_code, reason_short = skip
        return {
            "status": "skipped",
            "reason": reason_code,
            "skip_reason_short": reason_short,
        }
    generation_result = str(latest.audit.get("patch_generation_result", "n/a") or "n/a")
    validation_result = str(latest.audit.get("patch_validation_result", "n/a") or "n/a")
    if generation_result != "no_patch":
        return {
            "status": "not_applicable",
            "reason": "latest_fix_not_no_patch",
            "patch_generation_result": generation_result,
            "patch_validation_result": validation_result,
        }
    ok = validation_result == "no_patch"
    return {
        "status": "pass" if ok else "fail",
        "reason": "ok" if ok else "invalid_no_patch_validation",
        "patch_generation_result": generation_result,
        "patch_validation_result": validation_result,
    }


def _evidence_context_label_contract_probe() -> dict[str, Any]:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[
            EvidenceItem(file_path="repobrain/github_flow.py", line_start=1, line_end=1, score=0.9),
            EvidenceItem(file_path="tests/test_pr_review.py", line_start=2, line_end=2, score=0.5),
        ],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "pass_count": 1,
            "touched_files": ["repobrain/github_flow.py"],
            "selected": 2,
            "retrieval_snapshot_cache_used": True,
            "retrieval_snapshot_cache_hit": False,
            "retrieval_snapshot_cache_miss_reason": "cache_key_miss",
        },
        next_steps="n/a",
        command="ask",
    )
    changed_present = "[Changed in PR]" in md
    support_class_present = any(
        label in md
        for label in ("[Support context]", "[Test context]", "[Reference]")
    )
    ok = changed_present and support_class_present
    return {
        "status": "pass" if ok else "fail",
        "reason": "ok" if ok else "missing_context_labels",
    }


def _latest_runtime_summary(entries: list[AuditEntry], command: str) -> dict[str, Any]:
    latest = _latest_for(entries, command)
    if latest is None:
        return {"status": "not_enough_data"}
    audit = latest.audit
    summary = {
        "run_id": latest.run_id,
        "path": latest.path,
        "route_final": str(audit.get("route_final", "") or ""),
        "selected": int(audit.get("selected", 0) or 0),
        "retrieved": int(audit.get("retrieved", 0) or 0),
        "snapshot_status": _snapshot_status(audit),
        "snapshot_key_kind": str(audit.get("retrieval_snapshot_cache_key_kind", "not_applicable") or "not_applicable"),
        "snapshot_miss_reason": str(
            audit.get("retrieval_snapshot_cache_miss_reason", "not_applicable") or "not_applicable"
        ),
        "snapshot_age_s": int(audit.get("retrieval_snapshot_cache_age_s", 0) or 0),
        "timings_total_ms": _timing_total_ms(audit),
        "llm_tokens_total": int(audit.get("llm_tokens_total", 0) or 0),
        "embed_tokens_total": int(audit.get("embed_tokens_total", 0) or 0),
        "pr_metadata_used": bool(audit.get("pr_metadata_used", False)),
        "answer_grounding_mode": str(audit.get("answer_grounding_mode", "n/a") or "n/a"),
        "verification_overall": str(audit.get("verification_overall", "n/a") or "n/a"),
    }
    skip = _skip_meta(audit)
    if skip is not None:
        reason_code, reason_short = skip
        summary["status"] = "skipped"
        summary["skip_reason_code"] = reason_code
        summary["skip_reason_short"] = reason_short
        return summary
    summary["status"] = "available"
    return summary


def _status_weight(status: str) -> int:
    normalized = str(status or "").strip().lower()
    if normalized == "fail":
        return 3
    if normalized == "not_enough_data":
        return 2
    if normalized in {"not_applicable", "skipped"}:
        return 1
    return 0


def build_stability_benchmark_payload(*, audit_dir: Path) -> dict[str, Any]:
    return build_stability_benchmark_payload_with_history(
        audit_dir=audit_dir,
        history_path=None,
    )


def build_stability_benchmark_payload_with_history(
    *,
    audit_dir: Path,
    history_path: Path | None,
) -> dict[str, Any]:
    current_entries = _load_audit_entries(audit_dir)
    history_entries = _load_history_entries(history_path) if history_path is not None else []
    combined_entries = _merge_entries(history_entries, current_entries)
    scoped_entries = _scope_entries_to_current_pr(combined_entries, current_entries)
    if history_path is not None:
        _write_history_entries(history_path, combined_entries)

    entries = scoped_entries or current_entries
    scenarios = {
        "ask_snapshot_transition": _transition_for(entries, "ask"),
        "review_snapshot_transition": _transition_for(entries, "review"),
        "ask_truth_binding_contract": _ask_truth_binding_contract(entries),
        "review_async_subsection_contract": _review_async_subsection_contract(entries),
        "fix_no_patch_contract": _fix_no_patch_contract(entries),
        "evidence_context_label_contract": _evidence_context_label_contract_probe(),
    }
    overall_status = "pass"
    for scenario in scenarios.values():
        status = str(scenario.get("status", "not_enough_data") or "not_enough_data")
        if _status_weight(status) > _status_weight(overall_status):
            overall_status = status
    return {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "audit_dir": audit_dir.as_posix(),
        "history_path": history_path.as_posix() if history_path is not None else "disabled",
        "history_entries_loaded": len(history_entries),
        "audit_files_current_run": len(current_entries),
        "audit_files_scanned": len(entries),
        "overall_status": overall_status,
        "scenarios": scenarios,
        "latest": {
            "ask": _latest_runtime_summary(entries, "ask"),
            "review": _latest_runtime_summary(entries, "review"),
            "fix": _latest_runtime_summary(entries, "fix"),
        },
    }


def _status_label(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "pass":
        return "PASS"
    if normalized == "fail":
        return "FAIL"
    if normalized == "skipped":
        return "SKIPPED"
    if normalized == "not_applicable":
        return "N/A"
    return "NEEDS_DATA"


def build_stability_benchmark_markdown(payload: dict[str, Any]) -> str:
    scenarios = payload.get("scenarios", {})
    if not isinstance(scenarios, dict):
        scenarios = {}

    def _scenario_line(name: str, key: str) -> str:
        scenario_raw = scenarios.get(key, {})
        scenario = dict(scenario_raw) if isinstance(scenario_raw, dict) else {}
        status = str(scenario.get("status", "not_enough_data") or "not_enough_data")
        line = f"- {name}: **{_status_label(status)}**"
        reason = str(scenario.get("reason", "") or "").strip()
        if reason and reason != "ok":
            line += f" (`{reason}`)"
        return line

    latest_raw = payload.get("latest", {})
    latest = dict(latest_raw) if isinstance(latest_raw, dict) else {}
    lines = [
        "# RepoBrain Stability Benchmark",
        "",
        f"- Overall status: **{_status_label(str(payload.get('overall_status', 'not_enough_data')))}**",
        f"- Generated (UTC): `{str(payload.get('generated_at_utc', 'n/a') or 'n/a')}`",
        f"- Audit files scanned: `{int(payload.get('audit_files_scanned', 0) or 0)}`",
        "",
        "## Scenario checks",
        _scenario_line("Ask snapshot transition (miss -> hit)", "ask_snapshot_transition"),
        _scenario_line("Review snapshot transition (miss -> hit)", "review_snapshot_transition"),
        _scenario_line("Ask truth-binding contract", "ask_truth_binding_contract"),
        _scenario_line("Review async subsection contract", "review_async_subsection_contract"),
        _scenario_line("Fix safe no_patch contract", "fix_no_patch_contract"),
        _scenario_line("Evidence context label contract", "evidence_context_label_contract"),
        "",
        "## Latest runtime summary",
    ]
    for command in ("ask", "review", "fix"):
        summary_raw = latest.get(command, {})
        summary = dict(summary_raw) if isinstance(summary_raw, dict) else {}
        if summary.get("status") == "skipped":
            lines.extend(
                [
                    f"### {command.upper()}",
                    f"- Skipped: `{summary.get('skip_reason_code', 'skipped')}`",
                    f"- Reason: {summary.get('skip_reason_short', 'n/a')}",
                    "",
                ]
            )
            continue
        if summary.get("status") != "available":
            lines.extend([f"### {command.upper()}", "- No data.", ""])
            continue
        lines.extend(
            [
                f"### {command.upper()}",
                f"- Run id: `{summary.get('run_id', 'n/a')}`",
                f"- Snapshot status: `{summary.get('snapshot_status', 'not_applicable')}`",
                f"- Route: `{summary.get('route_final', 'n/a')}`",
                f"- Selected evidence: `{int(summary.get('selected', 0) or 0)}`",
                f"- Retrieved candidates: `{int(summary.get('retrieved', 0) or 0)}`",
                f"- Timing total (ms): `{float(summary.get('timings_total_ms', 0.0) or 0.0):.3f}`",
                f"- LLM tokens total: `{int(summary.get('llm_tokens_total', 0) or 0)}`",
                f"- Embeddings tokens total: `{int(summary.get('embed_tokens_total', 0) or 0)}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_stability_benchmark_artifacts(
    *,
    audit_dir: Path,
    output_json_path: Path,
    output_markdown_path: Path,
    history_path: Path | None = None,
) -> dict[str, Any]:
    payload = build_stability_benchmark_payload_with_history(
        audit_dir=audit_dir,
        history_path=history_path,
    )
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    output_markdown_path.write_text(build_stability_benchmark_markdown(payload), encoding="utf-8")
    return payload
