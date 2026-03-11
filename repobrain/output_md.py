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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def _verification_status(audit_summary: dict[str, Any]) -> str:
    raw_overall = str(audit_summary.get("verification_overall", "") or "").strip().upper()
    passed = _int(audit_summary.get("verification_pass_count", 0))
    failed = _int(audit_summary.get("verification_fail_count", 0))
    pending = _int(audit_summary.get("verification_pending_count", 0))
    not_run = _int(audit_summary.get("verification_not_run_count", 0))

    if raw_overall in {"PASS", "FAIL", "WARN", "NOT_RUN"}:
        if raw_overall == "FAIL":
            return "WARN"
        return raw_overall
    if failed > 0 or pending > 0:
        return "WARN"
    if passed > 0 and not_run == 0:
        return "PASS"
    return "NOT_RUN"


def _verification_lines(audit_summary: dict[str, Any]) -> list[str]:
    passed = _int(audit_summary.get("verification_pass_count", 0))
    failed = _int(audit_summary.get("verification_fail_count", 0))
    pending = _int(audit_summary.get("verification_pending_count", 0))
    not_run = _int(audit_summary.get("verification_not_run_count", 0))
    status = _verification_status(audit_summary)

    lines = [
        "### 🔎 Verification",
        f"- Status: **{status}**",
    ]

    if status == "NOT_RUN" and passed == 0 and failed == 0 and pending == 0 and not_run == 0:
        lines.append("- checks were not run.")
        lines.append("- Counters: n/a")
        return lines

    warn_count = failed + pending
    lines.append(f"- PASS: {passed}, WARN: {warn_count}, NOT_RUN: {not_run}")
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


def _llm_models_used_summary(audit_summary: dict[str, Any]) -> str:
    if not bool(audit_summary.get("llm_used", False)):
        return "n/a"

    as_text = str(audit_summary.get("llm_models_used", "") or "").strip()
    if as_text and as_text.lower() != "n/a":
        return as_text

    model_counts_raw = audit_summary.get("llm_model_counts", {})
    if isinstance(model_counts_raw, dict) and model_counts_raw:
        parts = [
            f"{model} ({_int(count, 0)} call{'s' if _int(count, 0) != 1 else ''})"
            for model, count in sorted(model_counts_raw.items(), key=lambda item: str(item[0]))
            if str(model).strip()
        ]
        if parts:
            return ", ".join(parts)

    model_id = str(audit_summary.get("llm_model_used", "") or "").strip()
    calls = max(1, _int(audit_summary.get("llm_calls_this_run", 1), 1))
    if model_id and model_id.lower() not in {"n/a", "not used"}:
        return f"{model_id} ({calls} call{'s' if calls != 1 else ''})"
    return "n/a"


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
    prompt = _int(audit_summary.get("llm_tokens_prompt", 0))
    completion = _int(audit_summary.get("llm_tokens_completion", 0))
    total = _int(audit_summary.get("llm_tokens_total", 0))
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
    input_budget_used = _int(audit_summary.get("llm_input_budget_used_est", 0))
    input_budget_limit = _int(audit_summary.get("llm_input_budget_limit", 0))
    dropped_locators = _int(audit_summary.get("llm_dropped_locators_count", 0))
    dropped_hunks = _int(audit_summary.get("llm_dropped_hunks_count", 0))
    dropped_snippets = _int(audit_summary.get("llm_dropped_snippets_count", 0))
    calls_count = _int(audit_summary.get("llm_calls_this_run", 0))
    models_used = _llm_models_used_summary(audit_summary)
    budget_action = str(audit_summary.get("llm_budget_action", "n/a") or "n/a")
    lines = [
        "### 🤖 LLM",
        f"- TKYA LLM decision: {tkya_decision}",
        f"- Reason: {decision_reason}",
    ]
    if runtime_override != "n/a":
        lines.append(f"- Runtime override: {runtime_override}")
    lines.extend(
        [
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
        ]
    )
    if budget_action != "n/a":
        lines.append(f"- AI Budget action: {budget_action}")
    return lines


