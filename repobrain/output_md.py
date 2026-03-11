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
    passed = int(audit_summary.get("verification_pass_count", 0) or 0)
    failed = int(audit_summary.get("verification_fail_count", 0) or 0)
    pending = int(audit_summary.get("verification_pending_count", 0) or 0)
    not_run = int(audit_summary.get("verification_not_run_count", 0) or 0)

    if failed > 0 or pending > 0:
        status = "WARN"
    elif passed > 0 and not_run == 0:
        status = "PASS"
    else:
        status = "NOT_RUN"

    lines = [
        "### 🔎 Verification",
        f"- Status: **{status}**",
        f"- PASS: {passed}, WARN: {failed + pending}, NOT_RUN: {not_run}",
    ]
    if status == "NOT_RUN" or not_run > 0:
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
    execution_mode = str(audit_summary.get("execution_mode", "retrieval_only") or "retrieval_only")
    tkya_decision = "used" if execution_mode == "retrieval_plus_llm" else "not used"
    decision_reason = str(
        audit_summary.get(
            "llm_decision_reason_short",
            "LLM not used: direct answer available from retrieved evidence.",
        )
        or "LLM not used: direct answer available from retrieved evidence."
    )
    runtime_override = str(audit_summary.get("llm_runtime_override_reason", "n/a") or "n/a")
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
    reset_raw = audit_summary.get("llm_reset_time_utc_iso", audit_summary.get("llm_rate_limit_reset", None))
    reset_value = str(reset_raw) if reset_raw not in {None, ""} else "n/a"
    input_budget_used = int(audit_summary.get("llm_input_budget_used_est", 0) or 0)
    input_budget_limit = int(audit_summary.get("llm_input_budget_limit", 0) or 0)
    dropped_locators = int(audit_summary.get("llm_dropped_locators_count", 0) or 0)
    dropped_hunks = int(audit_summary.get("llm_dropped_hunks_count", 0) or 0)
    dropped_snippets = int(audit_summary.get("llm_dropped_snippets_count", 0) or 0)
    calls_count = int(audit_summary.get("llm_calls_this_run", 0) or 0)
    models_used = str(audit_summary.get("llm_models_used", "n/a") or "n/a")
    budget_action = str(audit_summary.get("llm_budget_action", "n/a") or "n/a")
    return [
        "### 🤖 LLM",
        f"- TKYA LLM decision: {tkya_decision}",
        f"- Reason: {decision_reason}",
        *([f"- Runtime override: {runtime_override}"] if runtime_override != "n/a" else []),
        "- LLM used: yes" if llm_used else f"- LLM used: no ({skip_reason})",
        f"- LLM model used: `{model_id}`",
        (
            f"- Tokens used: prompt={prompt} completion={completion} total={total} "
            f"({'estimate' if usage_estimated else 'reported'})"
        ),
        f"- Requests remaining today: {remaining}{' (estimated)' if remaining_is_estimate else ''}",
        f"- Reset time UTC: {reset_value}",
        f"- Calls this run: {calls_count}",
        f"- Models used: {models_used}",
        f"- Prompt budget: used~{input_budget_used} / limit={input_budget_limit}",
        (
            "- Dropped context items: "
            f"locators={dropped_locators}, hunks={dropped_hunks}, snippets={dropped_snippets}"
        ),
        *([f"- AI Budget action: {budget_action}"] if budget_action != "n/a" else []),
    ]


