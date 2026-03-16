from __future__ import annotations

import re
from typing import Any


def check_name_for_command(cmd: str) -> str:
    normalized = str(cmd or "").strip().lower()
    if normalized in {"ask", "locate", "explain"}:
        return "RepoBrain Ask"
    if normalized == "fix":
        return "RepoBrain Fix"
    return "RepoBrain Review"


def _compact_text(text: str, *, max_len: int = 220) -> str:
    compact = " ".join(str(text or "").strip().split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 3].rstrip()}..."


def _verification_status(audit: dict[str, Any]) -> str:
    report_raw = audit.get("verification_report", {})
    report = dict(report_raw) if isinstance(report_raw, dict) else {}
    overall = str(
        report.get("overall", report.get("summary", audit.get("verification_overall", "NOT_RUN")))
        or "NOT_RUN"
    ).strip()
    normalized = overall.upper()
    if normalized in {"PASS", "FAIL", "WARN", "NOT_RUN"}:
        return normalized
    return "NOT_RUN"


def _comment_reference(audit: dict[str, Any]) -> str:
    pr_number = audit.get("pr_number")
    if isinstance(pr_number, int) and pr_number > 0:
        return f"PR #{pr_number}"
    issue_number = audit.get("issue_number")
    if isinstance(issue_number, int) and issue_number > 0:
        return f"Issue/PR #{issue_number}"
    return "n/a"


def _status_word(conclusion: str) -> str:
    normalized = str(conclusion or "neutral").strip().lower()
    if normalized == "success":
        return "completed"
    if normalized == "failure":
        return "failed"
    return "neutral"


def map_check_conclusion(
    *,
    cmd: str,
    audit: dict[str, Any],
    base_conclusion: str,
) -> str:
    normalized_cmd = str(cmd or "").strip().lower()
    normalized_base = str(base_conclusion or "neutral").strip().lower()
    if normalized_base not in {"success", "neutral", "failure"}:
        normalized_base = "neutral"

    route = str(audit.get("route_final", "FAST") or "FAST").strip().upper()
    if route == "ERROR":
        return "failure"

    skip_reason_code = str(audit.get("skip_reason_code", "n/a") or "n/a").strip().lower()
    if skip_reason_code not in {"", "n/a"}:
        return "neutral"

    if normalized_cmd == "fix":
        patch_result = str(
            audit.get("patch_generation_result", audit.get("patch_validation_result", "n/a"))
            or "n/a"
        ).strip().lower()
        if patch_result == "valid_patch":
            return "success"
        if patch_result == "no_patch":
            return "neutral"
        if patch_result in {"patch_validation_failed", "provider_failed"}:
            return "failure"

    if normalized_cmd in {"review", "fix"} and route in {"WAIT", "REFUSE", "BLOCK"}:
        return "neutral"

    if normalized_cmd in {"ask", "locate", "explain"} and route in {"WAIT", "REFUSE", "BLOCK"}:
        return "neutral"

    return normalized_base


def build_check_summary_markdown(
    *,
    cmd: str,
    audit: dict[str, Any],
    conclusion: str,
) -> tuple[str, str]:
    normalized_cmd = str(cmd or "").strip().lower()
    route = str(audit.get("route_final", "FAST") or "FAST").strip().upper()
    verification = _verification_status(audit)
    reference = _comment_reference(audit)
    status_word = _status_word(conclusion)
    skip_reason = str(audit.get("skip_reason_short", "n/a") or "n/a").strip()

    header = f"Status: **{status_word}**"
    if skip_reason and skip_reason.lower() != "n/a":
        header = "Status: **neutral (safe skip)**"

    if normalized_cmd in {"ask", "locate", "explain"}:
        answer_summary = _compact_text(
            str(audit.get("check_answer_summary", audit.get("answer_summary", "Answer generated.")) or "Answer generated.")
        )
        grounding = str(audit.get("answer_grounding_mode", "retrieval") or "retrieval")
        llm_used = bool(audit.get("llm_used", False))
        final_model = str(audit.get("llm_final_synthesis_model_id", "n/a") or "n/a")
        lines = [
            "### RepoBrain Ask Check",
            f"- Command: `{normalized_cmd}`",
            f"- {header}",
            f"- Route: `{route}`",
            f"- Grounding: `{grounding}`",
            f"- LLM: {'used' if llm_used else 'not used'} (`{final_model if llm_used else 'n/a'}`)",
            f"- Verification: `{verification}`",
            f"- Summary: {answer_summary}",
        ]
        if reference != "n/a":
            lines.append(f"- Thread: {reference}")
        if skip_reason and skip_reason.lower() != "n/a":
            lines.append(f"- Skip reason: {skip_reason}")
        markdown = "\n".join(lines)
        return markdown, markdown

    if normalized_cmd == "fix":
        patch_result = str(
            audit.get("patch_generation_result", audit.get("patch_validation_result", "n/a"))
            or "n/a"
        )
        selected = int(audit.get("patch_target_files_selected", audit.get("patch_target_files_count", 0)) or 0)
        total = int(audit.get("patch_target_files_total", 0) or 0)
        validation_result = str(audit.get("patch_validation_result", "n/a") or "n/a")
        outcome_line = _compact_text(
            str(
                audit.get(
                    "patch_validation_reason",
                    audit.get("patch_apply_message", "Patch workflow completed."),
                )
                or "Patch workflow completed."
            )
        )
        lines = [
            "### RepoBrain Fix Check",
            "- Command: `fix`",
            f"- {header}",
            f"- Patch result: `{patch_result}`",
            f"- Patch targeting: {selected} selected / {total} considered",
            f"- Patch validation: `{validation_result}`",
            f"- Verification: `{verification}`",
            f"- Outcome: {outcome_line}",
        ]
        if reference != "n/a":
            lines.append(f"- Thread: {reference}")
        if skip_reason and skip_reason.lower() != "n/a":
            lines.append(f"- Skip reason: {skip_reason}")
        markdown = "\n".join(lines)
        return markdown, markdown

    risk_level = str(audit.get("review_risk_level", "LOW") or "LOW").strip().upper()
    confirmed = int(audit.get("review_confirmed_findings_count", 0) or 0)
    possible = int(audit.get("review_possible_signals_count", 0) or 0)
    info_notes = int(audit.get("review_informational_notes_count", 0) or 0)
    drivers = int(audit.get("review_risk_drivers_count", 0) or 0)
    tldr = _compact_text(
        str(audit.get("review_tldr", audit.get("check_review_tldr", "Review completed.")) or "Review completed."),
        max_len=260,
    )
    tldr = re.sub(r"^\s*TL;DR:\s*", "", tldr, flags=re.IGNORECASE).strip() or "Review completed."

    lines = [
        "### RepoBrain Review Check",
        "- Command: `review`",
        f"- {header}",
        f"- Risk level: `{risk_level}`",
        f"- Confirmed findings: `{confirmed}`",
        f"- Possible signals: `{possible}`",
        f"- Informational notes: `{info_notes}`",
        f"- Risk drivers: `{drivers}`",
        f"- Verification: `{verification}`",
        f"- TL;DR: {tldr}",
    ]
    if reference != "n/a":
        lines.append(f"- Thread: {reference}")
    if skip_reason and skip_reason.lower() != "n/a":
        lines.append(f"- Skip reason: {skip_reason}")
    markdown = "\n".join(lines)
    return markdown, markdown
