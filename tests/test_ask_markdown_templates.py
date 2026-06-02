from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import (
    render_answer_markdown,
    render_refuse_markdown,
    render_wait_markdown,
)


def _sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=40,
            score=0.1234,
        )
    ]


def test_render_answer_markdown_fast() -> None:
    text = render_answer_markdown(
        answer_text="Question: test\nRoute: FAST",
        evidence=_sample_evidence(),
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "retrieved": 10,
            "selected": 2,
        },
        next_steps="Open evidence links and verify logic",
        command="ask",
    )
    assert "### ✅ Answer" in text
    assert "### 📍 Evidence used" in text
    assert "- Route: `FAST`" in text


def test_render_answer_markdown_deep_marks_second_pass() -> None:
    text = render_answer_markdown(
        answer_text="Question: test\nRoute: DEEP",
        evidence=_sample_evidence(),
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 40,
            "selected": 4,
            "verification_not_run_count": 1,
        },
        next_steps="Open evidence links and verify logic",
        command="ask",
    )
    assert "- Route: `DEEP`" in text
    assert "### 🤖 LLM" in text


def test_render_wait_markdown() -> None:
    text = render_wait_markdown(
        reason="Verification pending",
        audit_summary={"route_final": "WAIT", "retrieved": 0, "selected": 0},
    )
    assert "### ⏳ Needs verification" in text
    assert "checks were not run" in text


def test_render_refuse_or_block_markdown() -> None:
    refused = render_refuse_markdown(
        reason="Blocked by policy",
        audit_summary={"route_final": "REFUSE", "retrieved": 0, "selected": 0},
        blocked=False,
    )
    blocked = render_refuse_markdown(
        reason="Blocked by policy",
        audit_summary={"route_final": "BLOCK", "retrieved": 0, "selected": 0},
        blocked=True,
    )
    assert "### 🚫 Refused" in refused
    assert "### 🛑 Blocked" in blocked