def _embeddings_lines(audit_summary: dict[str, Any]) -> list[str]:
    embed_used = bool(audit_summary.get("embed_used", False))
    embed_reason = str(audit_summary.get("embed_reason", "n/a") or "n/a")
    model_id = str(audit_summary.get("embed_model_id", "not used") or "not used")
    index_model = str(audit_summary.get("embed_index_model", "n/a") or "n/a")
    index_dim = _int(audit_summary.get("embed_index_dim", 0))
    tokens_prompt = _int(audit_summary.get("embed_tokens_prompt", 0))
    tokens_total = _int(audit_summary.get("embed_tokens_total", 0))
    usage_estimated = bool(audit_summary.get("embed_usage_estimated", True))
    remaining = audit_summary.get("embed_remaining_requests", "n/a")
    remaining_is_estimate = bool(audit_summary.get("embed_remaining_is_estimate", True))
    reset_raw = audit_summary.get("embed_reset_time_utc_iso")
    reset_value = str(reset_raw) if reset_raw not in {None, ""} else "n/a"
    chunks_embedded = _int(audit_summary.get("embed_chunks_embedded", 0))
    query_embedded = bool(audit_summary.get("embed_query_embedded", False))
    budget_action = str(audit_summary.get("embed_budget_action", "n/a") or "n/a")
    lines = [
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
    ]
    if budget_action != "n/a":
        lines.append(f"- AI Budget action: {budget_action}")
    return lines


def _mode_lines(audit_summary: dict[str, Any]) -> list[str]:
    route = _route(audit_summary)
    pass_count = _int(audit_summary.get("pass_count", 1), 1)
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


def _tkya_mode_label(audit_summary: dict[str, Any]) -> str:
    raw = str(audit_summary.get("tky_engine", "n/a") or "n/a").strip().lower()
    if raw in {"baseline", "baseline-policy"}:
        return "baseline-policy"
    if raw in {"topocore_lite", "local"}:
        return "topocore_lite"
    if raw in {"remote"}:
        return "remote"
    if raw in {"n/a", ""}:
        return "n/a"
    return raw


def _version_backend_lines(audit_summary: dict[str, Any]) -> list[str]:
    version = str(audit_summary.get("repobrain_version", "") or "").strip()
    backend = str(audit_summary.get("tkya_backend", "") or "").strip()
    mode = _tkya_mode_label(audit_summary)
    lines: list[str] = []
    if version:
        lines.append(f"- RepoBrain version: `{version}`")
    if backend:
        lines.append(f"- TKYA backend: `{backend}`")
    if mode and mode != "n/a":
        lines.append(f"- TKYA mode: `{mode}`")
    return lines


def _diag_state(value: Any, parameter: str) -> str:
    if value is None:
        return "undefined"
    if isinstance(value, bool):
        key = parameter.lower()
        if key.endswith("used") or key.endswith("enabled") or key.endswith("allowed"):
            return "meaningful" if value else "disabled"
        return "meaningful"
    if isinstance(value, (list, tuple, set, dict)):
        return "meaningful" if len(value) > 0 else "disabled"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return "undefined"
        if normalized in {"n/a", "none", "null", "<missing>", "not used", "unknown"}:
            return "undefined"
        if normalized in {"disabled", "off", "false"}:
            return "disabled"
        return "meaningful"
    return "meaningful"


def _diag_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple, set)):
        return f"list[{len(value)}]"
    if isinstance(value, dict):
        return f"dict[{len(value)}]"
    text = str(value).strip()
    return text or "n/a"


