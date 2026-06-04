from __future__ import annotations

from repobrain.output_md import render_audit_markdown


def test_audit_limit_reporting_shows_exhausted_without_score_drift() -> None:
    markdown = render_audit_markdown(
        report={
            "overall_score": 85,
            "readiness_band": "STRONG",
            "executive_summary": "Strong repository baseline.",
            "categories": [],
            "critical_blockers": [],
            "top_improvements": [],
            "roadmap": {},
            "evidence_summary": {},
            "pr_context": {},
            "confidence": "high",
            "limitations": [],
            "audit_narrative_requested": True,
            "audit_narrative_mode": "narrative",
            "audit_narrative_text": "",
        },
        audit_summary={
            "audit_mode": "v6_enriched",
            "audit_narrative_requested": True,
            "audit_narrative_mode": "narrative",
            "audit_score_modified_by_llm": False,
            "llm_used": False,
            "llm_skip_reason": "budget:llm_remaining_exhausted",
            "llm_runtime_override_reason": "LLM quota/limit exhausted; audit score is available and narrative layer was skipped until limits reset.",
            "execution_mode": "retrieval_plus_llm",
            "resolved_backend": "v6",
            "requested_backend": "auto",
            "audit_contract_status": "accepted",
            "fallback_reason": "n/a",
        },
    )

    assert "- Score authority: `TopoCore contract`" in markdown
    assert "- Score modified by LLM: `no`" in markdown
    assert "quota/limit exhausted" in markdown
    assert "- Limit status: `exhausted`" in markdown
