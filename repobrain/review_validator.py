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


def _severity_from_message(message: str) -> str:
    lowered = str(message or "").strip().lower()
    if any(token in lowered for token in _HIGH_SEVERITY_HINTS):
        return "high"
    if any(token in lowered for token in _MEDIUM_SEVERITY_HINTS):
        return "medium"
    return "low"


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


def validate_review_findings(review: dict[str, Any]) -> dict[str, Any]:
    """Validate review findings so severe claims are evidence-backed."""
    risk_items = _collect_risk_items(review)
    confirmed_findings: list[str] = []
    possible_signals: list[str] = []
    recommendations_raw = review.get("suggested_tests", review.get("next_steps", []))
    recommendations = (
        [str(item).strip() for item in recommendations_raw if str(item).strip()]
        if isinstance(recommendations_raw, list)
        else []
    )

    for item in risk_items:
        message = str(item.get("message", "") or "").strip()
        if not message:
            continue
        severity = str(item.get("severity", "low") or "low").lower()
        evidence_raw = item.get("evidence", [])
        evidence = evidence_raw if isinstance(evidence_raw, list) else []
        has_evidence = any(isinstance(entry, dict) and str(entry.get("path", "")).strip() for entry in evidence)

        if severity == "high" and not has_evidence:
            possible_signals.append(f"{message} (downgraded: missing evidence)")
            continue
        if severity == "medium" and not has_evidence and "no obvious high-risk" not in message.lower():
            possible_signals.append(f"{message} (signal: verify evidence)")
            continue
        confirmed_findings.append(message)

    if any(_severity_from_message(item) == "high" for item in confirmed_findings):
        risk_level = "high"
    elif any(_severity_from_message(item) == "medium" for item in confirmed_findings):
        risk_level = "medium"
    elif possible_signals:
        risk_level = "medium"
    else:
        risk_level = "low"

    if not confirmed_findings:
        if possible_signals:
            confirmed_findings = ["No confirmed high-risk findings (signals require manual verification)."]
        else:
            confirmed_findings = ["No obvious high-risk patterns detected"]

    validated = dict(review)
    validated["summary_text"] = _compose_summary_text(
        str(review.get("summary_text", "")),
        risk_level,
    )
    validated["risk_level"] = risk_level
    validated["confirmed_findings"] = confirmed_findings
    validated["possible_signals"] = possible_signals
    validated["recommendations"] = recommendations
    # Backward-compatible output fields.
    validated["risks"] = confirmed_findings
    notes_raw = review.get("notes", [])
    notes = [str(item).strip() for item in notes_raw if str(item).strip()] if isinstance(notes_raw, list) else []
    notes.extend(possible_signals)
    validated["notes"] = list(dict.fromkeys(notes))
    validated["validation"] = {
        "confirmed_findings_count": len(confirmed_findings),
        "possible_signals_count": len(possible_signals),
        "risk_level": risk_level,
    }
    return validated

