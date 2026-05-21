from repobrain.formatting import format_verify_comment
from repobrain.github_flow import _build_verify_markdown
from repobrain.verify import build_verify_report


def test_pr_verify_success_maps_to_pass_informational_report() -> None:
    report = build_verify_report(
        {
            "total_count": 2,
            "check_runs": [
                {"name": "lint", "status": "completed", "conclusion": "success"},
                {"name": "tests", "status": "completed", "conclusion": "success"},
            ],
        },
        None,
        head_sha="abc123",
    )

    text = format_verify_comment(report)

    assert report["state"] == "success"
    assert report["status_label"] == "PASS"
    assert "Verification status: ✅ `PASS`" in text
    assert "Informational only." in text
    assert "safe to merge" not in text.lower()
    assert "security approved" not in text.lower()


def test_pr_verify_failure_maps_to_fail() -> None:
    report = build_verify_report(
        {
            "total_count": 1,
            "check_runs": [
                {
                    "name": "tests",
                    "status": "completed",
                    "conclusion": "failure",
                    "details_url": "https://example.test/checks/1",
                }
            ],
        },
        None,
        head_sha="abc123",
    )

    assert report["status_label"] == "FAIL"
    assert report["failure"] == 1


def test_pr_verify_pending_maps_to_pending() -> None:
    report = build_verify_report(
        {
            "total_count": 1,
            "check_runs": [
                {"name": "tests", "status": "in_progress", "conclusion": None},
            ],
        },
        None,
        head_sha="abc123",
    )

    assert report["status_label"] == "PENDING"
    assert report["pending"] == 1


def test_pr_verify_no_sources_maps_to_not_run() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": []},
        {"state": "unknown", "statuses": []},
        {"total_count": 0, "workflow_runs": []},
        head_sha="abc123",
    )
    text = format_verify_comment(report)

    assert report["status_label"] == "NOT_RUN"
    assert "No check runs, commit statuses, or workflow runs were observed" in text
    assert "Verification status: ⚪ `NOT_RUN`" in text


def test_pr_verify_pending_overall_without_concrete_contexts_stays_not_run() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": []},
        {"state": "pending", "statuses": []},
        {"total_count": 0, "workflow_runs": []},
        head_sha="abc123",
    )

    assert report["verify_source"] == "status"
    assert report["state"] == "pending"
    assert report["status_label"] == "NOT_RUN"


def test_pr_verify_permission_failure_maps_to_unknown_safely() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": [], "_error": "forbidden"},
        {"state": "unknown", "statuses": [], "_error": "forbidden"},
        {"total_count": 0, "workflow_runs": [], "_error": "forbidden"},
        head_sha="abc123",
    )
    text = format_verify_comment(report)

    assert report["status_label"] == "UNKNOWN"
    assert "checks: read" in text
    assert "statuses: read" in text
    assert "actions: read" in text


def test_pr_verify_workflow_fallback_with_permission_gap_maps_to_warn() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": [], "_error": "forbidden"},
        {"state": "unknown", "statuses": [], "_error": "forbidden"},
        {
            "total_count": 1,
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "head_sha": "abc123",
                    "html_url": "https://example.test/runs/1",
                }
            ],
        },
        head_sha="abc123",
    )
    text = format_verify_comment(report)

    assert report["verify_source"] == "workflow_runs"
    assert report["status_label"] == "WARN"
    assert "primary_source: workflow_runs" in text
    assert "Workflow runs are a coarse verification signal" in text


def test_pr_verify_output_includes_sources_limitations_and_audit_summary() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": []},
        {
            "state": "success",
            "statuses": [{"context": "ci/build", "state": "success"}],
        },
        None,
        head_sha="abc123def456",
    )
    text = format_verify_comment(report)

    assert report["verify_source"] == "status"
    assert "### 🧩 Sources" in text
    assert "### ⚠️ Limitations" in text
    assert "### 🧾 Audit summary" in text
    assert "head_sha" in text


def test_issue_verify_remains_scoped_unsupported() -> None:
    audit: dict[str, object] = {}

    markdown = _build_verify_markdown(
        tky_mode="local",
        is_pull_request=False,
        issue_number=15,
        dry_run=True,
        client=None,
        audit=audit,
    )

    assert "unsupported in issue-only context" in markdown
    assert audit["scope_status"] == "unsupported_issue_context"


def test_verify_output_stays_no_patch_and_no_legacy_runtime_language() -> None:
    report = build_verify_report(
        {"total_count": 0, "check_runs": []},
        {"state": "unknown", "statuses": []},
        {"total_count": 0, "workflow_runs": []},
        head_sha="abc123",
    )
    text = format_verify_comment(report)

    assert "patch applied" not in text.lower()
    assert "v5" not in text.lower()
    assert "repobrain-community" not in text.lower()
