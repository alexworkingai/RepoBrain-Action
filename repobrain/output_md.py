from __future__ import annotations

import os
from typing import Any

from repobrain.evidence import EvidenceItem
from repobrain.links import make_line_link

MAX_COMMENT_BYTES = 60 * 1024


def _audit_note() -> str:
    if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true":
        return "Audit: workflow artifact `repobrain-audit` (hash-only)."
    return "Audit: local run (no workflow artifacts)."


def _route(audit_summary: dict[str, Any]) -> str:
    route = str(audit_summary.get("route_final", audit_summary.get("route", "FAST")) or "FAST")
    route = route.strip().upper()
    return route or "FAST"


def _evidence_lines(
    evidence: list[EvidenceItem],
    *,
    repo: str | None,
    sha: str | None,
) -> list[str]:
    if not evidence:
        return ["- No source locators selected."]
    return [
        f"- {make_line_link(repo, sha, item.file_path, item.line_start, item.line_end)} "
        f"(score={item.score:.4f})"
        for item in evidence
    ]


def _verification_lines(audit_summary: dict[str, Any]) -> list[str]:
    p = int(audit_summary.get("verification_pass_count", 0) or 0)
    f = int(audit_summary.get("verification_fail_count", 0) or 0)
    q = int(audit_summary.get("verification_pending_count", 0) or 0)
    n = int(audit_summary.get("verification_not_run_count", 0) or 0)

    if f > 0:
        status = "WARN"
    elif q > 0:
        status = "WARN"
    elif p > 0 and n == 0:
        status = "PASS"
    else:
        status = "NOT_RUN"

    lines = [
        "### 🔎 Verification",
        f"- Status: **{status}**",
        f"- PASS: {p}, WARN: {f + q}, NOT_RUN: {n}",
    ]
    if status == "NOT_RUN" or n > 0:
        lines.append("- checks were not run.")
    return lines


def _verification_report_lines(verification_report: dict[str, Any]) -> list[str]:
    checks = verification_report.get("checks", [])
    if not isinstance(checks, list):
        checks = []
    trusted = bool(verification_report.get("trusted_context", False))
    dynamic = bool(verification_report.get("dynamic_allowed", False))
    lines = [
        "### 🔎 Verification",
        f"- Summary: {verification_report.get('summary', 'Verification not available')}",
        f"- trusted_context: {int(trusted)}",
        f"- dynamic_verify: {int(dynamic)}",
    ]
    for item in checks[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "check"))
        status = str(item.get("status", "NOT_RUN"))
        reason = str(item.get("reason", "n/a"))
        lines.append(f"- `{name}`: {status} ({reason})")
    return lines


def _llm_lines(audit_summary: dict[str, Any]) -> list[str]:
    llm_used = bool(audit_summary.get("llm_used", False))
    skip_reason = str(audit_summary.get("llm_skip_reason", "n/a") or "n/a")
    model_id = str(audit_summary.get("llm_model_used", "not used") or "not used")
    prompt = int(audit_summary.get("llm_tokens_prompt", 0) or 0)
    completion = int(audit_summary.get("llm_tokens_completion", 0) or 0)
    total = int(audit_summary.get("llm_tokens_total", 0) or 0)
    usage_estimated = bool(audit_summary.get("llm_usage_estimated", False))
    remaining = audit_summary.get(
        "llm_remaining_requests",
        audit_summary.get("llm_requests_remaining", "n/a"),
    )
    remaining_is_estimate = bool(
        audit_summary.get("llm_remaining_is_estimate", audit_summary.get("llm_remaining_estimated", False))
    )
    reset_raw = audit_summary.get(
        "llm_reset_time_utc_iso",
        audit_summary.get("llm_rate_limit_reset", None),
    )
    reset_value = str(reset_raw) if reset_raw not in {None, ""} else "n/a"
    input_budget_used = int(audit_summary.get("llm_input_budget_used_est", 0) or 0)
    input_budget_limit = int(audit_summary.get("llm_input_budget_limit", 0) or 0)
    dropped_locators = int(audit_summary.get("llm_dropped_locators_count", 0) or 0)
    dropped_hunks = int(audit_summary.get("llm_dropped_hunks_count", 0) or 0)
    dropped_snippets = int(audit_summary.get("llm_dropped_snippets_count", 0) or 0)
    return [
        "### 🤖 LLM",
        (
            "- LLM used: yes"
            if llm_used
            else f"- LLM used: no ({skip_reason})"
        ),
        f"- LLM model used: `{model_id}`",
        (
            f"- Tokens used: prompt={prompt} completion={completion} total={total} "
            f"({'estimate' if usage_estimated else 'reported'})"
        ),
        (
            f"- Requests remaining today: {remaining}"
            f"{' (estimated)' if remaining_is_estimate else ''}"
        ),
        f"- Reset time UTC: {reset_value}",
        f"- Prompt budget: used~{input_budget_used} / limit={input_budget_limit}",
        (
            "- Dropped context items: "
            f"locators={dropped_locators}, hunks={dropped_hunks}, snippets={dropped_snippets}"
        ),
    ]


