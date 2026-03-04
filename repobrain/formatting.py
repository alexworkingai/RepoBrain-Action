from __future__ import annotations

import os

from .evidence import EvidenceItem
from .links import make_line_link


def _audit_artifact_note() -> str:
    if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true":
        return "Audit: workflow artifact `repobrain-audit` (hash-only)."
    return "Audit: local run (no workflow artifacts)."


def _format_audit_summary(audit_summary: dict[str, object]) -> list[str]:
    audit_lines = [f"- `{key}`: {value}" for key, value in audit_summary.items()]
    return audit_lines or ["- No audit data."]


def _build_tky_status_line(audit_summary: dict[str, object]) -> str:
    fallback_raw = audit_summary.get("fallback_reason_code", None)
    fallback_code = str(fallback_raw).strip() if fallback_raw is not None else ""
    has_fallback = bool(fallback_code) and fallback_code.lower() not in {"n/a", "none", "null"}
    mode_used = str(audit_summary.get("tky_mode_used", "n/a") or "n/a").strip().lower()
    engine = str(audit_summary.get("tky_engine", "n/a") or "n/a").strip().lower()
    remote_used = bool(audit_summary.get("remote_used", False))

    if engine == "remote" and remote_used:
        return "TKY: remote (ok)"
    if engine == "baseline" and has_fallback:
        return f"TKY: fallback baseline ({fallback_code})"
    if mode_used == "fallback_baseline" and has_fallback:
        return f"TKY: fallback baseline ({fallback_code})"
    if mode_used == "fallback_baseline":
        return "TKY: fallback baseline (fallback)"
    if engine == "topocore_v5":
        return "TKY: topocore_v5"
    if engine == "topocore_lite":
        return "TKY: topocore_lite"
    if engine == "topocore_original":
        return "TKY: topocore_original"
    if engine == "topocore_local":
        return "TKY: topocore_local"
    if engine == "baseline":
        return "TKY: baseline"
    if mode_used == "remote" and remote_used:
        return "TKY: remote (ok)"
    if mode_used == "local":
        return "TKY: topocore_lite"
    if mode_used == "baseline":
        return "TKY: baseline"
    if has_fallback:
        return f"TKY: fallback baseline ({fallback_code})"
    return "TKY: n/a"


def _build_remote_skip_hint(audit_summary: dict[str, object]) -> str | None:
    reason = str(audit_summary.get("remote_skipped_reason", "n/a") or "n/a").strip().lower()
    if reason == "remote_url_missing":
        return (
            "Remote skipped: remote_url missing "
            "(set it via workflow input or tky.remote_url for stub tests)."
        )
    return None


def _format_evidence_lines(
    evidence: list[EvidenceItem],
    *,
    repo: str | None,
    sha: str | None,
) -> list[str]:
    if not evidence:
        return ["- No evidence selected."]
    return [
        f"- {make_line_link(repo, sha, item.file_path, item.line_start, item.line_end)} "
        f"(score={item.score:.4f})"
        for item in evidence
    ]


def format_github_comment(
    answer_text: str,
    evidence: list[EvidenceItem],
    audit_summary: dict[str, object],
    next_steps: str,
    *,
    command: str = "ask",
    repo: str | None = None,
    sha: str | None = None,
) -> str:
    """Format a GitHub-style markdown comment for ask/locate/explain commands."""
    evidence_lines = _format_evidence_lines(evidence, repo=repo, sha=sha)
    route_value = str(audit_summary.get("route_final", audit_summary.get("route", ""))).strip()
    mode_line = f"Mode: {route_value}" if route_value else ""

    if command == "locate":
        remote_hint = _build_remote_skip_hint(audit_summary)
        sections = [
            "### 📌 Evidence",
            *evidence_lines,
            "",
            "### 🧾 Audit summary",
            f"- {_build_tky_status_line(audit_summary)}",
            *([f"- {remote_hint}"] if remote_hint else []),
            *_format_audit_summary(audit_summary),
            "",
            _audit_artifact_note(),
        ]
        return "\n".join(sections)

    sections = ["### ✅ Answer"]
    remote_hint = _build_remote_skip_hint(audit_summary)
    if mode_line:
        sections.append(mode_line)
    sections.extend(
        [
            answer_text.strip() or "No answer generated.",
            "",
            "### 📌 Evidence",
            *evidence_lines,
            "",
            "### ✅ Next steps",
            f"- {next_steps.strip() or 'Open evidence links and verify logic'}",
            "",
            "### 🧾 Audit summary",
            f"- {_build_tky_status_line(audit_summary)}",
            *([f"- {remote_hint}"] if remote_hint else []),
            *_format_audit_summary(audit_summary),
            "",
            _audit_artifact_note(),
        ]
    )
    return "\n".join(sections)


