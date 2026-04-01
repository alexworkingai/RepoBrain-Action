from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
import re
from typing import Any

import orjson


_REQUIRED_WORKFLOW_PERMISSIONS: dict[str, str] = {
    "contents": "read",
    "issues": "write",
    "pull-requests": "write",
    "checks": "write",
    "statuses": "read",
    "actions": "read",
}

_SUPPORTED_RUNTIME_EVENTS = {
    "",
    "issue_comment",
    "workflow_dispatch",
}

_PERMISSION_LEVEL_ORDER = {
    "none": 0,
    "read": 1,
    "write": 2,
    "write-all": 3,
}

_INSTALL_READINESS_CONTRACT_VERSION = "install_readiness_v2"

_FAIL_CATEGORY_PRIORITY = (
    "unsupported_setup",
    "missing_permission",
    "missing_config",
)

_KNOWN_INPUT_SOURCES = {
    "secret",
    "vars",
    "env",
    "secret_or_vars",
    "missing",
    "unknown",
}


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _split_csv(value: str) -> list[str]:
    items = [_norm_text(item) for item in str(value or "").split(",")]
    return [item for item in items if item]


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_permission_sufficient(found: str, required: str) -> bool:
    found_norm = _norm_text(found).lower()
    required_norm = _norm_text(required).lower()
    if found_norm not in _PERMISSION_LEVEL_ORDER:
        return False
    if required_norm not in _PERMISSION_LEVEL_ORDER:
        return False
    return _PERMISSION_LEVEL_ORDER[found_norm] >= _PERMISSION_LEVEL_ORDER[required_norm]


def _extract_permissions_from_workflow_text(workflow_text: str) -> dict[str, str]:
    permissions: dict[str, str] = {}
    for match in re.finditer(r"(?m)^\s{2,}([a-zA-Z-]+)\s*:\s*([a-zA-Z-]+)\s*$", workflow_text):
        key = _norm_text(match.group(1)).lower()
        value = _norm_text(match.group(2)).lower()
        if key in _REQUIRED_WORKFLOW_PERMISSIONS and value in _PERMISSION_LEVEL_ORDER:
            permissions[key] = value
    return permissions


def _make_check(
    *,
    code: str,
    status: str,
    category: str,
    message: str,
    next_step: str,
) -> dict[str, str]:
    return {
        "code": code,
        "status": status,
        "category": category,
        "message": message,
        "next_step": next_step,
    }


def _resolve_input_source(*, value: str, source_hint: str) -> str:
    hint = _norm_text(source_hint).lower()
    if hint in _KNOWN_INPUT_SOURCES:
        if hint == "missing" and value:
            return "env"
        return hint
    if value:
        return "env"
    return "missing"


def _derive_ref_kind(*, ref: str, workflow_ref: str) -> str:
    ref_norm = _norm_text(ref)
    workflow_ref_norm = _norm_text(workflow_ref)
    if ref_norm.startswith("refs/heads/"):
        return "branch_ref"
    if ref_norm.startswith("refs/pull/"):
        return "pull_ref"
    if workflow_ref_norm and "@refs/heads/" in workflow_ref_norm:
        return "workflow_branch_ref"
    if workflow_ref_norm and "@refs/tags/" in workflow_ref_norm:
        return "workflow_tag_ref"
    if workflow_ref_norm:
        return "workflow_other_ref"
    return "unknown"


