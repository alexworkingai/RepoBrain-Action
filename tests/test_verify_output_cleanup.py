from repobrain.formatting import format_verify_comment
from repobrain.verify import build_verify_report


def test_verify_output_is_compact_and_has_no_legacy_diagnostics_header() -> None:
    report = build_verify_report(
        {
            "total_count": 1,
            "check_runs": [
                {"name": "tests", "status": "completed", "conclusion": "success"},
            ],
        },
        None,
        head_sha="abc123",
    )
    text = format_verify_comment(
        report,
        audit_summary={
            "route_final": "VERIFY",
            "requested_backend": "not_applicable",
            "resolved_backend": "not_applicable",
            "fallback_used": "not_applicable",
            "fallback_reason": "verify_report_only",
        },
    )

    assert "Runtime and safety" in text
    assert "TopoCore backend diagnostics" not in text
    assert "рџ" not in text
    assert "Route: `VERIFY`" in text