def _embeddings_lines(audit_summary: dict[str, Any]) -> list[str]:
    embed_used = bool(audit_summary.get("embed_used", False))
    embed_reason = str(audit_summary.get("embed_reason", "n/a") or "n/a")
    model_id = str(audit_summary.get("embed_model_id", "not used") or "not used")
    index_model = str(audit_summary.get("embed_index_model", "n/a") or "n/a")
    index_dim = int(audit_summary.get("embed_index_dim", 0) or 0)
    tokens_prompt = int(audit_summary.get("embed_tokens_prompt", 0) or 0)
    tokens_total = int(audit_summary.get("embed_tokens_total", 0) or 0)
    usage_estimated = bool(audit_summary.get("embed_usage_estimated", True))
    remaining = audit_summary.get("embed_remaining_requests", "n/a")
    remaining_is_estimate = bool(audit_summary.get("embed_remaining_is_estimate", True))
    reset_raw = audit_summary.get("embed_reset_time_utc_iso")
    reset_value = str(reset_raw) if reset_raw not in {None, ""} else "n/a"
    chunks_embedded = int(audit_summary.get("embed_chunks_embedded", 0) or 0)
    query_embedded = bool(audit_summary.get("embed_query_embedded", False))
    budget_action = str(audit_summary.get("embed_budget_action", "n/a") or "n/a")
    return [
        "### Embeddings",
        "- Embeddings used: yes" if embed_used else f"- Embeddings used: no ({embed_reason})",
        f"- Embeddings model: `{model_id}`",
        f"- Index vectors: model={index_model}, dim={index_dim}, chunks={chunks_embedded}",
        f"- Query embedded: {'yes' if query_embedded else 'no'}",
        (
            f"- Tokens used: prompt={tokens_prompt} total={tokens_total} "
            f"({'estimate' if usage_estimated else 'reported'})"
        ),
        f"- Requests remaining today: {remaining}{' (estimated)' if remaining_is_estimate else ''}",
        f"- Reset time UTC: {reset_value}",
        *([f"- AI Budget action: {budget_action}"] if budget_action != "n/a" else []),
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


def _version_backend_lines(audit_summary: dict[str, Any]) -> list[str]:
    version = str(audit_summary.get("repobrain_version", "") or "").strip()
    backend = str(
        audit_summary.get(
            "tkya_backend",
            audit_summary.get("tky_engine", ""),
        )
        or ""
    ).strip()
    if not version or not backend:
        return []
    return [f"- RepoBrain version: `{version}`, TKYA backend: `{backend}`"]


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
                *_embeddings_lines(audit_summary),
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
                *_embeddings_lines(audit_summary),
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
            *_version_backend_lines(audit_summary),
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
    return "\n".join(
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
            *_embeddings_lines(audit_summary),
            "",
            "### 🧭 Route details",
            "- Route/Mode: `WAIT`",
            "- Passes: `1`",
            "",
            "### 🧾 Audit summary",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            *_version_backend_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )


def render_refuse_markdown(
    *,
    reason: str,
    audit_summary: dict[str, Any],
    blocked: bool = False,
) -> str:
    title = "### 🛑 Blocked" if blocked else "### 🚫 Refused"
    return "\n".join(
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
            *_embeddings_lines(audit_summary),
            "",
            "### 🧾 Audit summary",
            f"- route: {_route(audit_summary)}",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            *_version_backend_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )


def render_error_markdown(
    *,
    message: str,
    audit_summary: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "### 🛑 Error",
            message.strip() or "Unexpected error.",
            "",
            *_llm_lines(audit_summary),
            "",
            *_embeddings_lines(audit_summary),
            "",
            "### 🧾 Audit summary",
            f"- route: {_route(audit_summary)}",
            f"- retrieved: {int(audit_summary.get('retrieved', 0) or 0)}",
            f"- selected: {int(audit_summary.get('selected', 0) or 0)}",
            *_version_backend_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )


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
        *_embeddings_lines(audit_summary),
        "",
        "### 🧭 Route details",
        *_mode_lines(audit_summary),
        "",
        "### 🧾 Audit summary",
        *_version_backend_lines(audit_summary),
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
        *_embeddings_lines(audit_summary),
        "",
        "### 🧾 Audit summary",
        *_version_backend_lines(audit_summary),
        *_audit_kv_lines(audit_summary),
        "",
        _audit_note(),
    ]
    return "\n".join(sections)