def _mode_lines(audit_summary: dict[str, Any]) -> list[str]:
    route = _route(audit_summary)
    pass_count = int(audit_summary.get("pass_count", 1) or 1)
    lines = [f"- Route/Mode: `{route}`", f"- Passes: `{pass_count}`"]
    if route == "DEEP" or pass_count > 1:
        lines.append("- Deep retrieval pass was used.")
    return lines


def _touched_files_lines(audit_summary: dict[str, Any]) -> list[str]:
    raw = audit_summary.get("touched_files", [])
    if not isinstance(raw, list):
        return []
    files = [str(item).strip() for item in raw if str(item).strip()]
    if not files:
        return []
    files = sorted(set(files))
    lines = ["", "Touched files:"]
    for path in files[:10]:
        lines.append(f"- `{path}`")
    if len(files) > 10:
        lines.append(f"- +{len(files) - 10} more")
    return lines


def _audit_kv_lines(audit_summary: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in sorted(audit_summary):
        value = audit_summary[key]
        if isinstance(value, list):
            lines.append(f"- {key}: list[{len(value)}]")
            continue
        if isinstance(value, dict):
            lines.append(f"- {key}: dict[{len(value)}]")
            continue
        lines.append(f"- {key}: {value}")
    return lines


def enforce_comment_limit(
    md: str,
    *,
    max_bytes: int = MAX_COMMENT_BYTES,
) -> tuple[str, bool]:
    if len(md.encode("utf-8")) <= max_bytes:
        return md, False
    lines = md.splitlines()
    kept = lines[:24]
    kept.extend(
        [
            "",
            "_Output truncated to keep GitHub comment size safe._",
            "_See workflow artifacts/logs for full details._",
        ]
    )
    return "\n".join(kept), True


def render_answer_markdown(
    *,
    answer_text: str,
    evidence: list[EvidenceItem],
    audit_summary: dict[str, Any],
    next_steps: str,
    command: str,
    repo: str | None = None,
    sha: str | None = None,
) -> str:
    route = _route(audit_summary)
    evidence_block = _evidence_lines(evidence, repo=repo, sha=sha)
    route_header = "### ✅ Answer"
    if route == "WAIT":
        route_header = "### ⏳ Needs verification"
    elif route == "REFUSE":
        route_header = "### 🚫 Refused"
    elif route == "BLOCK":
        route_header = "### 🛑 Blocked"

    sections: list[str] = [route_header]
    if command == "locate":
        sections.extend(
            [
                "Top locations found for the query:",
                "",
                "### 📌 Evidence",
                *evidence_block,
                "",
                *_verification_lines(audit_summary),
                "",
                *_llm_lines(audit_summary),
                "",
                "### 🧭 Route details",
                *_mode_lines(audit_summary),
            ]
        )
    else:
        sections.extend(
            [
                answer_text.strip() or "No answer generated.",
                "",
                "### 📌 Evidence (What I used)",
                *evidence_block,
                *_touched_files_lines(audit_summary),
                "",
                *_verification_lines(audit_summary),
                "",
                *_llm_lines(audit_summary),
                "",
                "### 🧭 Route details",
                *_mode_lines(audit_summary),
                "",
                "### ✅ Next steps",
                f"- {next_steps.strip() or 'Open evidence links and verify logic'}",
            ]
        )

    sections.extend(
        [
            "",
            "### 🧾 Audit summary",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            f"- top_score: {audit_summary.get('top_score', 'n/a')}",
            *_audit_kv_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )
    return "\n".join(sections)


def render_wait_markdown(
    *,
    reason: str,
    audit_summary: dict[str, Any],
) -> str:
    md = "\n".join(
        [
            "### ⏳ Needs verification",
            reason or "Verification is pending.",
            "",
            "### 🔎 Verification",
            "- Status: **NOT_RUN**",
            "- checks were not run.",
            "",
            *_llm_lines(audit_summary),
            "",
            "### 🧭 Route details",
            "- Route/Mode: `WAIT`",
            "- Passes: `1`",
            "",
            "### 🧾 Audit summary",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            "",
            _audit_note(),
        ]
    )
    return md


def render_refuse_markdown(
    *,
    reason: str,
    audit_summary: dict[str, Any],
    blocked: bool = False,
) -> str:
    title = "### 🛑 Blocked" if blocked else "### 🚫 Refused"
    md = "\n".join(
        [
            title,
            reason or "Request was refused by policy.",
            "",
            "### ✅ What you can ask instead",
            "- `/repobrain ask Где реализована логика TKYProvider?`",
            "- `/repobrain locate TKYProvider`",
            "- `/repobrain explain two-pass retrieval logic`",
            "",
            "### 🔎 Verification",
            "- Status: **NOT_RUN**",
            "- checks were not run.",
            "",
            *_llm_lines(audit_summary),
            "",
            "### 🧾 Audit summary",
            f"- route: {_route(audit_summary)}",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            "",
            _audit_note(),
        ]
    )
    return md


def render_error_markdown(
    *,
    message: str,
    audit_summary: dict[str, Any],
) -> str:
    md = "\n".join(
        [
            "### 🛑 Error",
            message.strip() or "Unexpected error.",
            "",
            *_llm_lines(audit_summary),
            "",
            "### 🧾 Audit summary",
            f"- route: {_route(audit_summary)}",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            "",
            _audit_note(),
        ]
    )
    return md


def render_review_markdown(
    *,
    review: dict[str, Any],
    verification_report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    files_block = review.get("files_block", [])
    if not isinstance(files_block, list):
        files_block = []
    risks = review.get("risks", [])
    if not isinstance(risks, list):
        risks = []
    notes = review.get("notes", [])
    if not isinstance(notes, list):
        notes = []
    summary_text = str(review.get("summary_text", "No summary available.")).strip()
    risk_level = str(review.get("risk_level", "low") or "low").upper()
    sections = [
        "### ✅ PR Review",
        f"TL;DR: {summary_text}",
        f"Risk level: **{risk_level}**",
        "",
        "### 🗂️ Touched files",
        *(files_block[:10] if files_block else ["- No changed files detected."]),
        *([f"- +{len(files_block) - 10} more"] if len(files_block) > 10 else []),
        "",
        "### ⚠️ Findings",
        *([f"- {item}" for item in risks] if risks else ["- No high-risk findings detected."]),
        *([f"- Note: {item}" for item in notes[:5]] if notes else []),
        "",
        *_verification_report_lines(verification_report),
        "",
        *_llm_lines(audit_summary),
        "",
        "### 🧭 Route details",
        *_mode_lines(audit_summary),
        "",
        "### 🧾 Audit summary",
        *_audit_kv_lines(audit_summary),
        "",
        _audit_note(),
    ]
    return "\n".join(sections)


def render_patch_markdown(
    *,
    review: dict[str, Any],
    verification_report: dict[str, Any],
    patch_snippet: str,
    patch_written: bool,
    patch_apply_message: str,
    audit_summary: dict[str, Any],
) -> str:
    summary_text = str(review.get("summary_text", "Patch suggestion flow")).strip()
    sections = [
        "### 🛠️ Patch proposal",
        f"Summary: {summary_text}",
        "",
        "### 📦 Patch artifact",
        "- Full patch is saved to `artifacts/patch.diff`." if patch_written else "- No patch generated.",
        f"- Apply status: {patch_apply_message}",
        "",
        "### 🧩 Patch snippet",
        "```diff",
        patch_snippet.strip() or "# no patch generated",
        "```",
        "",
        *_verification_report_lines(verification_report),
        "",
        *_llm_lines(audit_summary),
        "",
        "### 🧾 Audit summary",
        *_audit_kv_lines(audit_summary),
        "",
        _audit_note(),
    ]
    return "\n".join(sections)
