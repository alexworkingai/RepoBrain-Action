from repobrain.formatting import format_verify_comment
from repobrain.verify import build_verify_report


def test_verify_forbidden_returns_unknown_and_permissions_hint() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": [], "_error": "forbidden"},
        {"state": "unknown", "statuses": [], "_error": "forbidden"},
        {"total_count": 0, "workflow_runs": [], "_error": "forbidden"},
    )

    text = format_verify_comment(report)

    assert report["state"] == "unknown"
    assert "Verification unavailable due to token permissions" in text
    assert "checks: read" in text
    assert "statuses: read" in text
    assert "actions: read" in text