def _reason_for_status(
    *,
    overall_status: str,
    fail_codes: list[str],
) -> tuple[str, str]:
    fail_set = {code.strip() for code in fail_codes if code.strip()}
    if overall_status == "READY":
        return (
            "ready_all_prereqs_satisfied",
            "All required GitHub App onboarding prerequisites are satisfied.",
        )
    if overall_status == "UNSUPPORTED_SETUP":
        if "runtime_event_unsupported" in fail_set:
            return (
                "unsupported_runtime_event",
                "Runtime event is unsupported for onboarding validation.",
            )
        if "repository_selection_mode_invalid" in fail_set:
            return (
                "unsupported_repository_selection_mode",
                "Repository selection mode is invalid.",
            )
        if "selected_repositories_repo_not_allowed" in fail_set:
            return (
                "selected_repo_binding_mismatch",
                "Current repository is not included in selected-repository rollout allowlist.",
            )
        if "workflow_issue_comment_missing" in fail_set:
            return (
                "issue_comment_trigger_missing",
                "Workflow does not expose issue_comment trigger required for command flow.",
            )
        if "workflow_file_missing" in fail_set:
            return (
                "workflow_file_missing",
                "RepoBrain workflow file is missing or unresolved.",
            )
        return ("unsupported_setup_detected", "Unsupported setup topology detected.")
    if overall_status == "MISSING_PERMISSION":
        if "workflow_permissions_missing" in fail_set:
            return (
                "workflow_permissions_missing",
                "Workflow permissions are missing or weaker than required.",
            )
        return ("missing_permission_detected", "Required permission prerequisites are missing.")
    if overall_status == "MISSING_CONFIG":
        if "github_app_id_missing" in fail_set:
            return ("github_app_id_missing", "GitHub App ID is missing.")
        if "github_app_id_invalid" in fail_set:
            return ("github_app_id_invalid", "GitHub App ID format is invalid.")
        if "github_app_installation_id_missing" in fail_set:
            return ("github_app_installation_id_missing", "GitHub App installation ID is missing.")
        if "github_app_installation_id_invalid" in fail_set:
            return ("github_app_installation_id_invalid", "GitHub App installation ID format is invalid.")
        if "github_app_private_key_missing" in fail_set:
            return ("github_app_private_key_missing", "GitHub App private key is missing.")
        if "selected_repositories_missing" in fail_set:
            return ("selected_repositories_missing", "Selected repositories allowlist is missing.")
        return ("missing_config_detected", "Configuration prerequisites are missing.")
    return ("unknown_status", "Readiness status could not be classified.")


