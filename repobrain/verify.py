from __future__ import annotations

from typing import Any

FAIL_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required"}
SUCCESS_CONCLUSIONS = {"success"}
NEUTRAL_CONCLUSIONS = {"neutral", "skipped"}
PENDING_STATUSES = {"queued", "in_progress", "pending"}


def _normalize_str(value: object) -> str:
    return str(value or "").strip().lower()


def _report_from_check_runs(check_runs_json: dict[str, Any]) -> dict[str, Any]:
    runs = check_runs_json.get("check_runs", [])
    if not isinstance(runs, list):
        runs = []
    runs = [run for run in runs if isinstance(run, dict)]

    failures: list[dict[str, str | None]] = []
    success = 0
    failure = 0
    pending = 0
    neutral = 0

    for run in runs:
        status = _normalize_str(run.get("status"))
        conclusion = _normalize_str(run.get("conclusion"))
        name = str(run.get("name", "Unnamed check"))
        details_url = run.get("details_url")
        details_url = str(details_url) if isinstance(details_url, str) and details_url.strip() else None

        if status in {"queued", "in_progress"}:
            pending += 1
            continue

        if conclusion in FAIL_CONCLUSIONS:
            failure += 1
            failures.append(
                {
                    "name": name,
                    "conclusion": conclusion or "failure",
                    "details_url": details_url,
                }
            )
        elif conclusion in SUCCESS_CONCLUSIONS:
            success += 1
        elif conclusion in NEUTRAL_CONCLUSIONS:
            neutral += 1
        elif status in PENDING_STATUSES:
            pending += 1
        else:
            neutral += 1

    if failure > 0:
        state = "failure"
    elif pending > 0:
        state = "pending"
    elif runs:
        state = "success"
    else:
        state = "unknown"

    return {
        "state": state,
        "total": len(runs),
        "success": success,
        "failure": failure,
        "pending": pending,
        "neutral": neutral,
        "failures": failures,
    }


def _report_from_combined_status(status_json: dict[str, Any] | None) -> dict[str, Any]:
    status_json = status_json or {}
    contexts = status_json.get("statuses", [])
    if not isinstance(contexts, list):
        contexts = []
    contexts = [ctx for ctx in contexts if isinstance(ctx, dict)]

    failures: list[dict[str, str | None]] = []
    success = 0
    failure = 0
    pending = 0
    neutral = 0

    for ctx in contexts:
        state = _normalize_str(ctx.get("state"))
        name = str(ctx.get("context", "status"))
        details_url = ctx.get("target_url")
        details_url = str(details_url) if isinstance(details_url, str) and details_url.strip() else None

        if state == "failure" or state == "error":
            failure += 1
            failures.append(
                {"name": name, "conclusion": state or "failure", "details_url": details_url}
            )
        elif state == "success":
            success += 1
        elif state == "pending":
            pending += 1
        else:
            neutral += 1

    overall = _normalize_str(status_json.get("state"))
    if failure > 0:
        final_state = "failure"
    elif pending > 0 or overall == "pending":
        final_state = "pending"
    elif contexts or overall == "success":
        final_state = "success"
    else:
        final_state = "unknown"

    return {
        "state": final_state,
        "total": len(contexts),
        "success": success,
        "failure": failure,
        "pending": pending,
        "neutral": neutral,
        "failures": failures,
    }


def build_verify_report(
    check_runs_json: dict[str, Any],
    status_json: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a lightweight verification report from GitHub checks/status APIs."""
    if (
        str(check_runs_json.get("_error", "")).lower() == "forbidden"
        and isinstance(status_json, dict)
        and str(status_json.get("_error", "")).lower() == "forbidden"
    ):
        return {
            "state": "unknown",
            "total": 0,
            "success": 0,
            "failure": 0,
            "pending": 0,
            "neutral": 0,
            "failures": [],
            "message": (
                "Verification unavailable due to token permissions. "
                "Add `checks: read` and `statuses: read` to workflow permissions."
            ),
        }

    total_count = check_runs_json.get("total_count", 0)
    if isinstance(total_count, int) and total_count > 0:
        return _report_from_check_runs(check_runs_json)
    return _report_from_combined_status(status_json)
