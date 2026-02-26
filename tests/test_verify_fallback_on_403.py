from repobrain.verify import build_verify_report


def test_verify_fallback_on_empty_check_runs_uses_combined_status() -> None:
    check_runs = {"total_count": 0, "check_runs": []}
    status_json = {
        "state": "pending",
        "statuses": [
            {
                "context": "ci/tests",
                "state": "pending",
                "target_url": "https://example.test/status/ci-tests",
            }
        ],
    }

    report = build_verify_report(check_runs, status_json)

    assert report["state"] == "pending"
    assert report["total"] == 1
    assert report["pending"] == 1
    assert report["failure"] == 0
