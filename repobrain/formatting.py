from __future__ import annotations

from .evidence import EvidenceItem


def _format_audit_summary(audit_summary: dict[str, object]) -> list[str]:
    audit_lines = [f"- `{key}`: {value}" for key, value in audit_summary.items()]
    return audit_lines or ["- No audit data."]


def format_github_comment(
    answer_text: str,
    evidence: list[EvidenceItem],
    audit_summary: dict[str, object],
    next_steps: str,
) -> str:
    """Format a GitHub-style markdown comment for ask/locate/explain commands."""
    evidence_lines = (
        [
            f"- `{item.file_path}:L{item.line_start}-L{item.line_end}` (score={item.score:.4f})"
            for item in evidence
        ]
        if evidence
        else ["- No evidence selected."]
    )

    sections = [
        "### ✅ Answer",
        answer_text.strip() or "No answer generated.",
        "",
        "### 📌 Evidence",
        *evidence_lines,
        "",
        "### ✅ Next steps",
        f"- {next_steps.strip() or 'Open evidence links and verify logic'}",
        "",
        "### 🧾 Audit summary",
        *_format_audit_summary(audit_summary),
    ]
    return "\n".join(sections)


def format_pr_review_comment(review: dict[str, object]) -> str:
    """Format a PR review markdown comment from `repobrain.review.build_pr_review` output."""
    summary_text = str(review.get("summary_text", "")).strip() or "No summary available."
    files_block = list(review.get("files_block", []))
    risks = list(review.get("risks", []))
    next_steps = list(review.get("next_steps", []))
    audit_summary = dict(review.get("audit_summary", {}))

    file_lines = files_block or ["- No changed files detected."]
    risk_lines = [f"- {item}" for item in risks] or ["- No obvious risks detected."]
    next_step_lines = [f"- {item}" for item in next_steps] or ["- Run checks and review changes."]

    sections = [
        "### ✅ PR Review",
        "",
        f"TL;DR: {summary_text}",
        "",
        "### 🗂️ Files changed",
        *file_lines,
        "",
        "### ⚠️ Risks",
        *risk_lines,
        "",
        "### ✅ Next steps",
        *next_step_lines,
        "",
        "### 🧾 Audit summary",
        *_format_audit_summary(audit_summary),
    ]
    return "\n".join(sections)
