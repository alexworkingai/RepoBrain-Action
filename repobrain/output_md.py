from __future__ import annotations

import os
import re
from typing import Any

from repobrain.audit_contract import AUDIT_V6_CONTRACT_VERSION, _sanitize_repo_path, _sanitize_text
from repobrain.evidence import EvidenceItem
from repobrain.links import make_line_link
from repobrain.patch_governance import build_patch_governance_contract

MAX_COMMENT_BYTES = 60 * 1024


def _audit_note() -> str:
    if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true":
        return "Audit: workflow artifact `repobrain-audit` (hash-only)."
    return "Audit: local run (no workflow artifacts)."


def _route(audit_summary: dict[str, Any]) -> str:
    route = str(audit_summary.get("route_final", audit_summary.get("route", "FAST")) or "FAST")
    route = route.strip().upper()
    return route or "FAST"


def _verbose_diagnostics_enabled() -> bool:
    value = str(os.getenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "0") or "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _safe_visible_repo_path(path: Any) -> str:
    return _sanitize_repo_path(path)


def _safe_visible_text(text: Any) -> str:
    return _sanitize_text(text, max_length=400)


def _display_execution_mode(audit_summary: dict[str, Any]) -> str:
    execution_mode = str(audit_summary.get("execution_mode", "retrieval_only") or "retrieval_only").strip()
    if execution_mode == "retrieval_plus_llm" and not bool(audit_summary.get("llm_used", False)):
        return "retrieval_only"
    return execution_mode or "retrieval_only"


_REVIEW_SCAFFOLD_ONLY_RE = re.compile(
    r"^(?:[#>*\-\s]*)?(?:\(?\d+\)?[.)]?\s*)?"
    r"(?:pr metadata summary|targeted evidence|concise final review|final review synthesis|concise review)\s*:?\s*$",
    re.IGNORECASE,
)
_REVIEW_SCAFFOLD_PREFIX_RE = re.compile(
    r"^(?:[#>*\-\s]*)?(?:\(?\d+\)?[.)]?\s*)?"
    r"(?:pr metadata summary|targeted evidence|concise final review|final review synthesis|concise review)\s*:\s*",
    re.IGNORECASE,
)


def _semantic_key(text: str) -> str:
    compact = " ".join(str(text or "").strip().lower().split())
    return re.sub(r"[^a-z0-9]+", " ", compact).strip()


def _clean_review_tldr(summary_text: str) -> str:
    lines = [str(item).strip() for item in str(summary_text or "").splitlines() if str(item).strip()]
    cleaned: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if _REVIEW_SCAFFOLD_ONLY_RE.match(line):
            continue
        line_without_scaffold = _REVIEW_SCAFFOLD_PREFIX_RE.sub("", line).strip()
        if not line_without_scaffold:
            continue
        key = _semantic_key(line_without_scaffold)
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(line_without_scaffold)
    if not cleaned:
        return "Review summary available in findings and diagnostics."
    if len(cleaned) > 3:
        cleaned = cleaned[:3]
    summary = " ".join(cleaned).strip()
    if len(summary) > 420:
        summary = summary[:417].rstrip() + "..."
    return summary


def _compress_review_summary(
    summary_text: str,
    *,
    risk_drivers: list[str],
    informational_notes: list[str],
) -> str:
    summary = _clean_review_tldr(summary_text)
    sentence_split = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", summary)
        if str(item).strip()
    ]
    if not sentence_split:
        return summary
    blocker_keys = {
        _semantic_key(item)
        for item in [*risk_drivers, *informational_notes]
        if str(item).strip()
    }
    deduped_sentences: list[str] = []
    seen: set[str] = set()
    for sentence in sentence_split:
        key = _semantic_key(sentence)
        if not key or key in seen:
            continue
        if key in blocker_keys:
            continue
        seen.add(key)
        deduped_sentences.append(sentence)
        if len(deduped_sentences) >= 3:
            break
    if not deduped_sentences:
        deduped_sentences = sentence_split[:1]
    compact = " ".join(deduped_sentences).strip()
    if len(compact) > 420:
        compact = compact[:417].rstrip() + "..."
    return compact or "Review summary available in findings and diagnostics."


def _compress_review_summary_with_flag(
    summary_text: str,
    *,
    risk_drivers: list[str],
    informational_notes: list[str],
) -> tuple[str, bool]:
    original = " ".join(str(summary_text or "").strip().split())
    compact = _compress_review_summary(
        summary_text,
        risk_drivers=risk_drivers,
        informational_notes=informational_notes,
    )
    compact_norm = " ".join(str(compact or "").strip().split())
    return compact, compact_norm != original


def _confirmed_evidence_map(review: dict[str, Any]) -> dict[str, list[str]]:
    raw_items = review.get("confirmed_risk_items", [])
    if not isinstance(raw_items, list):
        return {}
    mapping: dict[str, list[str]] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        message = str(item.get("message", "") or "").strip()
        if not message:
            continue
        key = _semantic_key(message)
        if not key:
            continue
        paths_raw = item.get("evidence_paths", [])
        paths = (
            [str(path).strip() for path in paths_raw if str(path).strip()]
            if isinstance(paths_raw, list)
            else []
        )
        if paths:
            mapping[key] = list(dict.fromkeys(paths))
    return mapping