def format_pr_review_comment(review: dict[str, object]) -> str:
    """Format a PR review markdown comment from `repobrain.review.build_pr_review` output."""
    summary_text = str(review.get("summary_text", "")).strip() or "No summary available."
    risk_level = str(review.get("risk_level", "low")).strip().lower() or "low"
    files_block = list(review.get("files_block", []))
    risks = list(review.get("risks", []))
    suggested_tests = list(review.get("suggested_tests", review.get("next_steps", [])))
    notes = list(review.get("notes", []))
    audit_summary = dict(review.get("audit_summary", {}))

    file_lines = files_block or ["- No changed files detected."]
    risk_lines = [f"- {item}" for item in risks] or ["- No obvious risks detected."]
    test_lines = [f"- {item}" for item in suggested_tests] or ["- Run checks and review changes."]
    impact_lines = [f"- {item}" for item in notes] or ["- No additional impact notes."]

    risk_badge = {
        "high": "🔴 HIGH",
        "medium": "🟠 MEDIUM",
        "low": "🟢 LOW",
    }.get(risk_level, f"⚪ {risk_level.upper()}")

    sections = [
        "### ✅ PR Review",
        "",
        f"TL;DR: {summary_text}  \nRisk level: **{risk_badge}**",
        "",
        "### 🗂️ Files changed",
        *file_lines,
        "",
        "### ⚠️ Risks",
        *risk_lines,
        "",
        "### ✅ Suggested tests",
        *test_lines,
        "",
        "### 🧭 Impact map",
        *impact_lines,
        "",
        "### 🧾 Audit summary",
        *_format_audit_summary(audit_summary),
        "",
        _audit_artifact_note(),
    ]
    return "\n".join(sections)


def format_refusal_comment(
    *,
    reason: str,
    audit_summary: dict[str, object],
) -> str:
    """Format a safe refusal response for blocked requests."""
    sections = [
        "### ⛔️ Request blocked",
        reason or "This request looks like a prompt-injection or exfiltration attempt.",
        "",
        "### ✅ What you can ask instead",
        "- `/repobrain ask Где реализована логика TKYProvider?`",
        "- `/repobrain locate BaselineTKYProvider`",
        "- `/repobrain explain retrieve_adaptive`",
        "- `/repobrain review` (in a PR discussion)",
        "",
        "### 🧾 Audit summary",
        *_format_audit_summary(audit_summary),
        "",
        _audit_artifact_note(),
    ]
    return "\n".join(sections)


def format_verify_comment(report: dict[str, object]) -> str:
    """Format a PR verification report based on GitHub checks/status APIs."""
    state = str(report.get("state", "unknown")).lower()
    message = str(report.get("message", "")).strip()
    total = int(report.get("total", 0) or 0)
    success = int(report.get("success", 0) or 0)
    failure = int(report.get("failure", 0) or 0)
    pending = int(report.get("pending", 0) or 0)
    neutral = int(report.get("neutral", 0) or 0)
    failures = list(report.get("failures", []))
    verify_source = str(report.get("verify_source", "none") or "none")
    sources = report.get("sources", {})
    if not isinstance(sources, dict):
        sources = {}

    status_icon = {
        "success": "✅",
        "pending": "🟡",
        "failure": "❌",
    }.get(state, "❔")

    failing_lines: list[str] = []
    for item in failures:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "Unnamed check"))
        conclusion = str(item.get("conclusion", "failure"))
        details_url = item.get("details_url")
        if isinstance(details_url, str) and details_url.strip():
            label = f"`{name}` ({conclusion})"
            failing_lines.append(f"- [{label}]({details_url})")
        else:
            failing_lines.append(f"- `{name}` ({conclusion})")

    if state == "pending":
        next_steps = ["Wait for checks to finish, then run `/repobrain verify` again."]
    elif state == "failure":
        next_steps = ["Open failing checks, fix issues, push changes, then verify again."]
    elif state == "success":
        next_steps = ["Looks good; proceed with review or merge when ready."]
    else:
        next_steps = ["No checks/statuses detected yet. Re-run `/repobrain verify` later."]

    audit_summary = {
        "route": "VERIFY",
        "checks_total": total,
        "checks_failure": failure,
        "checks_pending": pending,
        "verify_source": verify_source,
    }

    sections = [
        "### ✅ Verification report",
        f"Status: {status_icon} `{state}`",
        "",
    ]
    if message:
        sections.extend([message, ""])

    sections.extend(
        [
            f"- Total checks: {total}",
            f"- Success: {success}",
            f"- Failure: {failure}",
            f"- Pending: {pending}",
            f"- Neutral/Skipped: {neutral}",
        ]
    )
    if failing_lines:
        sections.extend(["", "Failing checks:", *failing_lines])

    sections.extend(
        [
            "",
            "### 🧩 Sources",
            f"- checks: {sources.get('checks', 'empty')}",
            f"- statuses: {sources.get('statuses', 'empty')}",
            f"- workflow_runs: {sources.get('workflow_runs', 'empty')}",
        ]
    )

    sections.extend(
        [
            "",
            "### ✅ Next steps",
            *[f"- {line}" for line in next_steps],
            "",
            "### 🧾 Audit summary",
            *_format_audit_summary(audit_summary),
            "",
            _audit_artifact_note(),
        ]
    )
    return "\n".join(sections)
