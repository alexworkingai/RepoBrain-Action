from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown, render_review_markdown


def test_ask_output_keeps_answer_and_compact_evidence() -> None:
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[EvidenceItem(file_path="repobrain/github_flow.py", line_start=1, line_end=2, score=1.0)],
        audit_summary={"command": "ask", "route_final": "FAST", "selected": 1},
        next_steps="Inspect",
        command="ask",
    )

    assert "Answer text" in md
    assert "### 📍 Evidence used" in md
    assert "`repobrain/github_flow.py`" in md


def test_locate_output_keeps_route_and_direct_retrieval_note() -> None:
    md = render_answer_markdown(
        answer_text="unused",
        evidence=[EvidenceItem(file_path="repobrain/github_flow.py", line_start=1, line_end=2, score=1.0)],
        audit_summary={"command": "locate", "route_final": "REVIEW", "selected": 1},
        next_steps="Inspect",
        command="locate",
    )

    assert "Route: `LOCATE`" in md
    assert "direct retrieval command" in md.lower()


def test_review_output_keeps_changed_files_findings_signals_and_notes() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Summary",
            "risk_level": "medium",
            "files_block": ["- `repobrain/github_flow.py`"],
            "confirmed_findings": ["A confirmed finding"],
            "possible_signals": ["A possible signal"],
            "informational_notes": ["A note"],
            "recommendations": ["Run tests"],
            "risk_drivers": ["Reason"],
        },
        verification_report={"summary": "PASS", "overall": "PASS"},
        audit_summary={"command": "review", "route_final": "REVIEW"},
    )

    assert "Changed files:" in md
    assert "Findings:" in md
    assert "Signals:" in md
    assert "Notes:" in md
