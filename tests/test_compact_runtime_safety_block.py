from __future__ import annotations

from repobrain.output_md import render_audit_markdown


def test_compact_runtime_and_safety_block_hides_raw_backend_fields() -> None:
    md = render_audit_markdown(
        report={
            "overall_score": 77,
            "readiness_band": "GOOD",
            "executive_summary": "Summary",
            "categories": [],
            "critical_blockers": [],
            "top_improvements": [],
            "roadmap": {},
            "evidence_summary": {},
            "limitations": [],
            "confidence": "medium",
        },
        audit_summary={
            "command": "audit",
            "route_final": "AUDIT",
            "audit_mode": "v6_enriched",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "fallback_used": False,
            "fallback_reason": "none",
            "tky_mode_requested": "local",
            "tky_mode_used": "local",
            "tkya_backend": "v6",
        },
    )

    assert "### 🛡️ Runtime and safety" in md
    assert "- Runtime: `v6-enriched`" in md
    assert "- Backend: `private runtime resolved successfully`" in md
    assert "TKY mode requested" not in md
    assert "TKYA mode" not in md
    assert "Files modified: `no`" not in md
    assert "Patch applied: `no`" not in md