def evaluate_install_readiness(
    *,
    workflow_path: Path,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_env = dict(env or {})
    checks: list[dict[str, str]] = []
    next_steps: list[str] = []

    app_id = _norm_text(source_env.get("RB_GH_APP_ID", ""))
    installation_id = _norm_text(source_env.get("RB_GH_APP_INSTALLATION_ID", ""))
    app_id_source = _resolve_input_source(
        value=app_id,
        source_hint=_norm_text(source_env.get("RB_GH_APP_ID_SOURCE", "")),
    )
    installation_id_source = _resolve_input_source(
        value=installation_id,
        source_hint=_norm_text(source_env.get("RB_GH_APP_INSTALLATION_ID_SOURCE", "")),
    )
    private_key_inline = _norm_text(source_env.get("RB_GH_APP_PRIVATE_KEY", ""))
    private_key_path = _norm_text(source_env.get("RB_GH_APP_PRIVATE_KEY_PATH", ""))
    webhook_secret = _norm_text(source_env.get("RB_GH_APP_WEBHOOK_SECRET", ""))
    repo_selection_mode = _norm_text(source_env.get("RB_GH_APP_REPOSITORY_SELECTION", "selected")).lower()
    selected_repositories = _split_csv(source_env.get("RB_GH_APP_SELECTED_REPOS", ""))
    selected_repositories_norm = {item.lower() for item in selected_repositories}
    current_repo = _norm_text(source_env.get("GITHUB_REPOSITORY", "")).lower()
    event_name = _norm_text(source_env.get("GITHUB_EVENT_NAME", "")).lower()

    private_key_path_exists = bool(private_key_path and Path(private_key_path).exists())
    private_key_path_readable = False
    if private_key_path_exists:
        try:
            _ = Path(private_key_path).read_text(encoding="utf-8")
            private_key_path_readable = True
        except OSError:
            private_key_path_readable = False
    private_key_present = bool(private_key_inline or private_key_path_readable)
    private_key_source = (
        "env_inline"
        if private_key_inline
        else ("path" if private_key_path_readable else "missing")
    )

    if event_name in _SUPPORTED_RUNTIME_EVENTS:
        checks.append(
            _make_check(
                code="runtime_event_supported",
                status="PASS",
                category="runtime",
                message=f"Runtime event is supported for onboarding checks (`{event_name or 'local/manual'}`).",
                next_step="Proceed with readiness checks.",
            )
        )
    else:
        checks.append(
            _make_check(
                code="runtime_event_unsupported",
                status="FAIL",
                category="unsupported_setup",
                message=f"Unsupported event context for onboarding validation (`{event_name}`).",
                next_step="Run readiness on `issue_comment` or `workflow_dispatch` context.",
            )
        )
        next_steps.append("Use `workflow_dispatch` or `/repobrain ...` issue_comment context for install readiness checks.")

    if repo_selection_mode not in {"selected", "all"}:
        checks.append(
            _make_check(
                code="repository_selection_mode_invalid",
                status="FAIL",
                category="unsupported_setup",
                message=f"Invalid `RB_GH_APP_REPOSITORY_SELECTION` value (`{repo_selection_mode}`).",
                next_step="Set `RB_GH_APP_REPOSITORY_SELECTION` to `selected` or `all`.",
            )
        )
        next_steps.append("Set `RB_GH_APP_REPOSITORY_SELECTION` to `selected` (recommended) or `all`.")
    else:
        checks.append(
            _make_check(
                code="repository_selection_mode_valid",
                status="PASS",
                category="config",
                message=f"Repository rollout mode is `{repo_selection_mode}`.",
                next_step="Keep `selected` for controlled rollout where possible.",
            )
        )
        if repo_selection_mode == "selected" and not selected_repositories:
            checks.append(
                _make_check(
                    code="selected_repositories_missing",
                    status="FAIL",
                    category="missing_config",
                    message="Selected-repository rollout is enabled but `RB_GH_APP_SELECTED_REPOS` is empty.",
                    next_step="Set `RB_GH_APP_SELECTED_REPOS` to a comma-separated allowlist.",
                )
            )
            next_steps.append("Populate `RB_GH_APP_SELECTED_REPOS` for selected-repository onboarding.")
        elif repo_selection_mode == "selected":
            checks.append(
                _make_check(
                    code="selected_repositories_configured",
                    status="PASS",
                    category="config",
                    message=f"Selected repositories configured (`{len(selected_repositories)}`).",
                    next_step="Verify installed repositories match this allowlist.",
                )
            )
            if current_repo and current_repo not in selected_repositories_norm:
                checks.append(
                    _make_check(
                        code="selected_repositories_repo_not_allowed",
                        status="FAIL",
                        category="unsupported_setup",
                        message=(
                            f"Current repository `{current_repo}` is not included in "
                            "`RB_GH_APP_SELECTED_REPOS` allowlist."
                        ),
                        next_step="Add current repository to allowlist or install App on this repository.",
                    )
                )
                next_steps.append(
                    "Add current repository to `RB_GH_APP_SELECTED_REPOS` or update GitHub App selected-repository installation."
                )
        elif repo_selection_mode == "all" and selected_repositories:
            checks.append(
                _make_check(
                    code="selected_repositories_ignored_in_all_mode",
                    status="WARN",
                    category="config",
                    message="`RB_GH_APP_SELECTED_REPOS` is set but rollout mode is `all`; allowlist is ignored.",
                    next_step="Clear selected allowlist or switch rollout mode back to `selected`.",
                )
            )

    if app_id:
        if app_id.isdigit():
            checks.append(
                _make_check(
                    code="github_app_id_present",
                    status="PASS",
                    category="config",
                    message="`RB_GH_APP_ID` is configured.",
                    next_step="Keep App ID stable across environments.",
                )
            )
        else:
            checks.append(
                _make_check(
                    code="github_app_id_invalid",
                    status="FAIL",
                    category="missing_config",
                    message="`RB_GH_APP_ID` is set but format is invalid (expected numeric App ID).",
                    next_step="Set numeric App ID from GitHub App settings.",
                )
            )
            next_steps.append("Set `RB_GH_APP_ID` to numeric GitHub App id.")
    else:
        checks.append(
            _make_check(
                code="github_app_id_missing",
                status="FAIL",
                category="missing_config",
                message="`RB_GH_APP_ID` is missing.",
                next_step="Set App ID in repository or organization secrets/variables.",
            )
        )
        next_steps.append("Set `RB_GH_APP_ID` for GitHub App-first mode.")

    if installation_id:
        if installation_id.isdigit():
            checks.append(
                _make_check(
                    code="github_app_installation_id_present",
                    status="PASS",
                    category="config",
                    message="`RB_GH_APP_INSTALLATION_ID` is configured.",
                    next_step="Ensure installation id matches selected repository install.",
                )
            )
        else:
            checks.append(
                _make_check(
                    code="github_app_installation_id_invalid",
                    status="FAIL",
                    category="missing_config",
                    message=(
                        "`RB_GH_APP_INSTALLATION_ID` is set but format is invalid "
                        "(expected numeric installation ID)."
                    ),
                    next_step="Set numeric installation id from GitHub App installation page.",
                )
            )
            next_steps.append("Set `RB_GH_APP_INSTALLATION_ID` to numeric installation id.")
    else:
        checks.append(
            _make_check(
                code="github_app_installation_id_missing",
                status="FAIL",
                category="missing_config",
                message="`RB_GH_APP_INSTALLATION_ID` is missing.",
                next_step="Set installation id from GitHub App installation details.",
            )
        )
        next_steps.append("Set `RB_GH_APP_INSTALLATION_ID` for the target installation.")

    if private_key_inline:
        checks.append(
            _make_check(
                code="github_app_private_key_present",
                status="PASS",
                category="config",
                message="GitHub App private key is available (`env_inline`).",
                next_step="Rotate key regularly and keep key material secret-scoped.",
            )
        )
    elif private_key_path and not private_key_path_exists:
        checks.append(
            _make_check(
                code="github_app_private_key_path_missing",
                status="FAIL",
                category="missing_config",
                message=f"`RB_GH_APP_PRIVATE_KEY_PATH` is set but file is missing (`{private_key_path}`).",
                next_step="Fix key path or provide `RB_GH_APP_PRIVATE_KEY` secret.",
            )
        )
        next_steps.append("Fix `RB_GH_APP_PRIVATE_KEY_PATH` or set `RB_GH_APP_PRIVATE_KEY` secret.")
    elif private_key_path_exists and not private_key_path_readable:
        checks.append(
            _make_check(
                code="github_app_private_key_path_unreadable",
                status="FAIL",
                category="missing_config",
                message=f"`RB_GH_APP_PRIVATE_KEY_PATH` exists but is not readable (`{private_key_path}`).",
                next_step="Grant read access to key file or use inline secret key.",
            )
        )
        next_steps.append("Grant read access to key file or set `RB_GH_APP_PRIVATE_KEY` secret.")
    elif private_key_present:
        checks.append(
            _make_check(
                code="github_app_private_key_present",
                status="PASS",
                category="config",
                message=f"GitHub App private key is available (`{private_key_source}`).",
                next_step="Rotate key regularly and keep key material secret-scoped.",
            )
        )
    else:
        checks.append(
            _make_check(
                code="github_app_private_key_missing",
                status="FAIL",
                category="missing_config",
                message="Neither `RB_GH_APP_PRIVATE_KEY` nor a readable `RB_GH_APP_PRIVATE_KEY_PATH` is configured.",
                next_step="Set inline private key secret or configure a readable key path.",
            )
        )
        next_steps.append("Provide `RB_GH_APP_PRIVATE_KEY` (recommended) or `RB_GH_APP_PRIVATE_KEY_PATH`.")

    if webhook_secret:
        checks.append(
            _make_check(
                code="github_app_webhook_secret_present",
                status="PASS",
                category="config",
                message="`RB_GH_APP_WEBHOOK_SECRET` is configured.",
                next_step="Validate webhook signature checks in receiving infrastructure.",
            )
        )
    else:
        checks.append(
            _make_check(
                code="github_app_webhook_secret_missing",
                status="WARN",
                category="missing_config",
                message="`RB_GH_APP_WEBHOOK_SECRET` is not configured.",
                next_step="Set webhook secret before external webhook exposure.",
            )
        )
        next_steps.append("Set `RB_GH_APP_WEBHOOK_SECRET` before enabling external webhook ingestion.")

    if workflow_path.exists():
        workflow_text = workflow_path.read_text(encoding="utf-8")
        workflow_permissions = _extract_permissions_from_workflow_text(workflow_text)
        missing_permissions: list[str] = []
        for permission, required_level in _REQUIRED_WORKFLOW_PERMISSIONS.items():
            found_level = workflow_permissions.get(permission, "none")
            if not _is_permission_sufficient(found_level, required_level):
                missing_permissions.append(f"{permission}:{required_level}")
        if missing_permissions:
            checks.append(
                _make_check(
                    code="workflow_permissions_missing",
                    status="FAIL",
                    category="missing_permission",
                    message=(
                        "Workflow permissions are missing or too weak: "
                        + ", ".join(sorted(missing_permissions))
                    ),
                    next_step="Update `.github/workflows/repobrain.yml` permissions to required minimums.",
                )
            )
            next_steps.append("Align workflow permissions with onboarding docs (`docs/onboarding/github_app_setup.md`).")
        else:
            checks.append(
                _make_check(
                    code="workflow_permissions_ready",
                    status="PASS",
                    category="permission",
                    message="Workflow permissions satisfy GitHub App-first baseline.",
                    next_step="Keep permission scope minimal and explicit.",
                )
            )
        issue_comment_enabled = "issue_comment:" in workflow_text
        if issue_comment_enabled:
            checks.append(
                _make_check(
                    code="workflow_issue_comment_enabled",
                    status="PASS",
                    category="workflow",
                    message="Workflow includes issue_comment trigger for command-driven runs.",
                    next_step="Keep issue_comment trigger restricted to `/repobrain` commands.",
                )
            )
        else:
            checks.append(
                _make_check(
                    code="workflow_issue_comment_missing",
                    status="FAIL",
                    category="unsupported_setup",
                    message="Workflow does not include `issue_comment` trigger required for normal RepoBrain command flow.",
                    next_step="Enable issue_comment trigger in `.github/workflows/repobrain.yml`.",
                )
            )
            next_steps.append("Enable `issue_comment` trigger for normal RepoBrain onboarding flow.")
    else:
        checks.append(
            _make_check(
                code="workflow_file_missing",
                status="FAIL",
                category="unsupported_setup",
                message=f"Workflow file not found: `{workflow_path.as_posix()}`.",
                next_step="Point readiness checker to a valid RepoBrain workflow file.",
            )
        )
        next_steps.append("Provide a valid RepoBrain workflow path to readiness checker.")
        workflow_permissions = {}
        missing_permissions = list(_REQUIRED_WORKFLOW_PERMISSIONS.keys())
        issue_comment_enabled = False

    fail_categories = {
        check["category"]
        for check in checks
        if check["status"] == "FAIL"
    }
    fail_codes = [
        str(check.get("code", "")).strip()
        for check in checks
        if str(check.get("status", "")).upper() == "FAIL"
    ]
    fail_codes_by_category = {
        category: sorted(
            str(check.get("code", "")).strip()
            for check in checks
            if str(check.get("status", "")).upper() == "FAIL"
            and str(check.get("category", "")).strip() == category
            and str(check.get("code", "")).strip()
        )
        for category in _FAIL_CATEGORY_PRIORITY
    }
    fail_counts_by_category = {
        category: len(fail_codes_by_category[category])
        for category in _FAIL_CATEGORY_PRIORITY
    }
    if "unsupported_setup" in fail_categories:
        overall_status = "UNSUPPORTED_SETUP"
    elif "missing_permission" in fail_categories:
        overall_status = "MISSING_PERMISSION"
    elif "missing_config" in fail_categories:
        overall_status = "MISSING_CONFIG"
    else:
        overall_status = "READY"
    status_reason_code, status_reason_short = _reason_for_status(
        overall_status=overall_status,
        fail_codes=fail_codes,
    )

    summary = {
        "pass": sum(1 for check in checks if check["status"] == "PASS"),
        "fail": sum(1 for check in checks if check["status"] == "FAIL"),
        "warn": sum(1 for check in checks if check["status"] == "WARN"),
    }
    generation_event = _norm_text(
        source_env.get(
            "RB_READINESS_GENERATION_EVENT_NAME",
            source_env.get("GITHUB_EVENT_NAME", "local/manual"),
        )
    ) or "local/manual"
    generation_workflow_path = _norm_text(
        source_env.get("RB_READINESS_GENERATION_WORKFLOW_PATH", workflow_path.as_posix())
    ) or workflow_path.as_posix()
    generation_ref = _norm_text(
        source_env.get("RB_READINESS_GENERATION_REF", source_env.get("GITHUB_REF", "n/a"))
    ) or "n/a"
    generation_sha = _norm_text(
        source_env.get("RB_READINESS_GENERATION_SHA", source_env.get("GITHUB_SHA", "n/a"))
    ) or "n/a"
    generation_workflow_ref = _norm_text(
        source_env.get("RB_READINESS_GENERATION_WORKFLOW_REF", source_env.get("GITHUB_WORKFLOW_REF", "n/a"))
    ) or "n/a"
    generation_workflow_sha = _norm_text(
        source_env.get("RB_READINESS_GENERATION_WORKFLOW_SHA", source_env.get("GITHUB_WORKFLOW_SHA", "n/a"))
    ) or "n/a"
    generation_run_id = _norm_text(
        source_env.get("RB_READINESS_GENERATION_RUN_ID", source_env.get("GITHUB_RUN_ID", "n/a"))
    ) or "n/a"
    generation_run_attempt = _norm_text(
        source_env.get("RB_READINESS_GENERATION_RUN_ATTEMPT", source_env.get("GITHUB_RUN_ATTEMPT", "n/a"))
    ) or "n/a"
    generation_job_name = _norm_text(source_env.get("RB_READINESS_GENERATION_JOB_NAME", "n/a")) or "n/a"
    generation_ref_kind = _derive_ref_kind(ref=generation_ref, workflow_ref=generation_workflow_ref)

    payload: dict[str, Any] = {
        "readiness_contract_version": _INSTALL_READINESS_CONTRACT_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "installation_model": "github_app_first",
        "overall_status": overall_status,
        "status_reason_code": status_reason_code,
        "status_reason_short": status_reason_short,
        "ready_for_ask_review_fix": overall_status == "READY",
        "repository_selection_mode": repo_selection_mode,
        "selected_repositories": selected_repositories,
        "checks": checks,
        "summary": summary,
        "blocking_summary": {
            "fail_codes": sorted(fail_codes),
            "fail_codes_by_category": fail_codes_by_category,
            "fail_counts_by_category": fail_counts_by_category,
        },
        "next_steps": list(dict.fromkeys(next_steps)),
        "workflow_probe": {
            "workflow_path": workflow_path.as_posix(),
            "exists": workflow_path.exists(),
            "issue_comment_enabled": issue_comment_enabled,
            "required_permissions": dict(_REQUIRED_WORKFLOW_PERMISSIONS),
            "detected_permissions": workflow_permissions,
            "missing_permissions": sorted(missing_permissions),
        },
        "readiness_provenance": {
            "generation_event_name": generation_event,
            "generation_workflow_path": generation_workflow_path,
            "generation_ref": generation_ref,
            "generation_sha": generation_sha,
            "generation_ref_kind": generation_ref_kind,
            "generation_workflow_ref": generation_workflow_ref,
            "generation_workflow_sha": generation_workflow_sha,
            "generation_run_id": generation_run_id,
            "generation_run_attempt": generation_run_attempt,
            "generation_job_name": generation_job_name,
        },
        "inputs_seen": {
            "event_name": generation_event,
            "current_repository": current_repo or "n/a",
            "app_id_present": bool(app_id),
            "app_id_source": app_id_source,
            "installation_id_present": bool(installation_id),
            "installation_id_source": installation_id_source,
            "private_key_source": private_key_source,
            "private_key_path_present": bool(private_key_path),
            "private_key_path_exists": private_key_path_exists,
            "private_key_path_readable": private_key_path_readable,
            "webhook_secret_present": bool(webhook_secret),
            "selected_repositories_count": len(selected_repositories),
        },
    }
    return payload


def render_install_readiness_markdown(payload: dict[str, Any]) -> str:
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        checks = []
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    next_steps = payload.get("next_steps", [])
    if not isinstance(next_steps, list):
        next_steps = []

    lines: list[str] = [
        "# RepoBrain GitHub App Install Readiness",
        "",
        f"- Contract version: `{payload.get('readiness_contract_version', 'install_readiness_v1')}`",
        f"- Installation model: `{payload.get('installation_model', 'github_app_first')}`",
        f"- Overall status: `{payload.get('overall_status', 'UNSUPPORTED_SETUP')}`",
        f"- Status reason: `{payload.get('status_reason_code', 'unknown')}`",
        f"- Status summary: {payload.get('status_reason_short', 'n/a')}",
        f"- Ready for Ask/Review/Fix: `{'yes' if bool(payload.get('ready_for_ask_review_fix', False)) else 'no'}`",
        f"- Repository selection mode: `{payload.get('repository_selection_mode', 'selected')}`",
        f"- Generation event: `{payload.get('readiness_provenance', {}).get('generation_event_name', 'local/manual')}`",
        f"- Generation ref: `{payload.get('readiness_provenance', {}).get('generation_ref', 'n/a')}`",
        f"- App ID source: `{payload.get('inputs_seen', {}).get('app_id_source', 'unknown')}`",
        "",
        "## Check Summary",
        f"- PASS: `{int(summary.get('pass', 0) or 0)}`",
        f"- FAIL: `{int(summary.get('fail', 0) or 0)}`",
        f"- WARN: `{int(summary.get('warn', 0) or 0)}`",
        "",
        "## Checks",
    ]
    for item in checks:
        if not isinstance(item, dict):
            continue
        status = _norm_text(item.get("status", "UNKNOWN")).upper()
        code = _norm_text(item.get("code", "unknown"))
        message = _norm_text(item.get("message", ""))
        lines.append(f"- [{status}] `{code}`: {message}")

    lines.extend(["", "## Next Safe Steps"])
    if next_steps:
        lines.extend(f"- {str(step)}" for step in next_steps if _norm_text(step))
    else:
        lines.append("- Setup is ready. Proceed with controlled Ask/Review/Fix first-run validation.")
    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check RepoBrain GitHub App install readiness.")
    parser.add_argument(
        "--workflow",
        default=".github/workflows/repobrain.yml",
        help="Path to RepoBrain workflow file.",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/onboarding/repobrain_install_readiness.json",
        help="Path to JSON readiness output.",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/onboarding/repobrain_install_readiness.md",
        help="Path to Markdown readiness output.",
    )
    parser.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="Return non-zero when readiness is not READY.",
    )
    args = parser.parse_args(argv)

    payload = evaluate_install_readiness(
        workflow_path=Path(args.workflow),
        env={key: value for key, value in os.environ.items()},
    )
    markdown = render_install_readiness_markdown(payload)
    _write_json(Path(args.output_json), payload)
    _write_text(Path(args.output_md), markdown)

    print(f"INSTALL_READINESS_JSON={Path(args.output_json).as_posix()}")
    print(f"INSTALL_READINESS_MD={Path(args.output_md).as_posix()}")
    print(f"INSTALL_READINESS_STATUS={payload.get('overall_status', 'UNSUPPORTED_SETUP')}")

    if args.fail_on_not_ready and str(payload.get("overall_status", "")).upper() != "READY":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
