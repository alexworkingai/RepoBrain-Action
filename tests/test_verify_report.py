from repobrain.verify import build_verify_report


def test_verify_report_success_from_check_runs() -> None:
    report = build_verify_report(
        {
            "total_count": 2,
            "check_runs": [
                {"name": "lint", "status": "completed", "conclusion": "success"},
                {"name": "tests", "status": "completed", "conclusion": "success"},
            ],
        },
        None,
    )

    assert report["state"] == "success"
    assert report["total"] == 2
    assert report["failure"] == 0
    assert report["pending"] == 0


def test_verify_report_failure_collects_failures() -> None:
    report = build_verify_report(
        {
            "total_count": 2,
            "check_runs": [
                {"name": "lint", "status": "completed", "conclusion": "success"},
                {
                    "name": "tests",
                    "status": "completed",
                    "conclusion": "failure",
                    "details_url": "https://example.test/checks/1",
                },
            ],
        },
        None,
    )

    assert report["state"] == "failure"
    assert report["failure"] == 1
    assert report["failures"]
    assert report["failures"][0]["name"] == "tests"


def test_verify_report_pending_from_in_progress_check() -> None:
    report = build_verify_report(
        {
            "total_count": 1,
            "check_runs": [
                {"name": "tests", "status": "in_progress", "conclusion": None},
            ],
        },
        None,
    )

    assert report["state"] == "pending"
    assert report["pending"] == 1


def test_verify_report_falls_back_to_combined_status() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": []},
        {
            "state": "failure",
            "statuses": [
                {
                    "context": "ci/build",
                    "state": "failure",
                    "target_url": "https://example.test/status/1",
                }
            ],
        },
    )

    assert report["state"] == "failure"
    assert report["total"] == 1
    assert report["failure"] == 1
    assert report["failures"][0]["name"] == "ci/build"