def _render_confirmed_finding_with_evidence(
    finding: str,
    *,
    evidence_map: dict[str, list[str]],
) -> str:
    text = str(finding or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if "files:" in lowered or "file:" in lowered or "locator:" in lowered:
        return text
    base = re.sub(r"\s*\(evidence:\s*\d+\s*file\(s\)\)\s*$", "", text, flags=re.IGNORECASE).strip()
    key = _semantic_key(base)
    evidence_paths = evidence_map.get(key, [])
    if not evidence_paths:
        return text
    if len(evidence_paths) == 1:
        return f"{base} (file: `{evidence_paths[0]}`)"
    if len(evidence_paths) <= 3:
        rendered = ", ".join(f"`{path}`" for path in evidence_paths)
        return f"{base} (files: {rendered})"
    return f"{base} (evidence: {len(evidence_paths)} files; sample: `{evidence_paths[0]}`)"


def _compact_anchor_list(paths: list[str], *, max_items: int = 3) -> str:
    anchors = [_safe_visible_repo_path(path) for path in paths]
    anchors = [path for path in anchors if path]
    if not anchors:
        return "none"
    unique = list(dict.fromkeys(anchors))
    if len(unique) <= max_items:
        return ", ".join(f"`{item}`" for item in unique)
    kept = ", ".join(f"`{item}`" for item in unique[:max_items])
    return f"{kept} (+{len(unique) - max_items} more)"


def _decision_card_lines(title: str, rows: list[str]) -> list[str]:
    cleaned = [str(row).strip() for row in rows if str(row).strip()]
    if not cleaned:
        return []
    lines = [f"#### {title}"]
    lines.extend(f"- {row}" for row in cleaned)
    lines.append("")
    return lines


def _evidence_verdict_lines(review: dict[str, Any]) -> list[str]:
    raw = review.get("evidence_verdicts", [])
    if not isinstance(raw, list):
        raw = []
    verdict_lines: list[str] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim", "") or "").strip()
        if not claim:
            continue
        anchors_raw = item.get("evidence_anchors", [])
        anchors = (
            [str(path).strip() for path in anchors_raw if str(path).strip()]
            if isinstance(anchors_raw, list)
            else []
        )
        confidence = str(item.get("confidence", "n/a") or "n/a").strip().lower() or "n/a"
        impact = str(item.get("impact", "n/a") or "n/a").strip().lower() or "n/a"
        patchability = str(item.get("patchability", "n/a") or "n/a").strip().lower() or "n/a"
        why_now = str(item.get("why_now", "n/a") or "n/a").strip() or "n/a"
        why_not = str(item.get("why_not", "n/a") or "n/a").strip() or "n/a"
        uncertainty = str(item.get("uncertainty", "n/a") or "n/a").strip() or "n/a"
        verdict_lines.extend(
            _decision_card_lines(
                f"Verdict {idx}",
                [
                    f"Claim: {claim}",
                    f"Evidence anchors: {_compact_anchor_list(anchors)}",
                    f"Confidence: `{confidence}`",
                    f"Impact: `{impact}`",
                    f"Patchability: `{patchability}`",
                    f"Why now: {why_now}",
                    f"Why not: {why_not}",
                    f"Uncertainty: {uncertainty}",
                ],
            )
        )
    if verdict_lines:
        return verdict_lines
    return [
        "- No evidence-backed verdicts were emitted in this run (no confirmed findings).",
    ]


def _resolve_patch_governance_contract(
    *,
    review: dict[str, Any],
    verification_report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> dict[str, str]:
    existing_class = str(audit_summary.get("patch_governance_class", "") or "").strip()
    if existing_class and existing_class not in {"n/a", "not_applicable"}:
        return {
            "patchability_class": existing_class,
            "patch_risk_class": str(audit_summary.get("patch_risk_class", "n/a") or "n/a"),
            "minimum_proof_threshold_status": str(
                audit_summary.get("patch_proof_threshold_status", "not_applicable") or "not_applicable"
            ),
            "verification_preconditions": str(
                audit_summary.get("patch_verification_preconditions", "not_applicable") or "not_applicable"
            ),
            "governance_reason": str(
                audit_summary.get("patch_governance_reason", "not_applicable") or "not_applicable"
            ),
            "why_now": str(audit_summary.get("patch_governance_why_now", "not_applicable") or "not_applicable"),
            "why_not": str(audit_summary.get("patch_governance_why_not", "not_applicable") or "not_applicable"),
            "uncertainty": str(
                audit_summary.get("patch_governance_uncertainty", "not_applicable") or "not_applicable"
            ),
            "next_safe_step": str(
                audit_summary.get("patch_governance_next_safe_step", "not_applicable") or "not_applicable"
            ),
        }
    verification_summary = str(
        verification_report.get("summary", verification_report.get("overall", "NOT_RUN")) or "NOT_RUN"
    )
    return build_patch_governance_contract(
        patch_generation_result=str(audit_summary.get("patch_generation_result", "n/a") or "n/a"),
        patch_validation_result=str(audit_summary.get("patch_validation_result", "n/a") or "n/a"),
        patch_targeting_mode=str(audit_summary.get("patch_targeting_mode", "n/a") or "n/a"),
        patch_targeting_reason=str(audit_summary.get("patch_targeting_reason", "n/a") or "n/a"),
        localized_patch_evidence_count=_int(audit_summary.get("localized_patch_evidence_count", 0)),
        patch_target_files_selected=_int(
            audit_summary.get("patch_target_files_selected", audit_summary.get("patch_target_files_count", 0))
        ),
        patch_guard_triggered=bool(audit_summary.get("patch_guard_triggered", False)),
        verification_summary=verification_summary,
        evidence_verdicts=review.get("evidence_verdicts", []),
    )


def _patch_governance_lines(
    *,
    review: dict[str, Any],
    verification_report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> list[str]:
    contract = _resolve_patch_governance_contract(
        review=review,
        verification_report=verification_report,
        audit_summary=audit_summary,
    )
    evidence_verdicts = review.get("evidence_verdicts", [])
    evidence_verdicts_count = len(evidence_verdicts) if isinstance(evidence_verdicts, list) else 0
    return _decision_card_lines(
        "Patch governance decision",
        [
            f"Patchability class: `{contract.get('patchability_class', 'no_patch_safe_default')}`",
            f"Patch risk class: `{contract.get('patch_risk_class', 'n/a')}`",
            f"Minimum proof threshold: `{contract.get('minimum_proof_threshold_status', 'not_applicable')}`",
            f"Verification preconditions: `{contract.get('verification_preconditions', 'not_applicable')}`",
            f"Governance reason: {contract.get('governance_reason', 'not_applicable')}",
            f"Why now: {contract.get('why_now', 'not_applicable')}",
            f"Why not: {contract.get('why_not', 'not_applicable')}",
            f"Uncertainty: `{contract.get('uncertainty', 'not_applicable')}`",
            f"Next safe step: {contract.get('next_safe_step', 'not_applicable')}",
            f"Evidence verdicts considered: `{evidence_verdicts_count}`",
        ],
    )


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
    audit_summary: dict[str, Any] | None = None,
) -> list[str]:
    if not evidence:
        return ["- No source locators selected."]
    lines: list[str] = []
    for item in evidence:
        safe_path = _safe_visible_repo_path(item.file_path)
        if not safe_path:
            continue
        lines.append(
            (
                f"- [{_evidence_context_label_for_path(safe_path, audit_summary)}] "
                f"{make_line_link(repo, sha, safe_path, item.line_start, item.line_end)} "
                f"(score={item.score:.4f})"
            )
        )
    return lines or ["- No source locators selected."]


def _changed_files_set(audit_summary: dict[str, Any] | None) -> set[str]:
    if not isinstance(audit_summary, dict):
        return set()
    raw = audit_summary.get("touched_files", [])
    if not isinstance(raw, list):
        return set()
    return {
        safe
        for item in raw
        for safe in [_safe_visible_repo_path(item)]
        if safe
    }


def _is_test_context_path(path: str) -> bool:
    normalized = str(path or "").strip().lower()
    if not normalized:
        return False
    return (
        normalized.startswith("tests/")
        or "/tests/" in normalized
        or normalized.endswith("_test.py")
        or normalized.endswith("_spec.py")
    )


def _is_reference_context_path(path: str) -> bool:
    normalized = str(path or "").strip().lower()
    if not normalized:
        return False
    if normalized.startswith("docs/") or normalized.startswith(".github/workflows/"):
        return True
    if normalized.endswith(".md") or normalized.endswith(".rst"):
        return True
    if normalized.endswith((".toml", ".yaml", ".yml", ".json", ".ini", ".cfg")):
        return True
    basename = normalized.rsplit("/", 1)[-1]
    return basename in {
        "pyproject.toml",
        "poetry.lock",
        "requirements.txt",
        "setup.cfg",
        "setup.py",
        "tox.ini",
        "package.json",
        "package-lock.json",
    }


def _evidence_context_label_for_path(path: str, audit_summary: dict[str, Any] | None) -> str:
    changed_paths = _changed_files_set(audit_summary)
    normalized_path = str(path or "").strip()
    if normalized_path and normalized_path in changed_paths:
        return "Changed in PR"
    if _is_test_context_path(normalized_path):
        return "Test context"
    if _is_reference_context_path(normalized_path):
        return "Reference"
    return "Support context"


_TOUCHED_FILE_PATH_RE = re.compile(r"`([^`]+)`")


def _label_touched_file_lines(files_block: list[str], audit_summary: dict[str, Any]) -> list[str]:
    labeled: list[str] = []
    for raw in files_block:
        line = str(raw or "").strip()
        if not line or not line.startswith("- "):
            labeled.append(line)
            continue
        if line.startswith("- +") or "No changed files detected." in line:
            labeled.append(line)
            continue
        match = _TOUCHED_FILE_PATH_RE.search(line)
        path = _safe_visible_repo_path(match.group(1)) if match else ""
        if match and not path:
            continue
        label = _evidence_context_label_for_path(path, audit_summary) if path else "Support context"
        text = line[2:].strip()
        if match:
            text = text.replace(f"`{match.group(1)}`", f"`{path}`")
        labeled.append(f"- [{label}] {text}")
    return labeled


def _parse_evidence_bucket_counts(audit_summary: dict[str, Any]) -> dict[str, int]:
    counts = {
        "changed_primary": 0,
        "changed_secondary": 0,
        "support_context": 0,
        "tests": 0,
        "docs": 0,
        "workflow_config": 0,
    }
    raw = str(audit_summary.get("evidence_budget_bucket_counts", "") or "").strip()
    if not raw:
        return counts
    for token in raw.split(","):
        key, sep, value = token.partition(":")
        if not sep:
            continue
        key_norm = key.strip().lower()
        if key_norm not in counts:
            continue
        counts[key_norm] = _int(value.strip(), 0)
    return counts


def _evidence_context_summary_lines(audit_summary: dict[str, Any]) -> list[str]:
    counts = _parse_evidence_bucket_counts(audit_summary)
    changed_count = counts["changed_primary"] + counts["changed_secondary"]
    support_count = counts["support_context"]
    tests_count = counts["tests"]
    reference_count = counts["docs"] + counts["workflow_config"]
    if changed_count == 0:
        changed_count = len(_changed_files_set(audit_summary))
    selected = _int(audit_summary.get("selected", 0))
    if changed_count == 0 and support_count == 0 and tests_count == 0 and reference_count == 0 and selected == 0:
        return []
    return [
        "### 🏷️ Evidence context",
        f"- Changed in PR: `{changed_count}`",
        f"- Support context: `{support_count}`",
        f"- Test context: `{tests_count}`",
        f"- Reference: `{reference_count}`",
        "",
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


def _normalized_budget_action(
    *,
    budget_action: str,
    retained_reason: str,
    intermediate_downgrade_occurred: bool = False,
    final_synthesis_retained_preferred: bool = False,
) -> str:
    action = str(budget_action or "n/a").strip()
    retained = str(retained_reason or "n/a").strip()
    if action.lower() == "n/a":
        return "n/a"
    if retained.lower() == "n/a" and not final_synthesis_retained_preferred:
        return action

    parts = [item.strip() for item in action.split(";") if item.strip()]
    filtered = [
        item
        for item in parts
        if item not in {"model_downgraded_to_mini", "model_downgraded_to_mini_estimate_mode"}
    ]
    if intermediate_downgrade_occurred and final_synthesis_retained_preferred:
        retention_note = (
            "budget policy evaluated; final synthesis retained preferred model; "
            "intermediate downgrade used for auxiliary calls"
        )
    else:
        retention_note = "budget policy evaluated; preferred model retained"
    if filtered:
        return "; ".join([*filtered, retention_note])
    return retention_note


def _llm_lines(audit_summary: dict[str, Any]) -> list[str]:
    llm_used = bool(audit_summary.get("llm_used", False))
    skip_reason = str(audit_summary.get("llm_skip_reason", "n/a") or "n/a")
    planned_llm = str(audit_summary.get("execution_mode", "retrieval_only") or "retrieval_only") == "retrieval_plus_llm"
    if llm_used:
        tkya_decision = "used"
    elif planned_llm:
        tkya_decision = "not called"
    else:
        tkya_decision = "not used"
    decision_reason = str(
        audit_summary.get(
            "llm_decision_reason_short",
            "LLM not used: direct answer available from retrieved evidence.",
        )
        or "LLM not used: direct answer available from retrieved evidence."
    )
    runtime_override = str(audit_summary.get("llm_runtime_override_reason", "n/a") or "n/a")
    if not llm_used and planned_llm:
        decision_reason = (
            "LLM was not called; answer generated from deterministic retrieval/template path."
        )
    model_id = str(audit_summary.get("llm_model_used", "not used") or "not used")
    preferred_model_id = str(audit_summary.get("llm_preferred_model_id", "n/a") or "n/a")
    final_synthesis_model_id = str(
        audit_summary.get("llm_final_synthesis_model_id", model_id or "not used") or "not used"
    )
    if not llm_used:
        final_synthesis_model_id = "n/a"
    if llm_used and final_synthesis_model_id in {"", "n/a", "not used"}:
        final_synthesis_model_id = model_id
    preferred_model_id = str(audit_summary.get("llm_preferred_model_id", "n/a") or "n/a")
    selection_reason = str(audit_summary.get("llm_model_selection_reason", "n/a") or "n/a")
    downgrade_reason = str(audit_summary.get("llm_model_downgrade_reason", "n/a") or "n/a")
    retained_reason = str(audit_summary.get("llm_retained_preferred_model_reason", "n/a") or "n/a")
    downgrade_threshold = str(audit_summary.get("llm_downgrade_threshold_used", "n/a") or "n/a")
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
    model_counts_raw = audit_summary.get("llm_model_counts", {})
    model_counts = model_counts_raw if isinstance(model_counts_raw, dict) else {}
    computed_final_retained = (
        llm_used
        and preferred_model_id not in {"", "n/a", "not used"}
        and final_synthesis_model_id == preferred_model_id
    )
    final_retained = bool(
        audit_summary.get("llm_final_synthesis_retained_preferred_model", computed_final_retained)
    )
    computed_intermediate_downgrade = (
        llm_used
        and final_retained
        and any("mini" in str(model).lower() and _int(count) > 0 for model, count in model_counts.items())
    )
    intermediate_downgrade = bool(
        audit_summary.get("llm_intermediate_downgrade_occurred", computed_intermediate_downgrade)
    )
    intermediate_downgrade_reason = str(
        audit_summary.get("llm_intermediate_downgrade_reason", "n/a") or "n/a"
    )
    if intermediate_downgrade and intermediate_downgrade_reason == "n/a":
        if downgrade_reason != "n/a":
            intermediate_downgrade_reason = downgrade_reason
        elif budget_action != "n/a":
            intermediate_downgrade_reason = budget_action
    budget_action = _normalized_budget_action(
        budget_action=budget_action,
        retained_reason=retained_reason,
        intermediate_downgrade_occurred=intermediate_downgrade,
        final_synthesis_retained_preferred=final_retained,
    )
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
            f"- Preferred model: `{preferred_model_id}`",
            f"- Final synthesis model: `{final_synthesis_model_id}`",
            f"- LLM model used: `{model_id if llm_used else 'not used'}`",
            f"- Model selection reason: {selection_reason}",
            (
                f"- Tokens used: prompt={prompt} completion={completion} total={total} "
                f"({'estimate' if usage_estimated else 'reported'})"
            ),
            f"- Requests remaining today: {remaining}{' (estimated)' if remaining_is_estimate else ''}",
            f"- Reset time UTC: {reset_value}",
            f"- Calls this run: {calls_count}",
            f"- Models used: {models_used}",
            f"- Final synthesis retained preferred model: {'yes' if final_retained else 'no'}",
            f"- Intermediate downgrade occurred: {'yes' if intermediate_downgrade else 'no'}",
            f"- Prompt budget: used~{input_budget_used} / limit={input_budget_limit}",
            (
                "- Dropped context items: "
                f"locators={dropped_locators}, hunks={dropped_hunks}, snippets={dropped_snippets}"
            ),
        ]
    )
    if intermediate_downgrade and intermediate_downgrade_reason != "n/a":
        lines.append(f"- Intermediate downgrade reason: {intermediate_downgrade_reason}")
    if downgrade_reason != "n/a":
        lines.append(f"- Model downgrade reason: {downgrade_reason}")
    if retained_reason != "n/a":
        lines.append(f"- Preferred model retained: {retained_reason}")
    if downgrade_threshold != "n/a":
        lines.append(f"- Downgrade threshold (remaining requests): {downgrade_threshold}")
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


def _retrieval_snapshot_lines(audit_summary: dict[str, Any]) -> list[str]:
    command = str(audit_summary.get("command", "ask") or "ask").strip().lower()
    if command not in {"ask", "review", "fix"}:
        return []
    used = bool(audit_summary.get("retrieval_snapshot_cache_used", False))
    hit = bool(audit_summary.get("retrieval_snapshot_cache_hit", False))
    key_kind = str(audit_summary.get("retrieval_snapshot_cache_key_kind", "not_applicable") or "not_applicable")
    miss_reason = str(
        audit_summary.get("retrieval_snapshot_cache_miss_reason", "not_applicable")
        or "not_applicable"
    )
    age_s = _int(audit_summary.get("retrieval_snapshot_cache_age_s", 0))
    status = "hit" if used and hit else ("miss" if used else "not_applicable")
    lines = [
        "### 🗃️ Retrieval snapshot cache",
        f"- Status: `{status}`",
    ]
    if key_kind != "not_applicable":
        lines.append(f"- Key kind: `{key_kind}`")
    if status == "hit":
        lines.append(f"- Snapshot age (s): `{age_s}`")
    else:
        lines.append(f"- Reason: `{miss_reason}`")
    lines.append("")
    return lines


def _review_delta_lines(audit_summary: dict[str, Any]) -> list[str]:
    command = str(audit_summary.get("command", "review") or "review").strip().lower()
    if command != "review":
        return []
    active = bool(audit_summary.get("review_delta_memory_active", False))
    if not active:
        return []
    prior_state_available = bool(audit_summary.get("review_delta_prior_state_available", False))
    status = str(
        audit_summary.get(
            "review_delta_status",
            "prior_state_present" if prior_state_available else "first_run",
        )
        or "first_run"
    )
    matching_mode = str(audit_summary.get("review_delta_matching_mode", "not_applicable") or "not_applicable")
    summary = str(
        audit_summary.get(
            "review_delta_current_vs_prior_summary",
            "first_run_no_prior_state" if not prior_state_available else "n/a",
        )
        or "n/a"
    )
    new_count = _int(audit_summary.get("review_delta_new_count", 0))
    persisted_count = _int(audit_summary.get("review_delta_persisted_count", 0))
    resolved_count = _int(audit_summary.get("review_delta_resolved_count", 0))
    reclassified_count = _int(audit_summary.get("review_delta_reclassified_count", 0))
    uncertainty_level = str(
        audit_summary.get("review_delta_uncertainty_level", "not_applicable") or "not_applicable"
    )
    lines = [
        "### 🔄 Review delta",
        f"- Prior state available: `{'yes' if prior_state_available else 'no'}`",
        f"- Status: `{status}`",
        f"- Matching mode: `{matching_mode}`",
        f"- Summary: `{summary}`",
        f"- New findings: `{new_count}` ({str(audit_summary.get('review_delta_new_summary', 'none') or 'none')})",
        (
            f"- Persisted findings: `{persisted_count}` "
            f"({str(audit_summary.get('review_delta_persisted_summary', 'none') or 'none')})"
        ),
        (
            f"- Resolved findings: `{resolved_count}` "
            f"({str(audit_summary.get('review_delta_resolved_summary', 'none') or 'none')})"
        ),
    ]
    if reclassified_count > 0:
        lines.append(
            f"- Reclassified findings: `{reclassified_count}` "
            f"({str(audit_summary.get('review_delta_reclassified_summary', 'none') or 'none')})"
        )
    if uncertainty_level != "not_applicable":
        lines.append(f"- Uncertainty level: `{uncertainty_level}`")
    lines.append("")
    return lines


def _ultra_large_pr_mode_lines(audit_summary: dict[str, Any], *, command: str) -> list[str]:
    cmd = str(command or audit_summary.get("command", "ask") or "ask").strip().lower()
    if cmd not in {"ask", "review", "fix"}:
        return []
    active = bool(audit_summary.get("ultra_large_pr_mode_active", False))
    if not active:
        return []
    level = str(audit_summary.get("ultra_large_pr_mode_level", "large") or "large")
    reason = str(audit_summary.get("ultra_large_pr_mode_reason", "none") or "none")
    strategy = str(audit_summary.get("ultra_large_pr_depth_strategy", "primary_first_capped") or "primary_first_capped")
    budget_mode = str(audit_summary.get("evidence_budget_mode", "not_applied") or "not_applied")
    synthesis_cap = _int(audit_summary.get("ultra_large_pr_synthesis_window_cap", 0))
    primary = str(audit_summary.get("ultra_large_pr_primary_coverage_summary", "none") or "none")
    bounded = str(audit_summary.get("ultra_large_pr_bounded_coverage_summary", "none") or "none")
    coverage_statement = str(
        audit_summary.get("ultra_large_pr_coverage_statement", "Bounded coverage active.")
        or "Bounded coverage active."
    )
    lines = [
        "### 🧱 Ultra-large PR mode",
        "- Status: `active`",
        f"- Level: `{level}`",
        f"- Activation reason: `{reason}`",
        f"- Depth strategy: `{strategy}`",
        f"- Evidence budget mode: `{budget_mode}`",
        f"- Synthesis window cap: `{synthesis_cap}`",
        f"- Primary coverage: `{primary}`",
        f"- Bounded coverage: `{bounded}`",
        f"- Coverage statement: {coverage_statement}",
    ]
    if cmd == "fix":
        downgraded = bool(audit_summary.get("ultra_large_pr_patch_governance_downgraded", False))
        downgrade_reason = str(
            audit_summary.get("ultra_large_pr_patch_governance_reason", "n/a") or "n/a"
        )
        lines.append(f"- Patch governance downgraded: `{'yes' if downgraded else 'no'}`")
        if downgraded:
            lines.append(f"- Patch governance reason: `{downgrade_reason}`")
    lines.append("")
    return lines


def _runtime_provenance_lines(audit_summary: dict[str, Any], *, command: str) -> list[str]:
    cmd = str(command or audit_summary.get("command", "ask") or "ask").strip().lower()
    if cmd not in {"review", "fix"}:
        return []
    status = str(audit_summary.get("runtime_provenance_status", "not_applicable") or "not_applicable")
    if status == "not_applicable":
        return []
    runtime_sha = str(audit_summary.get("runtime_provenance_runtime_sha", "n/a") or "n/a")
    pr_head_sha = str(audit_summary.get("runtime_provenance_pr_head_sha", "n/a") or "n/a")
    reason_code = str(audit_summary.get("runtime_provenance_reason_code", "n/a") or "n/a")
    explanation = str(audit_summary.get("runtime_provenance_explanation", "n/a") or "n/a")
    sha_match = bool(audit_summary.get("runtime_provenance_sha_match", False))
    return [
        "### 🧬 Runtime provenance",
        f"- Status: `{status}`",
        f"- Runtime SHA: `{runtime_sha}`",
        f"- PR head SHA: `{pr_head_sha}`",
        f"- SHA match: `{'yes' if sha_match else 'no'}`",
        f"- Reason code: `{reason_code}`",
        f"- Explanation: {explanation}",
        "",
    ]


def _touched_files_lines(audit_summary: dict[str, Any]) -> list[str]:
    raw = audit_summary.get("touched_files", [])
    if not isinstance(raw, list):
        return []
    files = [str(item).strip() for item in raw if str(item).strip()]
    if not files:
        return []
    files = sorted(set(files))
    preview = ", ".join(f"`{path}`" for path in files[:3])
    lines = ["", f"Touched files: {len(files)} total."]
    if preview:
        lines.append(f"- sample: {preview}")
    if len(files) > 3:
        lines.append(f"- +{len(files) - 3} more")
    return lines


def _pr_segments_lines(audit_summary: dict[str, Any]) -> list[str]:
    used = bool(audit_summary.get("pr_segmentation_used", False))
    summary = str(audit_summary.get("pr_segment_summary", "none") or "none")
    primary = str(audit_summary.get("pr_primary_segments", "none") or "none")
    support = str(audit_summary.get("pr_support_segments", "none") or "none")
    cross_segment = bool(audit_summary.get("pr_cross_segment", False))
    if not used and summary == "none":
        return []
    lines = [""]
    if summary != "none":
        lines.append(f"PR segments: {summary}")
    else:
        lines.append(
            "PR segments: "
            f"primary={primary}; support={support}; cross-segment={'yes' if cross_segment else 'no'}"
        )
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


def _bool_label(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    raw = str(value or "").strip().lower()
    if raw in {"true", "1", "yes"}:
        return "yes"
    if raw in {"false", "0", "no"}:
        return "no"
    if raw in {"", "n/a"}:
        return "n/a"
    return raw


def _normalized_backend_evidence(audit_summary: dict[str, Any]) -> dict[str, str]:
    def _pick_str(*keys: str, default: str) -> str:
        for key in keys:
            raw = audit_summary.get(key)
            text = str(raw or "").strip()
            if text:
                return text
        return default

    requested = _pick_str("requested_backend", "topocore_backend_requested", default="n/a")
    resolved = _pick_str("resolved_backend", "topocore_backend_resolved", default="n/a")
    backend_mode = _pick_str("backend_mode", "topocore_backend_mode", default="n/a")
    tkya_mode = _pick_str("tkya_mode", default=_tkya_mode_label(audit_summary))
    tky_mode_requested = _pick_str("tky_mode_requested", default="n/a")
    tky_mode_used = _pick_str("tky_mode_used", default="n/a")
    fallback_used = _bool_label(
        audit_summary.get(
            "fallback_used",
            audit_summary.get("topocore_fallback_used", "n/a"),
        )
    )
    fallback_reason = _pick_str("fallback_reason", "topocore_fallback_reason", default="n/a")
    scope_status = _pick_str("scope_status", default="")
    patch_authorized = _bool_label(audit_summary.get("patch_authorized", "n/a"))
    patch_applied = _bool_label(audit_summary.get("patch_applied", "n/a"))
    files_modified = _bool_label(audit_summary.get("files_modified", "n/a"))
    branch_created = _bool_label(audit_summary.get("branch_created", "n/a"))
    commit_created = _bool_label(audit_summary.get("commit_created", "n/a"))
    pr_created = _bool_label(audit_summary.get("pr_created", "n/a"))
    tkya_backend = _pick_str("tkya_backend", default="")

    return {
        "tky_mode_requested": tky_mode_requested,
        "tky_mode_used": tky_mode_used,
        "tkya_mode": tkya_mode,
        "tkya_backend": tkya_backend,
        "topocore_backend_requested": requested,
        "topocore_backend_resolved": resolved,
        "topocore_backend_mode": backend_mode,
        "topocore_fallback_used": fallback_used,
        "topocore_fallback_reason": fallback_reason,
        "scope_status": scope_status,
        "patch_authorized": patch_authorized,
        "patch_applied": patch_applied,
        "files_modified": files_modified,
        "branch_created": branch_created,
        "commit_created": commit_created,
        "pr_created": pr_created,
    }


def _runtime_backend_evidence_lines(audit_summary: dict[str, Any]) -> list[str]:
    normalized = _normalized_backend_evidence(audit_summary)
    lines = [
        "### 🧭 Runtime backend evidence",
        f"- TKY mode requested: `{normalized['tky_mode_requested']}`",
        f"- TKY mode used: `{normalized['tky_mode_used']}`",
        f"- TKYA mode: `{normalized['tkya_mode']}`",
        f"- TopoCore backend requested: `{normalized['topocore_backend_requested']}`",
        f"- TopoCore backend resolved: `{normalized['topocore_backend_resolved']}`",
        f"- TopoCore backend mode: `{normalized['topocore_backend_mode']}`",
        f"- TopoCore fallback used: `{normalized['topocore_fallback_used']}`",
        f"- TopoCore fallback reason: `{normalized['topocore_fallback_reason']}`",
    ]
    if normalized["scope_status"]:
        lines.append(f"- Scope status: `{normalized['scope_status']}`")
    if normalized["patch_authorized"] != "n/a":
        lines.append(f"- Patch authorized: `{normalized['patch_authorized']}`")
    if normalized["patch_applied"] != "n/a":
        lines.append(f"- Patch applied: `{normalized['patch_applied']}`")
    if normalized["files_modified"] != "n/a":
        lines.append(f"- Files modified: `{normalized['files_modified']}`")
    if normalized["branch_created"] != "n/a":
        lines.append(f"- Branch created: `{normalized['branch_created']}`")
    if normalized["commit_created"] != "n/a":
        lines.append(f"- Commit created: `{normalized['commit_created']}`")
    if normalized["pr_created"] != "n/a":
        lines.append(f"- PR created: `{normalized['pr_created']}`")
    return lines


def _has_pr_backend_evidence_context(audit_summary: dict[str, Any]) -> bool:
    if bool(audit_summary.get("pr_metadata_used", False)):
        return True
    if _int(audit_summary.get("pr_changed_files_count", 0)) > 0:
        return True
    summary = str(audit_summary.get("pr_segment_summary", "none") or "none").strip().lower()
    if summary not in {"", "none", "not_available"}:
        return True
    if bool(audit_summary.get("runtime_provenance_status")) and str(
        audit_summary.get("runtime_provenance_status", "not_applicable") or "not_applicable"
    ).strip().lower() != "not_applicable":
        return True
    return False


def _version_backend_lines(audit_summary: dict[str, Any]) -> list[str]:
    version = str(audit_summary.get("repobrain_version", "") or "").strip()
    normalized = _normalized_backend_evidence(audit_summary)
    backend = normalized["tkya_backend"]
    mode = normalized["tkya_mode"]
    lines: list[str] = []
    if version:
        lines.append(f"- RepoBrain version: `{version}`")
    if backend:
        lines.append(f"- TKYA backend: `{backend}`")
    if mode and mode != "n/a":
        lines.append(f"- TKYA mode: `{mode}`")
    lines.extend(_runtime_backend_evidence_lines(audit_summary)[1:])
    return lines


def _diag_state(value: Any, parameter: str) -> str:
    parameter_norm = str(parameter or "").strip().lower()
    sprint38_always_meaningful = {
        "hybrid rerank used",
        "retrieval ranking mode",
        "evidence filtered",
        "evidence filter reason codes",
        "async batch used",
        "async batch mode",
        "async batch concurrency",
        "async batch tasks total",
        "async batch tasks completed",
        "async batch fallback reason",
        "async batch order preserved",
        "async batch error count",
        "batch planner used",
        "batch plan mode",
        "batch count planned",
        "batch primary segments",
        "batch support segments",
        "batch fallback reason",
        "evidence budget used",
        "evidence budget limit",
        "evidence budget mode",
        "evidence budget bucket counts",
        "evidence budget cutoffs",
        "evidence budget overflow",
        "evidence budget primary selected",
        "evidence budget support selected",
        "signal calibration used",
        "patch guard triggered",
        "tl;dr compressed",
        "incremental retrieval used",
        "incremental scope mode",
        "changed files considered",
        "changed regions considered",
        "unchanged files skipped",
        "unchanged chunks skipped",
        "retrieval cache hits",
        "retrieval cache misses",
        "incremental fallback reason",
        "pr segmentation used",
        "pr segment count",
        "pr primary segments",
        "pr support segments",
        "pr cross-segment",
        "pr segment summary",
        "pr segment file counts",
        "pr segment candidate counts",
        "pr segmentation fallback reason",
    }
    if parameter_norm in sprint38_always_meaningful:
        return "meaningful"
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
        if normalized == "none" and parameter_norm in {"patch targeting mode", "patch grounding mode"}:
            return "meaningful"
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


_PRIMARY_ALWAYS_VISIBLE_DIAGNOSTICS = {
    "route",
    "execution mode",
    "llm intent",
    "decision reason code",
    "answer grounding mode",
    "pr metadata used",
    "retrieval ranking mode",
    "hybrid rerank used",
    "evidence filtered",
    "evidence filter reason codes",
    "evidence budget used",
    "evidence budget limit",
    "evidence budget mode",
    "evidence budget bucket counts",
    "evidence budget cutoffs",
    "evidence budget overflow",
    "evidence budget primary selected",
    "evidence budget support selected",
    "signal calibration used",
    "patch guard triggered",
    "tl;dr compressed",
    "incremental retrieval used",
    "incremental scope mode",
    "changed files considered",
    "changed regions considered",
    "unchanged files skipped",
    "unchanged chunks skipped",
    "retrieval cache hits",
    "retrieval cache misses",
    "incremental fallback reason",
    "pr segmentation used",
    "pr segment count",
    "pr primary segments",
    "pr support segments",
    "pr cross-segment",
    "pr segment summary",
    "pr segment file counts",
    "pr segment candidate counts",
    "pr segmentation fallback reason",
    "risk level",
    "verification status",
    "check-run attempted",
    "check-run published",
    "check-run status",
    "check-run failure class",
    "check-run token source",
    "check-run event",
    "patch generation result",
    "patch validation",
    "patch targeting mode",
    "patch targeting reason",
    "patch target files",
    "patch target files total",
    "localized patch evidence",
    "review confirmed findings",
    "review possible signals",
    "review risk drivers",
    "review informational notes",
}

_LOW_VALUE_DIAGNOSTIC_TEXT = {
    "n/a",
    "none",
    "null",
    "<missing>",
    "unknown",
    "not used",
    "not_applicable",
    "no_cutoff",
}

_ASYNC_PLANNER_DIAGNOSTIC_PARAMETERS = {
    "async batch used",
    "async batch mode",
    "async batch concurrency",
    "async batch tasks total",
    "async batch tasks completed",
    "async batch fallback reason",
    "async batch order preserved",
    "async batch error count",
    "batch planner used",
    "batch plan mode",
    "batch count planned",
    "batch primary segments",
    "batch support segments",
    "batch fallback reason",
    "review batch mode",
    "review batch count",
}


def _is_low_value_diagnostic(*, parameter: str, value_text: str, state: str) -> bool:
    parameter_norm = str(parameter or "").strip().lower()
    if parameter_norm in _PRIMARY_ALWAYS_VISIBLE_DIAGNOSTICS:
        return False
    if state in {"undefined", "disabled"}:
        return True
    normalized = str(value_text or "").strip().lower()
    if normalized in _LOW_VALUE_DIAGNOSTIC_TEXT:
        return True
    if normalized in {"0", "0.0", "false", "no"}:
        return True
    if normalized.startswith("list[0]") or normalized.startswith("dict[0]"):
        return True
    return False


def _render_compact_diagnostic_groups(
    audit_summary: dict[str, Any],
    *,
    suppress_parameters: set[str] | None = None,
) -> tuple[list[str], list[tuple[str, str, str, str, str]]]:
    lines: list[str] = ["### 🧾 Runtime diagnostics"]
    secondary_rows: list[tuple[str, str, str, str, str]] = []
    suppressed = set(suppress_parameters or set())
    for group_name, rows in _diagnostic_groups(audit_summary):
        primary_rows: list[tuple[str, str]] = []
        for parameter, value, meaning in rows:
            state = _diag_state(value, parameter)
            value_text = _diag_value(value)
            parameter_norm = str(parameter or "").strip().lower()
            if parameter_norm in suppressed:
                continue
            low_value = _is_low_value_diagnostic(parameter=parameter, value_text=value_text, state=state)
            if low_value:
                secondary_rows.append((group_name, parameter, value_text, state, meaning))
                continue
            primary_rows.append((parameter, value_text))

        if not primary_rows:
            continue
        primary_rows.sort(key=lambda item: item[0].lower())
        lines.extend(["", f"#### {group_name}"])
        lines.extend(f"- {parameter}: `{value_text}`" for parameter, value_text in primary_rows)
    return lines, secondary_rows


def _diagnostic_groups(audit_summary: dict[str, Any]) -> list[tuple[str, list[tuple[str, Any, str]]]]:
    pr_files = _int(audit_summary.get("pr_changed_files_count", 0))
    if not pr_files:
        touched = audit_summary.get("touched_files", [])
        if isinstance(touched, list):
            pr_files = len([item for item in touched if str(item).strip()])
    command = str(audit_summary.get("command", "ask") or "ask").strip().lower()
    llm_used = bool(audit_summary.get("llm_used", False))
    preferred_model = str(audit_summary.get("llm_preferred_model_id", "n/a") or "n/a")
    final_model = str(
        audit_summary.get("llm_final_synthesis_model_id", audit_summary.get("llm_model_used", "not used"))
        or "not used"
    )
    llm_model_counts_raw = audit_summary.get("llm_model_counts", {})
    llm_model_counts = llm_model_counts_raw if isinstance(llm_model_counts_raw, dict) else {}
    final_retained_default = (
        llm_used
        and preferred_model not in {"", "n/a", "not used"}
        and final_model == preferred_model
    )
    final_synthesis_retained = bool(
        audit_summary.get("llm_final_synthesis_retained_preferred_model", final_retained_default)
    )
    intermediate_downgrade_default = (
        llm_used
        and final_synthesis_retained
        and any("mini" in str(model).lower() and _int(count) > 0 for model, count in llm_model_counts.items())
    )
    intermediate_downgrade = bool(
        audit_summary.get("llm_intermediate_downgrade_occurred", intermediate_downgrade_default)
    )
    intermediate_downgrade_reason = str(
        audit_summary.get("llm_intermediate_downgrade_reason", "n/a") or "n/a"
    )
    if intermediate_downgrade and intermediate_downgrade_reason == "n/a":
        fallback_reason = str(audit_summary.get("llm_model_downgrade_reason", "n/a") or "n/a")
        if fallback_reason != "n/a":
            intermediate_downgrade_reason = fallback_reason
    retrieval_rows: list[tuple[str, Any, str]] = [
        ("Retrieved candidates", _int(audit_summary.get("retrieved", 0)), "Candidates retrieved before selection."),
        ("Selected evidence", _int(audit_summary.get("selected", 0)), "Evidence items selected for response."),
        ("Retrieval passes", _int(audit_summary.get("pass_count", 1), 1), "Number of retrieval passes executed."),
        ("Top score", audit_summary.get("top_score", "n/a"), "Highest retrieval score observed."),
        (
            "Retrieval ranking mode",
            audit_summary.get("retrieval_ranking_mode", "n/a"),
            "Effective ranking strategy used for candidate ordering.",
        ),
        (
            "Hybrid rerank used",
            bool(audit_summary.get("hybrid_rerank_used", False)),
            "Whether post-retrieval hybrid reranking was applied.",
        ),
        (
            "Evidence filtered",
            _int(audit_summary.get("evidence_filtered_count", 0)),
            "Number of low-value/duplicate evidence items filtered before synthesis.",
        ),
        (
            "Evidence filter reason codes",
            audit_summary.get("evidence_filter_reason_codes", "none"),
            "Deterministic reason codes describing evidence filtering decisions.",
        ),
        (
            "Evidence budget used",
            _int(audit_summary.get("evidence_budget_used", 0)),
            "Number of candidates retained by command-aware evidence budget planning.",
        ),
        (
            "Evidence budget limit",
            _int(audit_summary.get("evidence_budget_limit", 0)),
            "Maximum candidates allowed by evidence budget policy for this command.",
        ),
        (
            "Evidence budget mode",
            audit_summary.get("evidence_budget_mode", "not_applied"),
            "Adaptive evidence-budget profile applied for this run.",
        ),
        (
            "Evidence budget bucket counts",
            audit_summary.get(
                "evidence_budget_bucket_counts",
                "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
            ),
            "Selected evidence counts by planner buckets.",
        ),
        (
            "Evidence budget cutoffs",
            audit_summary.get("evidence_budget_cutoffs", "no_cutoff"),
            "Planner cutoff reason codes when lower-priority evidence was dropped.",
        ),
        (
            "Evidence budget overflow",
            _int(audit_summary.get("evidence_budget_overflow", 0)),
            "Candidates dropped because evidence budget capacity was exceeded.",
        ),
        (
            "Evidence budget primary selected",
            _int(audit_summary.get("evidence_budget_primary_selected", 0)),
            "Selected evidence from changed primary/secondary buckets.",
        ),
        (
            "Evidence budget support selected",
            _int(audit_summary.get("evidence_budget_support_selected", 0)),
            "Selected evidence retained as supporting context.",
        ),
        (
            "Ultra-large PR mode active",
            bool(audit_summary.get("ultra_large_pr_mode_active", False)),
            "Whether deterministic ultra-large PR bounded-coverage mode was activated.",
        ),
        (
            "Ultra-large PR mode level",
            audit_summary.get("ultra_large_pr_mode_level", "normal"),
            "Activation severity level for ultra-large PR handling.",
        ),
        (
            "Ultra-large PR activation reason",
            audit_summary.get("ultra_large_pr_mode_reason", "none"),
            "Deterministic trigger reason(s) for ultra-large PR mode activation.",
        ),
        (
            "Ultra-large PR depth strategy",
            audit_summary.get("ultra_large_pr_depth_strategy", "standard"),
            "Depth strategy used when ultra-large PR mode is active.",
        ),
        (
            "Ultra-large PR synthesis window cap",
            _int(audit_summary.get("ultra_large_pr_synthesis_window_cap", 0)),
            "Per-command synthesis window cap applied under ultra-large PR mode.",
        ),
        (
            "Ultra-large PR primary coverage",
            audit_summary.get("ultra_large_pr_primary_coverage_summary", "none"),
            "Primary/deep coverage summary under ultra-large PR mode.",
        ),
        (
            "Ultra-large PR bounded coverage",
            audit_summary.get("ultra_large_pr_bounded_coverage_summary", "none"),
            "Bounded/secondary coverage summary under ultra-large PR mode.",
        ),
        (
            "Ultra-large PR coverage statement",
            audit_summary.get("ultra_large_pr_coverage_statement", "n/a"),
            "Human-readable bounded-coverage statement for ultra-large PR mode.",
        ),
        (
            "Signal calibration used",
            bool(audit_summary.get("signal_calibration_used", False)),
            "Whether review security-like signals were calibrated before final buckets.",
        ),
        (
            "Patch guard triggered",
            bool(audit_summary.get("patch_guard_triggered", False)),
            "Whether early placeholder/generic patch guard was triggered.",
        ),
        (
            "TL;DR compressed",
            bool(audit_summary.get("tldr_compressed", False)),
            "Whether compact summary compression removed scaffold/repetition.",
        ),
        (
            "PR changed files",
            pr_files,
            "Count of changed files from PR metadata (if available).",
        ),
        (
            "PR segmentation used",
            bool(audit_summary.get("pr_segmentation_used", False)),
            "Whether hierarchical PR segmentation was computed for this run.",
        ),
        (
            "PR segment count",
            _int(audit_summary.get("pr_segment_count", 0)),
            "Number of segment/subsystem groups detected in changed files.",
        ),
        (
            "PR primary segments",
            audit_summary.get("pr_primary_segments", "none"),
            "Primary PR segments where substantive changes are concentrated.",
        ),
        (
            "PR support segments",
            audit_summary.get("pr_support_segments", "none"),
            "Supporting segments (tests/docs/workflow/config) around primary changes.",
        ),
        (
            "PR cross-segment",
            bool(audit_summary.get("pr_cross_segment", False)),
            "Whether PR spans multiple major segments/subsystems.",
        ),
        (
            "PR segment summary",
            audit_summary.get("pr_segment_summary", "none"),
            "Compact hierarchical PR segmentation summary.",
        ),
        (
            "PR segment file counts",
            audit_summary.get("pr_segment_file_counts", "none"),
            "File counts per segment class in this PR.",
        ),
        (
            "PR segment candidate counts",
            audit_summary.get("pr_segment_candidate_counts", "none"),
            "Selected candidate/evidence counts per segment class.",
        ),
        (
            "PR segmentation fallback reason",
            audit_summary.get("pr_segmentation_fallback_reason", "none"),
            "Reason for deterministic segmentation fallback when applicable.",
        ),
        (
            "Incremental retrieval used",
            bool(audit_summary.get("incremental_retrieval_used", False)),
            "Whether changed-region/file-first incremental retrieval scope was applied.",
        ),
        (
            "Incremental scope mode",
            audit_summary.get("incremental_scope_mode", "fallback_full"),
            "Effective incremental scope mode selected for this run.",
        ),
        (
            "Changed files considered",
            _int(audit_summary.get("changed_files_considered", 0)),
            "Changed files included in incremental retrieval scope.",
        ),
        (
            "Changed regions considered",
            _int(audit_summary.get("changed_regions_considered", 0)),
            "Changed diff hunks considered for incremental scope decisions.",
        ),
        (
            "Unchanged files skipped",
            _int(audit_summary.get("unchanged_files_skipped", 0)),
            "Unchanged files skipped by incremental scope narrowing.",
        ),
        (
            "Unchanged chunks skipped",
            _int(audit_summary.get("unchanged_chunks_skipped", 0)),
            "Unchanged chunks skipped by incremental scope narrowing.",
        ),
        (
            "Retrieval cache hits",
            _int(audit_summary.get("retrieval_cache_hits", 0)),
            "File-hash reuse hits from incremental retrieval cache snapshot.",
        ),
        (
            "Retrieval cache misses",
            _int(audit_summary.get("retrieval_cache_misses", 0)),
            "File-hash reuse misses from incremental retrieval cache snapshot.",
        ),
        (
            "Incremental fallback reason",
            audit_summary.get("incremental_fallback_reason", "none"),
            "Reason incremental scope fell back to full retrieval when applicable.",
        ),
        (
            "Retrieval snapshot cache used",
            bool(audit_summary.get("retrieval_snapshot_cache_used", False)),
            "Whether PR-state retrieval snapshot cache was eligible for this run.",
        ),
        (
            "Retrieval snapshot cache hit",
            bool(audit_summary.get("retrieval_snapshot_cache_hit", False)),
            "Whether a retrieval snapshot was reused for this PR state.",
        ),
        (
            "Retrieval snapshot key kind",
            audit_summary.get("retrieval_snapshot_cache_key_kind", "not_applicable"),
            "Authoritative PR-state identity used for snapshot cache keying.",
        ),
        (
            "Retrieval snapshot miss reason",
            audit_summary.get("retrieval_snapshot_cache_miss_reason", "not_applicable"),
            "Deterministic reason snapshot reuse was not applied.",
        ),
        (
            "Retrieval snapshot age (s)",
            _int(audit_summary.get("retrieval_snapshot_cache_age_s", 0)),
            "Age in seconds of reused retrieval snapshot (0 for misses/new snapshots).",
        ),
        (
            "Batch planner used",
            bool(audit_summary.get("batch_planner_used", False)),
            "Whether segment-aware batch planner was applied before batch execution.",
        ),
        (
            "Batch plan mode",
            audit_summary.get("batch_plan_mode", "not_applied"),
            "Planner mode for deterministic batch ordering and grouping.",
        ),
        (
            "Batch count planned",
            _int(audit_summary.get("batch_count_planned", 0)),
            "Total batches emitted by planner before execution caps.",
        ),
        (
            "Batch primary segments",
            audit_summary.get("batch_primary_segments", "none"),
            "Primary segments prioritized by planner for early execution.",
        ),
        (
            "Batch support segments",
            audit_summary.get("batch_support_segments", "none"),
            "Support segments scheduled after primary segments.",
        ),
        (
            "Batch fallback reason",
            audit_summary.get("batch_fallback_reason", "not_applicable"),
            "Reason planner fell back to original ordering when segmentation was unavailable.",
        ),
        (
            "Async batch used",
            bool(audit_summary.get("async_batch_used", False)),
            "Whether bounded async execution was used for multi-batch orchestration.",
        ),
        (
            "Async batch mode",
            audit_summary.get("async_batch_mode", "sequential"),
            "Effective execution mode for batch orchestration (async or deterministic sequential fallback).",
        ),
        (
            "Async batch concurrency",
            _int(audit_summary.get("async_batch_concurrency", 1)),
            "Configured bounded concurrency for async batch execution.",
        ),
        (
            "Async batch tasks total",
            _int(audit_summary.get("async_batch_tasks_total", 0)),
            "Total batch tasks planned for orchestration.",
        ),
        (
            "Async batch tasks completed",
            _int(audit_summary.get("async_batch_tasks_completed", 0)),
            "Batch tasks completed including fallback recoveries.",
        ),
        (
            "Async batch fallback reason",
            audit_summary.get("async_batch_fallback_reason", "not_applicable"),
            "Deterministic reason when async orchestration falls back to sequential execution.",
        ),
        (
            "Async batch order preserved",
            bool(audit_summary.get("async_batch_order_preserved", True)),
            "Whether final merged batch outputs preserved original input order.",
        ),
        (
            "Async batch error count",
            _int(audit_summary.get("async_batch_error_count", 0)),
            "Count of batch-task errors recovered through deterministic fallback.",
        ),
    ]
    if command == "fix":
        retrieval_rows.extend(
            [
                (
                    "Patch target files",
                    _int(
                        audit_summary.get(
                            "patch_target_files_selected",
                            audit_summary.get("patch_target_files_count", 0),
                        )
                    ),
                    "Number of files targeted by patch generation context.",
                ),
                (
                    "Patch target files total",
                    _int(audit_summary.get("patch_target_files_total", 0)),
                    "Total candidate files considered before patch-target narrowing.",
                ),
                (
                    "Patch targeting mode",
                    audit_summary.get("patch_targeting_mode", "n/a"),
                    "Localized patch-target selection strategy outcome.",
                ),
                (
                    "Patch targeting reason",
                    audit_summary.get("patch_targeting_reason", "n/a"),
                    "Why patch targets were narrowed or no patch target was selected.",
                ),
                (
                    "Patch grounding mode",
                    audit_summary.get("patch_grounding_mode", "n/a"),
                    "How patch grounding context was assembled.",
                ),
                (
                    "Patch generation result",
                    audit_summary.get("patch_generation_result", "n/a"),
                    "Patch generation classification before publish.",
                ),
                (
                    "Localized patch evidence",
                    _int(audit_summary.get("localized_patch_evidence_count", 0)),
                    "Count of localized evidence/query signals used for patch targeting.",
                ),
                (
                    "Patch validation",
                    audit_summary.get("patch_validation_result", "n/a"),
                    "Patch validation classification before publication.",
                ),
                (
                    "Patch governance class",
                    audit_summary.get("patch_governance_class", "not_applicable"),
                    "Governed remediation class for patch/no_patch decision.",
                ),
                (
                    "Patch risk class",
                    audit_summary.get("patch_risk_class", "n/a"),
                    "Aggregated remediation risk class from evidence verdict context.",
                ),
                (
                    "Patch proof threshold",
                    audit_summary.get("patch_proof_threshold_status", "not_applicable"),
                    "Whether minimum localized proof threshold was met for patching.",
                ),
                (
                    "Patch verification preconditions",
                    audit_summary.get("patch_verification_preconditions", "not_applicable"),
                    "Verification gate status required before safe patch proposal.",
                ),
                (
                    "Ultra-large PR patch governance downgraded",
                    bool(audit_summary.get("ultra_large_pr_patch_governance_downgraded", False)),
                    "Whether patch governance was downgraded due to bounded ultra-large PR coverage.",
                ),
                (
                    "Ultra-large PR patch governance reason",
                    audit_summary.get("ultra_large_pr_patch_governance_reason", "n/a"),
                    "Reason patch governance was downgraded under ultra-large PR constraints.",
                ),
            ]
        )
    elif command == "review":
        retrieval_rows.extend(
            [
                (
                    "Review confirmed findings",
                    _int(audit_summary.get("review_confirmed_findings_count", 0)),
                    "Count of findings with evidence-backed validation.",
                ),
                (
                    "Review possible signals",
                    _int(audit_summary.get("review_possible_signals_count", 0)),
                    "Count of downgraded heuristic signals without strong evidence.",
                ),
                (
                    "Review risk drivers",
                    _int(audit_summary.get("review_risk_drivers_count", 0)),
                    "Count of explicit reasons driving current risk level.",
                ),
                (
                    "Review informational notes",
                    _int(audit_summary.get("review_informational_notes_count", 0)),
                    "Count of non-risk informational notes in review output.",
                ),
                (
                    "Review generation result",
                    audit_summary.get("review_generation_result", "n/a"),
                    "Review synthesis outcome after compaction/batching safeguards.",
                ),
                (
                    "Review compacted",
                    bool(audit_summary.get("review_compacted", False)),
                    "Whether final review context was compacted.",
                ),
                (
                    "Review batch mode",
                    bool(audit_summary.get("review_batch_mode", False)),
                    "Whether review used hierarchical batch synthesis.",
                ),
                (
                    "Review batch count",
                    _int(audit_summary.get("review_batch_count", 0)),
                    "Executed review batch calls count.",
                ),
            ]
        )
    else:
        retrieval_rows.extend(
            [
                (
                    "PR metadata used",
                    bool(audit_summary.get("pr_metadata_used", False)),
                    "Whether authoritative PR metadata grounded this answer.",
                ),
                (
                    "Answer grounding mode",
                    audit_summary.get("answer_grounding_mode", "retrieval"),
                    "Primary grounding source for ask/explain output.",
                ),
            ]
        )

    return [
        (
            "A. Decision summary",
            [
                ("Route", _route(audit_summary), "Final TKYA route used for this response."),
                (
                    "Execution mode",
                    _display_execution_mode(audit_summary),
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
                    "TopoCore backend requested",
                    audit_summary.get("requested_backend", "n/a"),
                    "Requested TopoCore backend policy after workflow and action inputs are applied.",
                ),
                (
                    "TopoCore backend resolved",
                    audit_summary.get("resolved_backend", "n/a"),
                    "Effective TopoCore backend after local selector resolution or safe fallback.",
                ),
                (
                    "TopoCore backend mode",
                    audit_summary.get("backend_mode", "n/a"),
                    "Backend policy mode recorded by the local TopoCore selector.",
                ),
                (
                    "TopoCore fallback used",
                    audit_summary.get("fallback_used", "n/a"),
                    "Whether the TopoCore selector fell back from v6 to v5.",
                ),
                (
                    "TopoCore fallback reason",
                    audit_summary.get("fallback_reason", "n/a"),
                    "Sanitized reason for TopoCore fallback when it occurs.",
                ),
                (
                    "Scope status",
                    audit_summary.get("scope_status", "n/a"),
                    "Explicit scoped-command status for unsupported or report-only contexts.",
                ),
                (
                    "Patch authorized",
                    audit_summary.get("patch_authorized", "n/a"),
                    "Whether command governance authorized any patch action.",
                ),
                (
                    "Patch applied",
                    audit_summary.get("patch_applied", "n/a"),
                    "Whether any patch was actually applied.",
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
                (
                    "Security scope",
                    audit_summary.get("security_scope", "n/a"),
                    "Security zone applied by orchestration policy.",
                ),
                (
                    "Security outcome",
                    audit_summary.get("security_outcome", "n/a"),
                    "Result of security policy evaluation.",
                ),
                (
                    "Security reason code",
                    audit_summary.get("security_reason_code", "n/a"),
                    "Machine-readable security policy reason.",
                ),
                (
                    "Skip reason code",
                    audit_summary.get("skip_reason_code", "n/a"),
                    "Machine-readable reason when command was intentionally skipped.",
                ),
                (
                    "Skip reason",
                    audit_summary.get("skip_reason_short", "n/a"),
                    "Usersafe explanation for intentional skip outcome.",
                ),
                (
                    "Skip visible to user",
                    bool(audit_summary.get("skip_visible_to_user", False)),
                    "Whether skip reason was posted in the user-facing comment.",
                ),
            ],
        ),
        (
            "C. LLM",
            [
                ("LLM used", bool(audit_summary.get("llm_used", False)), "Whether LLM generation was executed."),
                (
                    "Preferred model",
                    audit_summary.get("llm_preferred_model_id", "n/a"),
                    "Model selected by complexity policy before governor/runtime adjustments.",
                ),
                ("Model", audit_summary.get("llm_model_used", "n/a"), "Effective LLM model id."),
                (
                    "Models used",
                    _llm_models_used_summary(audit_summary),
                    "Per-model call distribution for this run.",
                ),
                (
                    "Final synthesis model",
                    audit_summary.get(
                        "llm_final_synthesis_model_id",
                        audit_summary.get("llm_model_used", "n/a"),
                    ),
                    "Model that produced final user-facing synthesis text.",
                ),
                (
                    "Final synthesis retained preferred model",
                    final_synthesis_retained,
                    "Whether final synthesis kept the preferred model selection.",
                ),
                (
                    "Intermediate downgrade",
                    intermediate_downgrade,
                    "Whether auxiliary calls used downgraded model while final synthesis stayed preferred.",
                ),
                (
                    "Intermediate downgrade reason",
                    intermediate_downgrade_reason,
                    "Reason for intermediate-only model downgrade when it occurred.",
                ),
                (
                    "Model selection reason",
                    audit_summary.get("llm_model_selection_reason", "n/a"),
                    "Why this model tier was selected.",
                ),
                (
                    "Model downgrade reason",
                    audit_summary.get("llm_model_downgrade_reason", "n/a"),
                    "Runtime/governor reason for downgrade from preferred model.",
                ),
                (
                    "Retained preferred model reason",
                    audit_summary.get("llm_retained_preferred_model_reason", "n/a"),
                    "Why preferred model was retained despite downgrade opportunity.",
                ),
                (
                    "Downgrade threshold",
                    audit_summary.get("llm_downgrade_threshold_used", "n/a"),
                    "Remaining-request threshold used for downgrade decisions.",
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
            retrieval_rows,
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
                    "Check-run attempted",
                    bool(audit_summary.get("check_run_attempted", False)),
                    "Whether GitHub Checks API publication was attempted in this run.",
                ),
                (
                    "Check-run published",
                    bool(audit_summary.get("check_run_published", False)),
                    "Whether check-run publication succeeded.",
                ),
                (
                    "Check-run status",
                    audit_summary.get("check_run_status_code", "n/a"),
                    "HTTP status code (or deterministic marker) for check publication.",
                ),
                (
                    "Check-run failure class",
                    audit_summary.get("check_run_failure_class", "n/a"),
                    "Normalized failure class for check publication failures.",
                ),
                (
                    "Check-run token source",
                    audit_summary.get("check_run_token_source", "n/a"),
                    "Token path used for check publication.",
                ),
                (
                    "Check-run event",
                    audit_summary.get("check_run_event_name", "n/a"),
                    "GitHub event context for check publication.",
                ),
                (
                    "Check-run required permissions",
                    audit_summary.get("check_run_required_permissions_header", "n/a"),
                    "Accepted permissions header from GitHub response when available.",
                ),
                (
                    "Check-run skip reason",
                    audit_summary.get("check_run_skip_reason", "n/a"),
                    "Reason check publication was skipped in this run.",
                ),
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
                    _normalized_budget_action(
                        budget_action=str(audit_summary.get("llm_budget_action", "n/a") or "n/a"),
                        retained_reason=str(
                            audit_summary.get("llm_retained_preferred_model_reason", "n/a") or "n/a"
                        ),
                        intermediate_downgrade_occurred=intermediate_downgrade,
                        final_synthesis_retained_preferred=final_synthesis_retained,
                    ),
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


def _render_diagnostic_table(
    audit_summary: dict[str, Any],
    *,
    suppress_async_planner_rows: bool = False,
) -> list[str]:
    if not _verbose_diagnostics_enabled():
        return []
    suppressed_parameters = _ASYNC_PLANNER_DIAGNOSTIC_PARAMETERS if suppress_async_planner_rows else set()
    lines, secondary_rows = _render_compact_diagnostic_groups(
        audit_summary,
        suppress_parameters=suppressed_parameters,
    )
    if secondary_rows:
        secondary_rows.sort(key=lambda item: (item[0].lower(), item[1].lower()))
        lines.extend(["", "### Secondary diagnostics", ""])
        current_group = ""
        max_rows = 48
        for group_name, parameter, value_text, state, _meaning in secondary_rows[:max_rows]:
            if group_name != current_group:
                current_group = group_name
                if len(lines) > 0 and lines[-1] != "":
                    lines.append("")
                lines.append(f"**{group_name}**")
            lines.append(f"- {parameter}: `{value_text}` ({state})")
        if len(secondary_rows) > max_rows:
            lines.append(f"- +{len(secondary_rows) - max_rows} additional rows omitted for compactness.")
        lines.append("")
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


def _compact_segment_summary(audit_summary: dict[str, Any]) -> str:
    summary = str(audit_summary.get("pr_segment_summary", "none") or "none").strip()
    if summary and summary.lower() != "none":
        return summary
    primary = str(audit_summary.get("pr_primary_segments", "none") or "none").strip()
    support = str(audit_summary.get("pr_support_segments", "none") or "none").strip()
    cross_segment = "yes" if bool(audit_summary.get("pr_cross_segment", False)) else "no"
    if primary.lower() == "none" and support.lower() == "none":
        return "not_available"
    return f"primary={primary}; support={support}; cross_segment={cross_segment}"


def _has_meaningful_budget(audit_summary: dict[str, Any]) -> bool:
    mode = str(audit_summary.get("evidence_budget_mode", "not_applied") or "not_applied").strip().lower()
    used = _int(audit_summary.get("evidence_budget_used", 0))
    return mode not in {"", "not_applied"} or used > 0


def _has_meaningful_incremental(audit_summary: dict[str, Any]) -> bool:
    used = bool(audit_summary.get("incremental_retrieval_used", False))
    mode = str(audit_summary.get("incremental_scope_mode", "fallback_full") or "fallback_full").strip().lower()
    return used or mode not in {"", "fallback_full", "not_applicable"}


def _render_secondary_diagnostics_details(audit_summary: dict[str, Any]) -> list[str]:
    _, secondary_rows = _render_compact_diagnostic_groups(audit_summary)
    if not secondary_rows:
        return []
    secondary_rows.sort(key=lambda item: (item[0].lower(), item[1].lower()))
    lines: list[str] = [
        "### Secondary diagnostics",
        "",
    ]
    current_group = ""
    max_rows = 40
    for group_name, parameter, value_text, state, _meaning in secondary_rows[:max_rows]:
        if group_name != current_group:
            current_group = group_name
            lines.append(f"**{group_name}**")
        lines.append(f"- {parameter}: `{value_text}` ({state})")
    if len(secondary_rows) > max_rows:
        lines.append(f"- +{len(secondary_rows) - max_rows} additional rows omitted.")
    lines.append("")
    return lines


def _render_async_batch_lines(audit_summary: dict[str, Any], *, command: str) -> list[str]:
    command_norm = str(command or "").strip().lower()
    if command_norm not in {"review", "fix"}:
        return []
    review_batch_mode = bool(audit_summary.get("review_batch_mode", False))
    review_batch_count = _int(audit_summary.get("review_batch_count", 0))
    planner_used = bool(audit_summary.get("batch_planner_used", False))
    planner_mode = str(audit_summary.get("batch_plan_mode", "not_applied") or "not_applied")
    planner_count = _int(audit_summary.get("batch_count_planned", 0))
    planner_primary = str(audit_summary.get("batch_primary_segments", "none") or "none")
    planner_support = str(audit_summary.get("batch_support_segments", "none") or "none")
    planner_fallback = str(audit_summary.get("batch_fallback_reason", "not_applicable") or "not_applicable")
    async_used = bool(audit_summary.get("async_batch_used", False))
    tasks_total = _int(audit_summary.get("async_batch_tasks_total", 0))
    mode = str(audit_summary.get("async_batch_mode", "sequential") or "sequential")
    tasks_completed = _int(audit_summary.get("async_batch_tasks_completed", 0))
    lines = ["### Async batch orchestration"]
    if review_batch_mode or review_batch_count > 0:
        lines.extend(
            [
                f"- Review batch mode: `{'yes' if review_batch_mode else 'no'}`",
                f"- Review batch count: `{review_batch_count}`",
            ]
        )
    lines.extend(
        [
            f"- Planner used: `{'yes' if planner_used else 'no'}`",
            f"- Plan mode: `{planner_mode}`",
            f"- Planned batches: `{planner_count}`",
            f"- Primary segments: `{planner_primary}`",
            f"- Support segments: `{planner_support}`",
            f"- Used: `{'yes' if async_used else 'no'}`",
            f"- Mode: `{mode}`",
            f"- Concurrency: `{_int(audit_summary.get('async_batch_concurrency', 1))}`",
            f"- Tasks: `{tasks_completed}/{tasks_total}`",
            f"- Order preserved: `{'yes' if bool(audit_summary.get('async_batch_order_preserved', True)) else 'no'}`",
            f"- Error count: `{_int(audit_summary.get('async_batch_error_count', 0))}`",
        ]
    )
    async_fallback = str(audit_summary.get("async_batch_fallback_reason", "not_applicable") or "not_applicable")
    lines.append(f"- Fallback reason: `{async_fallback}`")
    lines.append(f"- Planner fallback reason: `{planner_fallback}`")
    lines.append("")
    return lines


def _render_runtime_details_block(*, title: str, lines: list[str]) -> list[str]:
    compact_lines = [str(line) for line in lines]
    while compact_lines and not compact_lines[0].strip():
        compact_lines.pop(0)
    while compact_lines and not compact_lines[-1].strip():
        compact_lines.pop()
    if not any(line.strip() for line in compact_lines):
        return []
    return [
        "<details>",
        f"<summary>{title}</summary>",
        "",
        *compact_lines,
        "",
        "</details>",
    ]


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
    if command == "locate":
        route = "LOCATE"
    elif command == "explain":
        route = "EXPLAIN"
    evidence_block = _evidence_lines(evidence, repo=repo, sha=sha, audit_summary=audit_summary)
    route_header = "### ✅ Answer"
    if route == "WAIT":
        route_header = "### ⏳ Needs verification"
    elif route == "REFUSE":
        route_header = "### 🚫 Refused"
    elif route == "BLOCK":
        route_header = "### 🛑 Blocked"

    verification_status = _verification_status(audit_summary)
    selected_evidence = _int(audit_summary.get("selected", len(evidence)))
    grounding_mode = str(audit_summary.get("answer_grounding_mode", "retrieval") or "retrieval")
    segment_summary = _compact_segment_summary(audit_summary)

    sections: list[str] = [route_header]
    if command == "locate":
        promoted_backend_lines = (
            [*_runtime_backend_evidence_lines(audit_summary), ""]
            if _has_pr_backend_evidence_context(audit_summary)
            else []
        )
        sections.extend(
            [
                "Top locations found for the query:",
                "",
                "### 🧭 Run summary",
                f"- Route: `{route}`",
                f"- Selected evidence: `{selected_evidence}`",
                f"- Verification: `{verification_status}`",
                "",
                *promoted_backend_lines,
            ]
        )
        detail_lines = [
            *_retrieval_snapshot_lines(audit_summary),
            *_ultra_large_pr_mode_lines(audit_summary, command=command),
            "### 📊 Evidence",
            *evidence_block,
            "",
            *_evidence_context_summary_lines(audit_summary),
            "### ✅ Next steps",
            f"- {next_steps.strip() or 'Open evidence links and verify logic'}",
            "",
            *_verification_lines(audit_summary),
            "",
            *_llm_lines(audit_summary),
            "",
            *_embeddings_lines(audit_summary),
            "",
            "### 🧭 Route details",
            *_mode_lines(audit_summary),
            *_render_diagnostic_table(audit_summary),
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines({**audit_summary, "route_final": route}),
            *_version_backend_lines(audit_summary),
            "",
            _audit_note(),
        ]
        sections.extend(_render_runtime_details_block(title="Evidence and diagnostics", lines=detail_lines))
    else:
        promoted_backend_lines = (
            ["", *_runtime_backend_evidence_lines(audit_summary)]
            if _has_pr_backend_evidence_context(audit_summary)
            else []
        )
        sections.extend(
            [
                answer_text.strip() or "No answer generated.",
                "",
                "### 🧭 Run summary",
                f"- Route: `{route}`",
                f"- Grounding: `{grounding_mode}`",
                f"- Segment summary: `{segment_summary}`",
                f"- Selected evidence: `{selected_evidence}`",
                f"- Verification: `{verification_status}`",
                *promoted_backend_lines,
            ]
        )
        sections.append("")
        detail_lines = [
            *_retrieval_snapshot_lines(audit_summary),
            *_ultra_large_pr_mode_lines(audit_summary, command=command),
            "### 📊 Evidence",
            *evidence_block,
            "",
            *_evidence_context_summary_lines(audit_summary),
            "### ✅ Next steps",
            f"- {next_steps.strip() or 'Open evidence links and verify logic'}",
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
            *_pr_segments_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines({**audit_summary, "route_final": route}),
            *_version_backend_lines(audit_summary),
            "",
            _audit_note(),
        ]
        sections.extend(_render_runtime_details_block(title="Evidence and diagnostics", lines=detail_lines))
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
            "### 🧾 Audit anchors",
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
            "### 🧾 Audit anchors",
            f"- route: {_route(audit_summary)}",
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
            "### 🧾 Audit anchors",
            f"- route: {_route(audit_summary)}",
            *_version_backend_lines(audit_summary),
            "",
            *_render_diagnostic_table(audit_summary),
            "",
            _audit_note(),
        ]
    )


def render_scoped_command_markdown(
    *,
    title: str,
    message: str,
    audit_summary: dict[str, Any],
    next_steps: list[str] | None = None,
) -> str:
    next_step_lines = [str(item).strip() for item in (next_steps or []) if str(item).strip()]
    if not next_step_lines:
        next_step_lines = ["Use a supported context and rerun the command."]
    sections = [
        title.strip() or "### ⏳ Scoped command status",
        message.strip() or "This command is intentionally scoped in the current context.",
        "",
        *_runtime_backend_evidence_lines(audit_summary),
        "",
        "### ✅ Next steps",
        *(f"- {item}" for item in next_step_lines),
        "",
        "### 🧭 Scope details",
        *_mode_lines(audit_summary),
        "",
        *_render_diagnostic_table(audit_summary),
        "",
        "### 🧾 Audit anchors",
        *_version_backend_lines(audit_summary),
        "",
        _audit_note(),
    ]
    return "\n".join(sections)


_LEAKED_SECRET_SIGNAL_PHRASE = "possible secret leakage in patch"


def _strip_review_secret_signal_leak(text: str) -> str:
    lines = [line for line in str(text or "").splitlines() if _LEAKED_SECRET_SIGNAL_PHRASE not in line.lower()]
    normalized = "\n".join(lines).strip()
    if not normalized:
        return ""
    return normalized


def _sanitize_review_possible_signals(possible_signals: list[str]) -> list[str]:
    sanitized: list[str] = []
    for raw in possible_signals:
        item = str(raw or "").strip()
        if not item:
            continue
        if _LEAKED_SECRET_SIGNAL_PHRASE in item.lower():
            continue
        sanitized.append(item)
    return list(dict.fromkeys(sanitized))


def _sanitize_review_user_lines(values: list[str]) -> list[str]:
    sanitized: list[str] = []
    for raw in values:
        item = str(raw or "").strip()
        if not item:
            continue
        if _LEAKED_SECRET_SIGNAL_PHRASE in item.lower():
            continue
        sanitized.append(item)
    return list(dict.fromkeys(sanitized))


def render_review_markdown(
    *,
    review: dict[str, Any],
    verification_report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    files_block = review.get("files_block", [])
    if not isinstance(files_block, list):
        files_block = []
    files_block = _label_touched_file_lines(files_block, audit_summary)
    confirmed_findings = review.get("confirmed_findings", [])
    if not isinstance(confirmed_findings, list):
        confirmed_findings = []
    possible_signals = review.get("possible_signals", [])
    if not isinstance(possible_signals, list):
        possible_signals = []
    possible_signals = _sanitize_review_possible_signals(possible_signals)
    recommendations = review.get("recommendations", review.get("suggested_tests", []))
    if not isinstance(recommendations, list):
        recommendations = []
    recommendations = _sanitize_review_user_lines(recommendations)
    informational_notes = review.get("informational_notes", review.get("notes", []))
    if not isinstance(informational_notes, list):
        informational_notes = []
    informational_notes = _sanitize_review_user_lines(informational_notes)
    risk_drivers = review.get("risk_drivers", [])
    if not isinstance(risk_drivers, list):
        risk_drivers = []
    risk_drivers = _sanitize_review_user_lines(risk_drivers)
    summary_text = _strip_review_secret_signal_leak(
        str(review.get("summary_text", "No summary available.")).strip()
    )
    summary_text, tldr_compressed = _compress_review_summary_with_flag(
        summary_text,
        risk_drivers=risk_drivers,
        informational_notes=informational_notes,
    )
    audit_summary["tldr_compressed"] = bool(tldr_compressed)
    risk_level = str(review.get("risk_level", "low") or "low").upper()
    if not summary_text:
        summary_text = "Review completed."
    pseudo_confirmed_markers = {
        "no obvious high-risk patterns detected",
        "no confirmed high-risk findings detected",
        "no evidence-backed high-risk findings detected",
    }
    evidence_map = _confirmed_evidence_map(review)
    confirmed_block = []
    for raw_item in confirmed_findings:
        item = str(raw_item).strip()
        if not item or item.lower() in pseudo_confirmed_markers:
            continue
        rendered = _render_confirmed_finding_with_evidence(
            item,
            evidence_map=evidence_map,
        )
        if rendered:
            confirmed_block.append(f"- {rendered}")
    confirmed_section = (
        ["", "### ⚠️ Confirmed findings", *confirmed_block]
        if confirmed_block
        else ["", "Confirmed findings: none."]
    )
    possible_block = [f"- {item}" for item in possible_signals] if possible_signals else ["- None."]
    risk_driver_block = (
        [f"- {item}" for item in risk_drivers[:4] if str(item).strip()]
        if risk_drivers
        else ["- No material risk drivers identified."]
    )
    default_recommendation = (
        "- Proceed with standard CI checks before merge."
        if risk_level == "LOW" and not confirmed_block
        else "- Run standard CI checks before merge."
    )
    segment_summary = _compact_segment_summary(audit_summary)
    verification_status = str(
        verification_report.get("summary", verification_report.get("overall", _verification_status(audit_summary)))
        or _verification_status(audit_summary)
    ).strip()
    promoted_backend_lines = (
        ["", *_runtime_backend_evidence_lines(audit_summary)]
        if _has_pr_backend_evidence_context(audit_summary)
        else []
    )
    sections = [
        "### ✅ PR Review",
        f"TL;DR: {summary_text}",
        f"Risk level: **{risk_level}**",
        (
        f"- Decision snapshot: findings `{len(confirmed_block)}` | "
        f"signals `{len(possible_signals)}` | notes `{len(informational_notes)}`"
        ),
        f"- Segment summary: `{segment_summary}`",
        f"- Verification: `{verification_status}`",
        *promoted_backend_lines,
    ]
    sections.extend(
        [
            "",
            "### ✅ Recommendations",
            *([f"- {item}" for item in recommendations[:3]] if recommendations else [default_recommendation]),
            "",
        ]
    )

    detail_lines = [
        *_retrieval_snapshot_lines(audit_summary),
        *_runtime_provenance_lines(audit_summary, command="review"),
        *_review_delta_lines(audit_summary),
        *_ultra_large_pr_mode_lines(audit_summary, command="review"),
        *_render_async_batch_lines(audit_summary, command="review"),
        "### 🧩 Decision cards",
        "",
        "Risk drivers:",
        *risk_driver_block,
        "",
        "### 🗂️ Touched files",
        *(files_block[:6] if files_block else ["- No changed files detected."]),
        *([f"- +{len(files_block) - 6} more"] if len(files_block) > 6 else []),
        "",
        *_evidence_context_summary_lines(audit_summary),
        *confirmed_section,
        "",
        "### 📌 Evidence verdicts",
        *_evidence_verdict_lines(review),
        "",
        "### 🟡 Possible signals",
        *possible_block,
        "",
        "### ℹ️ Informational notes",
        *([f"- {item}" for item in informational_notes[:6]] if informational_notes else ["- None."]),
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
        *_render_diagnostic_table(audit_summary, suppress_async_planner_rows=True),
        "",
        "### 🧾 Audit anchors",
        *_version_backend_lines(audit_summary),
        "",
        _audit_note(),
    ]
    sections.extend(_render_runtime_details_block(title="Evidence and diagnostics", lines=detail_lines))
    return "\n".join(sections)


def _fix_status_label(*, review: dict[str, Any], audit_summary: dict[str, Any]) -> str:
    explicit = str(audit_summary.get("fix_status", "") or "").strip().upper()
    if explicit:
        return explicit
    scope_status = str(audit_summary.get("scope_status", "") or "").strip().lower()
    if scope_status.startswith("unsupported_"):
        return "UNSUPPORTED_SCOPE"
    if bool(audit_summary.get("fix_request_requires_mutation", False)):
        return "BLOCKED_BY_SAFETY"
    if bool(audit_summary.get("fix_request_is_vague", False)):
        return "NEEDS_MORE_INFORMATION"
    patch_generation_result = str(audit_summary.get("patch_generation_result", "n/a") or "n/a").strip().lower()
    selected = _int(audit_summary.get("selected", 0))
    if patch_generation_result in {"provider_failed", "patch_missing"}:
        return "ERROR_SANITIZED"
    if patch_generation_result == "patch_validation_failed":
        return "NEEDS_MORE_INFORMATION"
    if patch_generation_result == "no_patch" and selected <= 0:
        return "NO_ACTION_NEEDED"
    if isinstance(review.get("risks", []), list):
        risks = [str(item).strip().lower() for item in review.get("risks", []) if str(item).strip()]
        if risks == ["no obvious high-risk patterns detected"] and selected <= 0:
            return "NO_ACTION_NEEDED"
    return "PROPOSAL_READY"


def _fix_confidence_label(*, review: dict[str, Any], audit_summary: dict[str, Any]) -> str:
    if bool(audit_summary.get("fix_request_requires_mutation", False)):
        return "high"
    localized = _int(audit_summary.get("localized_patch_evidence_count", 0))
    selected = _int(audit_summary.get("selected", 0))
    if localized > 0 or selected >= 3:
        return "high"
    if selected > 0:
        return "medium"
    risks = review.get("risks", [])
    if isinstance(risks, list) and risks:
        return "medium"
    return "low"


def _fix_candidate_issue_lines(*, review: dict[str, Any], status_label: str) -> list[str]:
    if status_label == "BLOCKED_BY_SAFETY":
        return [
            "The request asked for mutation behavior that is disabled in this product path.",
        ]
    risks = review.get("risks", [])
    if isinstance(risks, list):
        cleaned = [str(item).strip() for item in risks if str(item).strip()]
        if cleaned:
            return cleaned[:2]
    return ["No clear repository change was proposed from the current evidence set."]


def _fix_proposed_change_lines(*, review: dict[str, Any], audit_summary: dict[str, Any], status_label: str) -> list[str]:
    if status_label == "BLOCKED_BY_SAFETY":
        return [
            "Patch/autofix is disabled. Review the proposal manually and apply any change outside RepoBrain.",
        ]
    notes = review.get("notes", [])
    if isinstance(notes, list):
        cleaned = [str(item).strip() for item in notes if str(item).strip()]
        if cleaned:
            return cleaned[:2]
    summary_text = str(review.get("summary_text", "") or "").strip()
    if summary_text:
        return [summary_text]
    return ["No concrete proposal text was produced from the available PR evidence."]


def _fix_affected_files_lines(review: dict[str, Any]) -> list[str]:
    files_changed = review.get("files_changed", [])
    if not isinstance(files_changed, list):
        return ["- None identified."]
    paths = [str(item.get("path", "")).strip() for item in files_changed if isinstance(item, dict)]
    paths = [path for path in paths if path]
    if not paths:
        return ["- None identified."]
    lines = [f"- `{path}`" for path in paths[:5]]
    if len(paths) > 5:
        lines.append(f"- +{len(paths) - 5} more")
    return lines


def _fix_validation_suggestion_lines(review: dict[str, Any]) -> list[str]:
    suggestions = review.get("suggested_tests", review.get("next_steps", []))
    if not isinstance(suggestions, list):
        return ["- Review the proposal manually before making any change."]
    cleaned = [str(item).strip() for item in suggestions if str(item).strip()]
    if not cleaned:
        return ["- Review the proposal manually before making any change."]
    return [f"- {item}" for item in cleaned[:4]]


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
    patch_generation_result = str(audit_summary.get("patch_generation_result", "n/a") or "n/a")
    patch_validation_reason = str(audit_summary.get("patch_validation_reason", "n/a") or "n/a")
    patch_target_files = _int(
        audit_summary.get(
            "patch_target_files_selected",
            audit_summary.get("patch_target_files_count", 0),
        )
    )
    patch_target_files_total = _int(audit_summary.get("patch_target_files_total", 0))
    patch_targeting_mode = str(audit_summary.get("patch_targeting_mode", "n/a") or "n/a")
    patch_targeting_reason = str(audit_summary.get("patch_targeting_reason", "n/a") or "n/a")
    localized_patch_evidence = _int(audit_summary.get("localized_patch_evidence_count", 0))
    patch_grounding_mode = str(audit_summary.get("patch_grounding_mode", "n/a") or "n/a")
    no_patch_result = patch_generation_result == "no_patch"
    if no_patch_result:
        summary_text = (
            "No patch generated: no sufficiently localized, evidence-backed patch target was found."
        )
    elif not summary_text:
        summary_text = "Patch proposal generated from localized PR context."
    patch_validation_result = str(audit_summary.get("patch_validation_result", "n/a") or "n/a")
    segment_summary = _compact_segment_summary(audit_summary)
    verification_status = str(
        verification_report.get("summary", verification_report.get("overall", _verification_status(audit_summary)))
        or _verification_status(audit_summary)
    ).strip()
    fix_status = _fix_status_label(review=review, audit_summary=audit_summary)
    fix_scope = "pull_request" if _has_pr_backend_evidence_context(audit_summary) else "repository"
    fix_confidence = _fix_confidence_label(review=review, audit_summary=audit_summary)
    risk_level = str(review.get("risk_level", "low") or "low").strip().lower() or "low"
    candidate_issue_lines = _fix_candidate_issue_lines(review=review, status_label=fix_status)
    proposed_change_lines = _fix_proposed_change_lines(
        review=review,
        audit_summary=audit_summary,
        status_label=fix_status,
    )
    validation_suggestion_lines = _fix_validation_suggestion_lines(review)
    safety_gate_lines = [
        f"- Patch authorized: `{_bool_label(audit_summary.get('patch_authorized', False))}`",
        f"- Patch applied: `{_bool_label(audit_summary.get('patch_applied', False))}`",
        f"- Files modified: `{_bool_label(audit_summary.get('files_modified', False))}`",
        f"- Branch created: `{_bool_label(audit_summary.get('branch_created', False))}`",
        f"- Commit created: `{_bool_label(audit_summary.get('commit_created', False))}`",
        f"- PR created: `{_bool_label(audit_summary.get('pr_created', False))}`",
    ]
    sections = [
        "### 🛠️ Fix proposal / governance",
        f"- Status: `{fix_status}`",
        f"- Scope: `{fix_scope}`",
        f"- Risk: `{risk_level}`",
        f"- Confidence: `{fix_confidence}`",
        "",
        "Candidate issue / risk:",
        *(f"- {item}" for item in candidate_issue_lines),
        "",
        "Proposed change:",
        *(f"- {item}" for item in proposed_change_lines),
        "",
        "Affected files:",
        *_fix_affected_files_lines(review),
        "",
        "Validation suggestions:",
        *validation_suggestion_lines,
        "",
        "Safety gates:",
        *safety_gate_lines,
        "",
        "### 🛠️ Patch operation",
        f"Summary: {summary_text}",
        "",
        "### 🧾 Patch result",
        f"- Result: `{patch_generation_result}`",
        (
            "- Outcome: safe no_patch (no grounded localized target)."
            if no_patch_result
            else "- Outcome: patch candidate generated."
        ),
        f"- Targeting reason: {patch_targeting_reason}",
        f"- Localized evidence: `{localized_patch_evidence}`",
        f"- Validation result: `{patch_validation_result}`",
        f"- Segment summary: `{segment_summary}`",
        f"- Verification: `{verification_status}`",
    ]
    sections.append("")

    detail_lines = [
        *_retrieval_snapshot_lines(audit_summary),
        *_runtime_provenance_lines(audit_summary, command="fix"),
        *_ultra_large_pr_mode_lines(audit_summary, command="fix"),
        *_render_async_batch_lines(audit_summary, command="fix"),
        "### 🧩 Decision cards",
        "",
        "### 🎯 Patch targeting",
        f"- Patch target files total: {patch_target_files_total}",
        f"- Patch target files selected: {patch_target_files}",
        f"- Patch targeting mode: `{patch_targeting_mode}`",
        f"- Patch targeting reason: {patch_targeting_reason}",
        f"- Localized patch evidence: {localized_patch_evidence}",
        f"- Patch grounding mode: {patch_grounding_mode}",
        "",
        *_evidence_context_summary_lines(audit_summary),
        "### 📌 Patch governance",
        *_patch_governance_lines(
            review=review,
            verification_report=verification_report,
            audit_summary=audit_summary,
        ),
        "",
        "### ✅ Patch validation",
        f"- Patch generation result: `{patch_generation_result}`",
        f"- Patch validation result: `{patch_validation_result}`",
        f"- Patch validation reason: {patch_validation_reason}",
        "",
        "### 📦 Patch artifact",
        "- Full patch is saved to `artifacts/patch.diff`."
        if patch_written
        else "- No patch generated (safe outcome).",
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
        *_render_diagnostic_table(audit_summary, suppress_async_planner_rows=True),
        "",
        "### 🧾 Audit anchors",
        *_version_backend_lines(audit_summary),
        "",
        _audit_note(),
    ]
    sections.extend(_render_runtime_details_block(title="Evidence and diagnostics", lines=detail_lines))
    return "\n".join(sections)


def _audit_category_table_lines(categories: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Category | Score | Label | Rationale | Evidence |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in categories:
        title = str(item.get("title", "Category") or "Category").strip()
        score = _int(item.get("score", 0))
        max_score = _int(item.get("max_score", 0))
        label = str(item.get("label", "UNKNOWN") or "UNKNOWN").strip().upper()
        rationale = str(item.get("rationale", "No rationale captured.") or "No rationale captured.").strip()
        evidence_paths_raw = item.get("evidence_paths", [])
        evidence_paths = (
            [str(path).strip() for path in evidence_paths_raw if str(path).strip()]
            if isinstance(evidence_paths_raw, list)
            else []
        )
        evidence_text = _compact_anchor_list(evidence_paths) if evidence_paths else "none"
        lines.append(
            f"| {title} | {score}/{max_score} | `{label}` | {rationale} | {evidence_text} |"
        )
    return lines


def _audit_category_mini_table_lines(categories: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Category | Score | Label |",
        "| --- | ---: | --- |",
    ]
    for item in categories:
        title = str(item.get("title", "Category") or "Category").strip()
        score = _int(item.get("score", 0))
        max_score = _int(item.get("max_score", 0))
        label = str(item.get("label", "UNKNOWN") or "UNKNOWN").strip().upper()
        lines.append(f"| {title} | {score}/{max_score} | `{label}` |")
    return lines


def _audit_blocker_lines(blockers: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    if not blockers:
        return ["- No critical blockers observed from the available evidence."]
    lines: list[str] = []
    for item in blockers[:limit]:
        title = str(item.get("title", "Critical blocker") or "Critical blocker").strip()
        category = str(item.get("category", "n/a") or "n/a").strip()
        rationale = str(item.get("rationale", "") or "").strip()
        evidence_paths_raw = item.get("evidence_paths", [])
        evidence_paths = (
            [str(path).strip() for path in evidence_paths_raw if str(path).strip()]
            if isinstance(evidence_paths_raw, list)
            else []
        )
        evidence_suffix = f" Evidence: {_compact_anchor_list(evidence_paths)}." if evidence_paths else ""
        lines.append(f"- **{title}** (`{category}`): {rationale}{evidence_suffix}")
    return lines


def _audit_improvement_lines(improvements: list[dict[str, Any]], *, limit: int = 8) -> list[str]:
    if not improvements:
        return ["- No improvement plan was generated from the current evidence sample."]
    lines: list[str] = []
    for item in improvements[:limit]:
        category = str(item.get("category", "Repository health") or "Repository health").strip()
        title = str(item.get("title", "Improve repository quality") or "Improve repository quality").strip()
        rationale = str(item.get("rationale", "") or "").strip()
        impact = str(item.get("expected_score_impact", "medium") or "medium").strip().lower()
        affected_raw = item.get("affected_files", [])
        affected = (
            [str(path).strip() for path in affected_raw if str(path).strip()]
            if isinstance(affected_raw, list)
            else []
        )
        lines.append(
            f"- **{category}** (`{impact}` impact): {title} "
            f"Affected: {_compact_anchor_list(affected)}. Rationale: {rationale}"
        )
    return lines


def _audit_roadmap_lines(roadmap: dict[str, Any]) -> list[str]:
    def _phase_lines(key: str, title: str) -> list[str]:
        raw_items = roadmap.get(key, [])
        items = [str(item).strip() for item in raw_items if str(item).strip()] if isinstance(raw_items, list) else []
        if not items:
            items = ["No specific roadmap item emitted for this phase."]
        return [f"**{title}**", *(f"- {item}" for item in items)]

    lines = _phase_lines("30_days", "30 days")
    lines.append("")
    lines.extend(_phase_lines("60_days", "60 days"))
    lines.append("")
    lines.extend(_phase_lines("90_days", "90 days"))
    return lines


def _audit_evidence_summary_lines(evidence_summary: dict[str, Any], pr_context: dict[str, Any]) -> list[str]:
    key_files_raw = evidence_summary.get("key_files", [])
    key_files = (
        [str(path).strip() for path in key_files_raw if str(path).strip()]
        if isinstance(key_files_raw, list)
        else []
    )
    workflows_raw = evidence_summary.get("workflows_considered", [])
    workflows = (
        [str(path).strip() for path in workflows_raw if str(path).strip()]
        if isinstance(workflows_raw, list)
        else []
    )
    docs_raw = evidence_summary.get("docs_considered", [])
    docs = [str(path).strip() for path in docs_raw if str(path).strip()] if isinstance(docs_raw, list) else []
    tests_raw = evidence_summary.get("tests_considered", [])
    tests = [str(path).strip() for path in tests_raw if str(path).strip()] if isinstance(tests_raw, list) else []
    manifests_raw = evidence_summary.get("manifests_considered", [])
    manifests = (
        [str(path).strip() for path in manifests_raw if str(path).strip()]
        if isinstance(manifests_raw, list)
        else []
    )
    lines = [
        f"- Evidence count: `{_int(evidence_summary.get('evidence_count', len(key_files)))}`",
        f"- Key files: {_compact_anchor_list(key_files, max_items=4)}",
        f"- Workflows considered: {_compact_anchor_list(workflows, max_items=3)}",
        f"- Docs considered: {_compact_anchor_list(docs, max_items=3)}",
        f"- Tests considered: {_compact_anchor_list(tests, max_items=3)}",
        f"- Manifests considered: {_compact_anchor_list(manifests, max_items=3)}",
        f"- Inventory sampled: `{_bool_label(evidence_summary.get('sampled_inventory', False))}`",
    ]
    if bool(pr_context.get("is_pr", False)):
        changed_files_raw = pr_context.get("changed_files_sample", [])
        changed_files = (
            [str(path).strip() for path in changed_files_raw if str(path).strip()]
            if isinstance(changed_files_raw, list)
            else []
        )
        lines.append(f"- PR context: `yes` (PR #{pr_context.get('pr_number', 'n/a')})")
        lines.append(f"- Changed files considered: `{_int(pr_context.get('changed_files_count', 0))}`")
        lines.append(f"- Changed file sample: {_compact_anchor_list(changed_files, max_items=3)}")
    else:
        lines.append("- PR context: `no`")
    return lines


def _audit_confidence_and_limitations_lines(report: dict[str, Any]) -> list[str]:
    limitations_raw = report.get("limitations", [])
    limitations = (
        [str(item).strip() for item in limitations_raw if str(item).strip()]
        if isinstance(limitations_raw, list)
        else []
    )
    lines = [f"- Confidence: `{str(report.get('confidence', 'medium') or 'medium').strip().lower()}`"]
    if limitations:
        lines.extend(f"- {item}" for item in limitations[:6])
    else:
        lines.append("- No additional limitations were recorded.")
    return lines


def _audit_mode_lines(report: dict[str, Any], audit_summary: dict[str, Any]) -> list[str]:
    audit_mode = str(audit_summary.get("audit_mode", "static_mvp") or "static_mvp").strip().lower()
    fallback_reason = str(audit_summary.get("fallback_reason", "audit_static_scoring") or "audit_static_scoring").strip()
    capability = str(audit_summary.get("audit_contract_capability", "") or "").strip()
    warning = str(audit_summary.get("audit_contract_warning", "") or "").strip()
    lines: list[str] = []
    if audit_mode == "v6_enriched":
        lines.append("- Audit mode: `v6-enriched scoring`")
        static_baseline = report.get("static_baseline", {})
        if isinstance(static_baseline, dict):
            baseline_score = _int(static_baseline.get("overall_score", 0))
            baseline_band = str(static_baseline.get("readiness_band", "WEAK") or "WEAK").strip().upper()
            lines.append(f"- Static baseline: `{baseline_score} / 100` (`{baseline_band}`)")
        adjustments_raw = report.get("v6_score_adjustments", [])
        if isinstance(adjustments_raw, list) and adjustments_raw:
            lines.append(f"- v6 bounded adjustments: `{len(adjustments_raw)}`")
    elif audit_mode == "static_contract_ready":
        lines.append("- Audit mode: `static scoring with v6 contract-ready guard`")
        lines.append("- TopoCore v6 deep scoring capability was not available in this runtime.")
    elif audit_mode == "static_contract_rejected":
        lines.append("- Audit mode: `static scoring with rejected v6 response`")
        if warning:
            lines.append(f"- Contract guard: `{warning}`")
    else:
        lines.append("- Audit mode: `static scoring MVP`")
    if capability:
        lines.append(f"- Audit contract capability: `{capability}`")
    lines.append(f"- Audit fallback reason: `{fallback_reason}`")
    return lines


def _audit_delta(report: dict[str, Any]) -> int:
    static_baseline = report.get("static_baseline", {})
    if not isinstance(static_baseline, dict):
        return 0
    return _int(report.get("overall_score", 0)) - _int(static_baseline.get("overall_score", 0))


def _audit_scorecard_lines(report: dict[str, Any], audit_summary: dict[str, Any]) -> list[str]:
    overall_score = _int(report.get("overall_score", 0))
    readiness_band = str(report.get("readiness_band", "WEAK") or "WEAK").strip().upper()
    confidence = str(report.get("confidence", "medium") or "medium").strip().lower()
    requested_backend = str(audit_summary.get("requested_backend", "auto") or "auto").strip()
    resolved_backend = str(audit_summary.get("resolved_backend", "not_applicable") or "not_applicable").strip()
    audit_mode = str(audit_summary.get("audit_mode", "static_mvp") or "static_mvp").strip().lower()
    contract_status = str(audit_summary.get("audit_contract_status", "not_requested") or "not_requested").strip()
    lines = [
        f"- Final score: **{overall_score} / 100** (`{readiness_band}`)",
        f"- Confidence: `{confidence}`",
        f"- Backend: `{requested_backend}` -> `{resolved_backend}`",
    ]
    static_baseline = report.get("static_baseline", {})
    if isinstance(static_baseline, dict) and static_baseline:
        baseline_score = _int(static_baseline.get("overall_score", 0))
        baseline_band = str(static_baseline.get("readiness_band", "WEAK") or "WEAK").strip().upper()
        delta = _audit_delta(report)
        delta_text = f"+{delta}" if delta > 0 else str(delta)
        lines.insert(1, f"- Static baseline: `{baseline_score} / 100` (`{baseline_band}`)")
        lines.insert(2, f"- v6 enriched score: `{overall_score} / 100` (`{readiness_band}`)")
        lines.insert(3, f"- Delta: `{delta_text}`")
    if audit_mode == "v6_enriched":
        lines.insert(0, "- Audit mode: `v6-enriched scoring`")
        lines.append(f"- Contract: `{AUDIT_V6_CONTRACT_VERSION}` accepted (`{contract_status}`)")
    elif audit_mode == "static_contract_ready":
        lines.insert(0, "- Audit mode: `static scoring with v6 contract-ready guard`")
        lines.append("- Contract: `topocore.audit_score.v1` ready, capability unavailable in this runtime.")
    elif audit_mode == "static_contract_rejected":
        lines.insert(0, "- Audit mode: `static scoring with rejected v6 response`")
        lines.append("- Contract: `topocore.audit_score.v1` rejected; static baseline retained.")
    else:
        lines.insert(0, "- Audit mode: `static scoring MVP`")
    return lines


def _audit_adjustment_lines(report: dict[str, Any]) -> list[str]:
    adjustments_raw = report.get("v6_score_adjustments", [])
    adjustments = [item for item in adjustments_raw if isinstance(item, dict)] if isinstance(adjustments_raw, list) else []
    if not adjustments:
        return ["- v6 enrichment accepted; no score delta was required from available evidence."]
    lines: list[str] = []
    for item in adjustments[:6]:
        category = str(item.get("category", "category") or "category").strip()
        delta = _int(item.get("delta", 0))
        reason = str(item.get("reason", "No reason recorded.") or "No reason recorded.").strip()
        evidence_paths_raw = item.get("evidence_paths", [])
        evidence_paths = (
            [str(path).strip() for path in evidence_paths_raw if str(path).strip()]
            if isinstance(evidence_paths_raw, list)
            else []
        )
        delta_text = f"+{delta}" if delta > 0 else str(delta)
        evidence_suffix = f" Evidence: {_compact_anchor_list(evidence_paths)}." if evidence_paths else ""
        lines.append(f"- **{category}** (`{delta_text}`): {reason}{evidence_suffix}")
    return lines


def _audit_safety_statement_lines(audit_summary: dict[str, Any]) -> list[str]:
    return [
        "- Audit is informational only.",
        f"- Files modified: `{_bool_label(audit_summary.get('files_modified', False))}`",
        f"- Patch applied: `{_bool_label(audit_summary.get('patch_applied', False))}`",
        f"- Branch created: `{_bool_label(audit_summary.get('branch_created', False))}`",
        f"- Commit created: `{_bool_label(audit_summary.get('commit_created', False))}`",
        f"- PR created: `{_bool_label(audit_summary.get('pr_created', False))}`",
        "- Not a security approval.",
        "- Not a merge approval.",
    ]


def _audit_anchor_lines(audit_summary: dict[str, Any]) -> list[str]:
    route = str(audit_summary.get("route_final", "AUDIT") or "AUDIT").strip().upper()
    version = str(audit_summary.get("repobrain_version", "") or "").strip()
    backend_mode = str(audit_summary.get("backend_mode", "n/a") or "n/a").strip()
    scope_status = str(audit_summary.get("scope_status", "n/a") or "n/a").strip()
    lines = [f"- Route: `{route}`"]
    if version:
        lines.append(f"- RepoBrain version: `{version}`")
    lines.append(f"- Backend mode: `{backend_mode}`")
    lines.append(f"- Scope status: `{scope_status}`")
    return lines


def render_audit_markdown(
    *,
    report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    overall_score = _int(report.get("overall_score", 0))
    readiness_band = str(report.get("readiness_band", "WEAK") or "WEAK").strip().upper()
    executive_summary = str(report.get("executive_summary", "No executive summary generated.") or "").strip()
    categories_raw = report.get("categories", [])
    categories = [item for item in categories_raw if isinstance(item, dict)] if isinstance(categories_raw, list) else []
    blockers_raw = report.get("critical_blockers", [])
    blockers = [item for item in blockers_raw if isinstance(item, dict)] if isinstance(blockers_raw, list) else []
    improvements_raw = report.get("top_improvements", [])
    improvements = [item for item in improvements_raw if isinstance(item, dict)] if isinstance(improvements_raw, list) else []
    roadmap = report.get("roadmap", {}) if isinstance(report.get("roadmap", {}), dict) else {}
    evidence_summary = (
        report.get("evidence_summary", {}) if isinstance(report.get("evidence_summary", {}), dict) else {}
    )
    pr_context = report.get("pr_context", {}) if isinstance(report.get("pr_context", {}), dict) else {}
    query = str(report.get("query", "") or "").strip()
    sections = [
        "# RepoBrain Repository Audit",
        "",
        "## Executive score card",
        *_audit_scorecard_lines(report, audit_summary),
    ]
    if query:
        sections.extend(["", f"Requested focus: {query}"])
    sections.extend(
        [
            "",
            "## Executive summary",
            executive_summary or "No executive summary generated.",
            "",
            f"Overall score: **{overall_score} / 100**",
            f"Readiness band: **{readiness_band}**",
            "",
            "## Audit mode",
            *_audit_mode_lines(report, audit_summary),
            "",
            "## Category scores",
            *_audit_category_table_lines(categories),
            "",
            "## v6 adjustments",
            *_audit_adjustment_lines(report),
            "",
            "## Critical blockers",
            *_audit_blocker_lines(blockers),
            "",
            "## Top improvements",
            *_audit_improvement_lines(improvements),
            "",
            "## 30/60/90-day roadmap",
            *_audit_roadmap_lines(roadmap),
            "",
            "## Evidence summary",
            *_audit_evidence_summary_lines(evidence_summary, pr_context),
            "",
            "## Confidence and limitations",
            *_audit_confidence_and_limitations_lines(report),
            "",
            "## Runtime and safety",
            *_runtime_backend_evidence_lines(audit_summary),
            "- No `v5`: `yes`",
            "- No legacy community dependency: `yes`",
            "- No patch/autofix: `yes`",
            "",
            "## Safety statement",
            *_audit_safety_statement_lines(audit_summary),
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )
    return "\n".join(sections)


def render_score_markdown(
    *,
    report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    categories_raw = report.get("categories", [])
    categories = [item for item in categories_raw if isinstance(item, dict)] if isinstance(categories_raw, list) else []
    blockers_raw = report.get("critical_blockers", [])
    blockers = [item for item in blockers_raw if isinstance(item, dict)] if isinstance(blockers_raw, list) else []
    improvements_raw = report.get("top_improvements", [])
    improvements = [item for item in improvements_raw if isinstance(item, dict)] if isinstance(improvements_raw, list) else []
    query = str(report.get("query", "") or "").strip()

    sections = [
        "# RepoBrain Repository Score",
        "",
        "## Score card",
        *_audit_scorecard_lines(report, audit_summary),
    ]
    if query:
        sections.extend(["", f"Requested focus: {query}"])
    sections.extend(
        [
            "",
            "## Category snapshot",
            *_audit_category_mini_table_lines(categories),
            "",
            "## Top blockers",
            *_audit_blocker_lines(blockers, limit=3),
            "",
            "## Top improvements",
            *_audit_improvement_lines(improvements, limit=3),
            "",
            "## Runtime and safety",
            f"- Backend resolved: `{str(audit_summary.get('resolved_backend', 'not_applicable') or 'not_applicable').strip()}`",
            f"- Backend mode: `{str(audit_summary.get('backend_mode', 'n/a') or 'n/a').strip()}`",
            f"- Fallback: `{str(audit_summary.get('fallback_used', 'not_applicable') or 'not_applicable').strip()}` / `{str(audit_summary.get('fallback_reason', 'n/a') or 'n/a').strip()}`",
            "- No patch/mutation: `yes`",
            "- Informational only: `yes`",
            "",
            "Use `/repobrain audit` for the full evidence report.",
            "",
            _audit_note(),
        ]
    )
    return "\n".join(sections)


def _supported_command_lines(report: dict[str, Any]) -> list[str]:
    supported_raw = report.get("supported_commands", [])
    supported = (
        [str(item).strip() for item in supported_raw if str(item).strip()]
        if isinstance(supported_raw, list)
        else []
    )
    roadmap_raw = report.get("roadmap_commands", [])
    roadmap = (
        [str(item).strip() for item in roadmap_raw if str(item).strip()]
        if isinstance(roadmap_raw, list)
        else []
    )
    lines = [
        f"- Supported: {', '.join(f'`{item}`' for item in supported) if supported else '`n/a`'}",
        f"- Roadmap-only: {', '.join(f'`{item}`' for item in roadmap) if roadmap else '`none`'}",
    ]
    return lines


def _policy_lines(items: list[str], *, fallback: str) -> list[str]:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return [f"- {fallback}"]
    return [f"- {item}" for item in cleaned]


def _doctor_check_table_lines(checks: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in checks:
        name = str(item.get("name", "Unnamed check") or "Unnamed check").strip()
        status = str(item.get("status", "UNKNOWN") or "UNKNOWN").strip().upper()
        detail = str(item.get("detail", "No detail recorded.") or "No detail recorded.").strip()
        lines.append(f"| {name} | `{status}` | {detail} |")
    return lines


def render_status_markdown(
    *,
    report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    query = str(report.get("query", "") or "").strip()
    topocore_policy = report.get("topocore_policy", [])
    safety_policy = report.get("safety_policy", [])
    install_hints = report.get("install_hints", [])
    workflow = report.get("workflow", {}) if isinstance(report.get("workflow", {}), dict) else {}
    sections = [
        "# RepoBrain Status",
        "",
        f"- RepoBrain version: `{str(report.get('version', 'n/a') or 'n/a').strip()}`",
        f"- Runtime mode: `{str(report.get('action_runtime_mode', 'n/a') or 'n/a').strip()}`",
        f"- Repository: `{str(report.get('repo_name', 'unknown') or 'unknown').strip()}`",
        f"- Event context: `{str(report.get('event_context', 'unknown') or 'unknown').strip()}`",
    ]
    if query:
        sections.extend(["", f"Requested focus: {query}"])
    sections.extend(
        [
            "",
            "## Command surface",
            *_supported_command_lines(report),
            "",
            "## Backend policy",
            *_policy_lines(topocore_policy if isinstance(topocore_policy, list) else [], fallback="No backend policy notes recorded."),
            f"- TopoCore dependency mode: `{str(report.get('topocore_dependency_mode', 'not_detected') or 'not_detected').strip()}`",
            f"- TopoCore runtime mode requested: `{str(report.get('topocore_runtime_mode_requested', 'auto') or 'auto').strip()}`",
            f"- TopoCore runtime mode effective: `{str(report.get('topocore_runtime_mode_effective', 'auto') or 'auto').strip()}`",
            "",
            "## Workflow snapshot",
            f"- RepoBrain workflow detected: `{_bool_label(bool(workflow.get('exists', False)))}`",
            f"- Explicit permissions block: `{_bool_label(bool(workflow.get('permissions_explicit', False)))}`",
            f"- Read-mostly baseline detected: `{_bool_label(bool(workflow.get('read_mostly_baseline', False)))}`",
            "",
            "## Safety policy",
            *_policy_lines(safety_policy if isinstance(safety_policy, list) else [], fallback="No safety policy notes recorded."),
            "",
            "## Install hints",
            *_policy_lines(install_hints if isinstance(install_hints, list) else [], fallback="No install hints recorded."),
            "",
            "## Runtime and safety",
            *_runtime_backend_evidence_lines(audit_summary),
            "- No `v5`: `yes`",
            "- No legacy community dependency: `yes`",
            "- No patch/autofix: `yes`",
            "",
            "## Safety statement",
            "- Status is informational only.",
            "- No files modified.",
            "- No patch applied.",
            "- No branch, commit, or PR created by RepoBrain.",
            "- Not a security approval.",
            "- Not a merge approval.",
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )
    return "\n".join(sections)


def render_doctor_markdown(
    *,
    report: dict[str, Any],
    audit_summary: dict[str, Any],
) -> str:
    query = str(report.get("query", "") or "").strip()
    checks_raw = report.get("checks", [])
    checks = [item for item in checks_raw if isinstance(item, dict)] if isinstance(checks_raw, list) else []
    issues_raw = report.get("issues_found", [])
    issues_found = [str(item).strip() for item in issues_raw if str(item).strip()] if isinstance(issues_raw, list) else []
    fixes_raw = report.get("recommended_fixes", [])
    fixes = [str(item).strip() for item in fixes_raw if str(item).strip()] if isinstance(fixes_raw, list) else []
    limitations_raw = report.get("limitations", [])
    limitations = (
        [str(item).strip() for item in limitations_raw if str(item).strip()]
        if isinstance(limitations_raw, list)
        else []
    )
    issue_lines = [f"- {item}" for item in issues_found] or [
        "- No blocking issue was confirmed from the current safe diagnostics."
    ]
    fix_lines = [f"- {item}" for item in fixes] or ["- No immediate fix recommendation was generated."]
    limitation_lines = [f"- {item}" for item in limitations] or ["- No additional limitation was recorded."]
    sections = [
        "# RepoBrain Doctor",
        "",
        f"Overall diagnostic status: **{str(report.get('overall_status', 'UNKNOWN') or 'UNKNOWN').strip().upper()}**",
        f"- Repository: `{str(report.get('repo_name', 'unknown') or 'unknown').strip()}`",
        f"- Event context: `{str(report.get('event_context', 'unknown') or 'unknown').strip()}`",
    ]
    if query:
        sections.extend(["", f"Requested focus: {query}"])
    sections.extend(
        [
            "",
            "## Runtime mode",
            f"- TopoCore runtime mode requested: `{str(report.get('topocore_runtime_mode_requested', 'auto') or 'auto').strip()}`",
            f"- TopoCore runtime mode effective: `{str(report.get('topocore_runtime_mode_effective', 'auto') or 'auto').strip()}`",
            f"- TopoCore dependency mode: `{str(report.get('topocore_dependency_mode', 'not_detected') or 'not_detected').strip()}`",
            "",
            "## Diagnostic checks",
            *_doctor_check_table_lines(checks),
            "",
            "## Issues found",
            *issue_lines,
            "",
            "## Recommended fixes",
            *fix_lines,
            "",
            "## Limitations",
            *limitation_lines,
            "",
            "## Runtime and safety",
            *_runtime_backend_evidence_lines(audit_summary),
            "- No `v5`: `yes`",
            "- No legacy community dependency: `yes`",
            "- No patch/autofix: `yes`",
            "",
            "## Safety statement",
            "- Doctor is informational only.",
            "- No files modified.",
            "- No patch applied.",
            "- No branch, commit, or PR created by RepoBrain.",
            "- Not a security approval.",
            "- Not a merge approval.",
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )
    return "\n".join(sections)


def render_unsupported_command_markdown(
    *,
    command: str,
    message: str,
    next_steps: list[str],
    audit_summary: dict[str, Any],
) -> str:
    steps = [str(item).strip() for item in next_steps if str(item).strip()]
    step_lines = [f"- {item}" for item in steps] or ["- Use `/repobrain help` to review supported commands."]
    return "\n".join(
        [
            "# RepoBrain command status",
            "",
            message.strip() or "Unsupported RepoBrain command. Use /repobrain help to see supported commands.",
            "",
            "## Next steps",
            *step_lines,
            "",
            "## Runtime and safety",
            *_runtime_backend_evidence_lines(audit_summary),
            "- No `v5`: `yes`",
            "- No legacy community dependency: `yes`",
            "- No patch/autofix: `yes`",
            "",
            "### 🧾 Audit anchors",
            *_audit_anchor_lines(audit_summary),
            "",
            _audit_note(),
        ]
    )