def _diagnostic_groups(audit_summary: dict[str, Any]) -> list[tuple[str, list[tuple[str, Any, str]]]]:
    pr_files = _int(audit_summary.get("pr_changed_files_count", 0))
    if not pr_files:
        touched = audit_summary.get("touched_files", [])
        if isinstance(touched, list):
            pr_files = len([item for item in touched if str(item).strip()])

    return [
        (
            "A. Decision summary",
            [
                ("Route", _route(audit_summary), "Final TKYA route used for this response."),
                (
                    "Execution mode",
                    audit_summary.get("execution_mode", "retrieval_only"),
                    "Semantic decision: retrieval-only vs retrieval+LLM/verification/refuse.",
                ),
                ("LLM intent", audit_summary.get("llm_intent", "none"), "TKYA-selected LLM intent."),
                (
                    "Decision reason code",
                    audit_summary.get("llm_decision_reason_code", "n/a"),
                    "Machine-readable reason for semantic execution choice.",
                ),
                (
                    "Answer grounding mode",
                    audit_summary.get("answer_grounding_mode", "retrieval"),
                    "Primary grounding source for the answer.",
                ),
                (
                    "PR metadata used",
                    bool(audit_summary.get("pr_metadata_used", False)),
                    "PR changed-files metadata participated in grounding.",
                ),
            ],
        ),
        (
            "B. Runtime / Policy",
            [
                ("TKYA backend", audit_summary.get("tkya_backend", "n/a"), "Active TKYA backend selection."),
                ("TKYA mode", _tkya_mode_label(audit_summary), "Active TKYA engine mode."),
                (
                    "TKY mode requested",
                    audit_summary.get("tky_mode_requested", "n/a"),
                    "Requested provider mode from runtime input.",
                ),
                (
                    "TKY mode used",
                    audit_summary.get("tky_mode_used", "n/a"),
                    "Effective provider mode after policy checks.",
                ),
                (
                    "Remote skipped reason",
                    audit_summary.get("remote_skipped_reason", "n/a"),
                    "Why remote TKY was skipped, if applicable.",
                ),
                (
                    "Remote fallback reason",
                    audit_summary.get("tky_fallback_reason", "n/a"),
                    "Fallback reason when remote provider fails at runtime.",
                ),
                (
                    "Remote fallback code",
                    audit_summary.get("fallback_reason_code", "n/a"),
                    "Machine-readable fallback code for remote provider path.",
                ),
                (
                    "Runtime override",
                    audit_summary.get("llm_runtime_override_reason", "n/a"),
                    "Higher-priority runtime policy that overrode semantic LLM decision.",
                ),
            ],
        ),
        (
            "C. LLM",
            [
                ("LLM used", bool(audit_summary.get("llm_used", False)), "Whether LLM generation was executed."),
                ("Model", audit_summary.get("llm_model_used", "n/a"), "Effective LLM model id."),
                (
                    "Models used",
                    _llm_models_used_summary(audit_summary),
                    "Per-model call distribution for this run.",
                ),
                ("Tokens total", _int(audit_summary.get("llm_tokens_total", 0)), "LLM token usage for this run."),
                (
                    "Requests remaining",
                    audit_summary.get("llm_remaining_requests", "n/a"),
                    "Provider quota remaining after the run.",
                ),
                (
                    "Rate-limit reset",
                    audit_summary.get("llm_reset_time_utc_iso", "n/a"),
                    "Provider quota reset timestamp (UTC).",
                ),
            ],
        ),
        (
            "D. Embeddings",
            [
                (
                    "Embeddings used",
                    bool(audit_summary.get("embed_used", False)),
                    "Whether query/vector embedding path was used.",
                ),
                (
                    "Embeddings model",
                    audit_summary.get("embed_model_id", "n/a"),
                    "Effective embedding model id.",
                ),
                (
                    "Query embedded",
                    bool(audit_summary.get("embed_query_embedded", False)),
                    "Whether query vector was generated.",
                ),
                (
                    "Index embeddings status",
                    audit_summary.get("embed_index_status", audit_summary.get("embeddings_index_status", "n/a")),
                    "Runtime truth for index vector availability/usage.",
                ),
                (
                    "Chunks with vectors",
                    _int(audit_summary.get("embed_chunks_embedded", 0)),
                    "Number of indexed chunks that had vectors.",
                ),
            ],
        ),
        (
            "E. Retrieval / Evidence",
            [
                ("Retrieved candidates", _int(audit_summary.get("retrieved", 0)), "Candidates retrieved before selection."),
                ("Selected evidence", _int(audit_summary.get("selected", 0)), "Evidence items selected for response."),
                ("Retrieval passes", _int(audit_summary.get("pass_count", 1), 1), "Number of retrieval passes executed."),
                ("Top score", audit_summary.get("top_score", "n/a"), "Highest retrieval score observed."),
                (
                    "PR changed files",
                    pr_files,
                    "Count of changed files from PR metadata (if available).",
                ),
            ],
        ),
        (
            "F. Verification",
            [
                (
                    "Verification status",
                    _verification_status(audit_summary),
                    "Outcome from verification runner/check summary.",
                ),
                ("PASS checks", _int(audit_summary.get("verification_pass_count", 0)), "Checks completed successfully."),
                ("WARN checks", _int(audit_summary.get("verification_fail_count", 0)) + _int(audit_summary.get("verification_pending_count", 0)), "Checks failed or still pending."),
                ("NOT_RUN checks", _int(audit_summary.get("verification_not_run_count", 0)), "Checks intentionally or contextually not run."),
            ],
        ),
        (
            "G. Provider / Quota",
            [
                (
                    "Provider HTTP status",
                    audit_summary.get("llm_provider_http_status", "n/a"),
                    "Provider HTTP status for latest LLM call.",
                ),
                (
                    "Provider error type",
                    audit_summary.get("llm_provider_error_type", "n/a"),
                    "Normalized provider/network error class.",
                ),
                (
                    "Fallback used",
                    bool(audit_summary.get("llm_fallback_used", False)),
                    "Whether fallback model path was used.",
                ),
                (
                    "Budget action",
                    audit_summary.get("llm_budget_action", "n/a"),
                    "Governor action that constrained this run.",
                ),
                (
                    "Governor reason",
                    audit_summary.get("llm_governor_reason", "n/a"),
                    "Why governor allowed/blocked/adjusted calls.",
                ),
            ],
        ),
    ]


