from __future__ import annotations

from .evidence import EvidenceItem


def format_github_comment(
    answer_text: str,
    evidence: list[EvidenceItem],
    audit_summary: dict[str, object],
    next_steps: str,
) -> str:
    """Format a GitHub-style markdown comment for RepoBrain local MVP."""
    evidence_lines = (
        [
            f"- `{item.file_path}:L{item.line_start}-L{item.line_end}` (score={item.score:.2f})"
            for item in evidence
        ]
        if evidence
        else ["- No evidence selected."]
    )

    audit_lines = [f"- `{key}`: {value}" for key, value in audit_summary.items()]
    if not audit_lines:
        audit_lines = ["- No audit data."]

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
        *audit_lines,
    ]
    return "\n".join(sections)
