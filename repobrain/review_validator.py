from __future__ import annotations

from typing import Any


_HIGH_SEVERITY_HINTS = (
    "secret leakage",
    "merge conflict markers",
    "security-sensitive area changed",
)

_MEDIUM_SEVERITY_HINTS = (
    "ci/cd changed",
    "dependencies changed",
    "checks",
    "todo",
    "fixme",
)

_RISK_DRIVER_HINTS = (
    "security-sensitive area changed",
    "ci/cd changed: verify workflows",
    "dependencies changed: verify install and tests",
)


def _severity_from_message(message: str) -> str:
    lowered = str(message or "").strip().lower()
    if any(token in lowered for token in _HIGH_SEVERITY_HINTS):
        return "high"
    if any(token in lowered for token in _MEDIUM_SEVERITY_HINTS):
        return "medium"
    return "low"


def _canonical_message(message: str) -> str:
    return " ".join(str(message or "").strip().split())


def _collect_evidence_paths(evidence: list[dict[str, str]]) -> list[str]:
    paths = [str(item.get("path", "")).strip() for item in evidence if str(item.get("path", "")).strip()]
    return sorted(set(paths))


def _collect_risk_items(review: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = review.get("risk_items", [])
    if isinstance(raw_items, list) and raw_items:
        out: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            message = str(item.get("message", "") or "").strip()
            if not message:
                continue
            severity = str(item.get("severity", "") or "").strip().lower() or _severity_from_message(message)
            evidence_raw = item.get("evidence", [])
            evidence: list[dict[str, str]] = []
            if isinstance(evidence_raw, list):
                for ev in evidence_raw:
                    if isinstance(ev, dict):
                        path = str(ev.get("path", "") or "").strip()
                        kind = str(ev.get("kind", "") or "").strip() or "evidence"
                        source = str(ev.get("source", "") or "").strip() or "unknown"
                        if path:
                            evidence.append({"path": path, "kind": kind, "source": source})
            out.append({"message": message, "severity": severity, "evidence": evidence})
        if out:
            return out

    # Fallback for older review payloads without structured risk items.
    risks_raw = review.get("risks", [])
    out: list[dict[str, Any]] = []
    if isinstance(risks_raw, list):
        for message_raw in risks_raw:
            message = str(message_raw or "").strip()
            if not message:
                continue
            out.append(
                {
                    "message": message,
                    "severity": _severity_from_message(message),
                    "evidence": [],
                }
            )
    return out


def _is_risk_driver_message(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return any(token in lowered for token in _RISK_DRIVER_HINTS)


def _compose_summary_text(base_summary: str, risk_level: str) -> str:
    summary = str(base_summary or "").strip()
    if not summary:
        return f"Validated risk: {risk_level.upper()}."
    lowered = summary.lower()
    if risk_level == "high" and "low risk" in lowered:
        return summary.replace("low risk", "high risk")
    if risk_level == "low" and "high risk" in lowered:
        return summary.replace("high risk", "low risk")
    return summary


def _aggregate_risk_items(risk_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for item in risk_items:
        message = _canonical_message(str(item.get("message", "") or ""))
        if not message:
            continue
        severity = str(item.get("severity", "low") or "low").strip().lower()
        if severity not in {"low", "medium", "high"}:
            severity = _severity_from_message(message)
        evidence_raw = item.get("evidence", [])
        evidence = evidence_raw if isinstance(evidence_raw, list) else []
        key = (severity, message.lower())
        bucket = merged.setdefault(
            key,
            {
                "message": message,
                "severity": severity,
                "evidence_paths": set(),
            },
        )
        for path in _collect_evidence_paths(evidence):
            bucket["evidence_paths"].add(path)

    out: list[dict[str, Any]] = []
    for key in sorted(merged, key=lambda item: (item[0], item[1])):
        item = merged[key]
        paths = sorted(path for path in item["evidence_paths"] if path)
        out.append(
            {
                "message": str(item["message"]),
                "severity": str(item["severity"]),
                "evidence_paths": paths,
                "evidence_count": len(paths),
            }
        )
    return out


def validate_review_findings(review: dict[str, Any]) -> dict[str, Any]:
    """Validate review findings so severe claims are evidence-backed."""
    risk_items = _collect_risk_items(review)
    aggregated_risks = _aggregate_risk_items(risk_items)
    confirmed_findings: list[str] = []
    confirmed_risk_entries: list[dict[str, Any]] = []
    possible_signals: list[str] = []
    risk_drivers: list[str] = []
    risk_driver_severities: list[str] = []
    recommendations_raw = review.get("suggested_tests", review.get("next_steps", []))
    recommendations = (
        [str(item).strip() for item in recommendations_raw if str(item).strip()]
        if isinstance(recommendations_raw, list)
        else []
    )

    for item in aggregated_risks:
        message = _canonical_message(str(item.get("message", "") or ""))
        if not message:
            continue
        severity = str(item.get("severity", "low") or "low").lower()
        evidence_paths = [str(path).strip() for path in item.get("evidence_paths", []) if str(path).strip()]
        has_evidence = bool(evidence_paths)
        lowered = message.lower()

        if severity == "high" and not has_evidence:
            possible_signals.append(f"{message} (downgraded: missing evidence)")
            continue
        if lowered.startswith("possible "):
            possible_signals.append(f"{message} (signal: heuristic wording)")
            continue
        if severity in {"medium", "high"} and not has_evidence and "no obvious high-risk" not in lowered:
            possible_signals.append(f"{message} (signal: verify evidence)")
            continue
        if _is_risk_driver_message(message):
            risk_drivers.append(message)
            risk_driver_severities.append(severity)
            continue
        evidence_suffix = f" (evidence: {len(evidence_paths)} file(s))" if evidence_paths else ""
        confirmed_findings.append(f"{message}{evidence_suffix}")
        confirmed_risk_entries.append(
            {
                "message": message,
                "severity": severity,
                "evidence_paths": evidence_paths,
            }
        )

    if any(str(item.get("severity", "low")) == "high" for item in confirmed_risk_entries):
        risk_level = "high"
    elif any(item == "high" for item in risk_driver_severities):
        risk_level = "high"
    elif any(str(item.get("severity", "low")) == "medium" for item in confirmed_risk_entries):
        risk_level = "medium"
    elif any(item == "medium" for item in risk_driver_severities):
        risk_level = "medium"
    elif possible_signals:
        risk_level = "medium"
    else:
        risk_level = "low"

    risk_drivers = list(dict.fromkeys(risk_drivers))
    for item in confirmed_risk_entries:
        if str(item.get("severity", "low")) == "high":
            risk_drivers.append(str(item.get("message", "")))
    if not risk_drivers:
        for item in confirmed_risk_entries:
            if str(item.get("severity", "low")) == "medium":
                risk_drivers.append(str(item.get("message", "")))
                if len(risk_drivers) >= 3:
                    break
    if not risk_drivers:
        risk_drivers.extend(signal for signal in possible_signals[:3])
    risk_drivers = list(dict.fromkeys(item for item in risk_drivers if item))

    validated = dict(review)
    validated["summary_text"] = _compose_summary_text(
        str(review.get("summary_text", "")),
        risk_level,
    )
    validated["risk_level"] = risk_level
    validated["confirmed_findings"] = confirmed_findings
    validated["possible_signals"] = list(dict.fromkeys(possible_signals))
    validated["recommendations"] = recommendations
    validated["risk_drivers"] = risk_drivers
    validated["confirmed_risk_items"] = confirmed_risk_entries
    # Backward-compatible output fields.
    validated["risks"] = confirmed_findings
    notes_raw = review.get("notes", [])
    informational_notes = (
        [str(item).strip() for item in notes_raw if str(item).strip()]
        if isinstance(notes_raw, list)
        else []
    )
    validated["notes"] = list(dict.fromkeys(informational_notes))
    validated["informational_notes"] = list(dict.fromkeys(informational_notes))
    validated["validation"] = {
        "confirmed_findings_count": len(confirmed_findings),
        "possible_signals_count": len(validated["possible_signals"]),
        "informational_notes_count": len(validated["informational_notes"]),
        "risk_drivers_count": len(validated["risk_drivers"]),
        "risk_level": risk_level,
        "risk_drivers": risk_drivers,
    }
    return validated