def _render_diagnostic_table(audit_summary: dict[str, Any]) -> list[str]:
    lines: list[str] = ["### 🧾 Diagnostic report"]
    undefined_rows: list[tuple[str, str, str, str]] = []

    for group_name, rows in _diagnostic_groups(audit_summary):
        meaningful: list[tuple[str, str, str]] = []
        for parameter, value, meaning in rows:
            state = _diag_state(value, parameter)
            value_text = _diag_value(value)
            if state == "meaningful":
                meaningful.append((parameter, value_text, meaning))
            else:
                undefined_rows.append((parameter, value_text, meaning, state))

        if not meaningful:
            continue
        meaningful.sort(key=lambda item: item[0].lower())
        lines.extend(
            [
                "",
                f"#### {group_name}",
                "| Parameter | Value | Meaning / Risk |",
                "| --- | --- | --- |",
            ]
        )
        for parameter, value_text, meaning in meaningful:
            lines.append(f"| {parameter} | `{value_text}` | {meaning} |")

    if undefined_rows:
        undefined_rows.sort(key=lambda item: item[0].lower())
        lines.extend(
            [
                "",
                "#### Undefined / disabled diagnostics",
                "| Parameter | Value | Meaning / Risk |",
                "| --- | --- | --- |",
            ]
        )
        for parameter, value_text, meaning, state in undefined_rows[:24]:
            lines.append(f"| {parameter} | `{value_text}` | {state}: {meaning} |")
        if len(undefined_rows) > 24:
            lines.append(f"| +{len(undefined_rows) - 24} more | `...` | omitted for compactness |")

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


def render_diagnostic_summary_markdown(audit_summary: dict[str, Any]) -> str:
    return "\n".join(_render_diagnostic_table(audit_summary))


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
                "### 📊 Evidence",
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
                "### 📊 Evidence (What I used)",
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
            f"- retrieved: {_int(audit_summary.get('retrieved', 0))}",
            f"- selected: {_int(audit_summary.get('selected', 0))}",
            f"- top_score: {audit_summary.get('top_score', 'n/a')}",
            *_version_backend_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
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
            f"- retrieved: {_int(audit_summary.get('retrieved', 0))}",
            f"- selected: {_int(audit_summary.get('selected', 0))}",
            *_version_backend_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
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
            f"- retrieved: {_int(audit_summary.get('retrieved', 0))}",
            f"- selected: {_int(audit_summary.get('selected', 0))}",
            *_version_backend_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
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
            f"- retrieved: {_int(audit_summary.get('retrieved', 0))}",
            f"- selected: {_int(audit_summary.get('selected', 0))}",
            *_version_backend_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
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
        "",
        *_render_diagnostic_table(audit_summary),
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
        "",
        *_render_diagnostic_table(audit_summary),
        "",
        _audit_note(),
    ]
    return "\n".join(sections)
