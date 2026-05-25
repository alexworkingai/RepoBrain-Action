from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from repobrain import __version__ as REPOBRAIN_VERSION
from repobrain.topocore_backend import TopoCoreBackendError, resolve_backend

SUPPORTED_COMMANDS: tuple[str, ...] = (
    "/repobrain help",
    "/repobrain ask",
    "/repobrain locate",
    "/repobrain explain",
    "/repobrain review",
    "/repobrain verify",
    "/repobrain fix",
    "/repobrain audit",
    "/repobrain score",
    "/repobrain doctor",
    "/repobrain status",
)
ROADMAP_COMMANDS: tuple[str, ...] = ()
FIX_LITE_GUIDANCE = "fix-lite is not a product command. Use /repobrain fix."

_DANGEROUS_PERMISSION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("pull_request_target", r"\bpull_request_target\b"),
    ("contents: write", r"contents\s*:\s*write"),
    ("checks: write", r"checks\s*:\s*write"),
    ("pull-requests: write", r"pull-requests\s*:\s*write"),
)


def build_status_report(
    *,
    repo_root: Path,
    query: str,
    github_context: dict[str, Any] | None,
) -> dict[str, Any]:
    workflow = _workflow_snapshot(repo_root)
    event_context = _event_context_label(github_context)
    repo_name = str((github_context or {}).get("repository", "") or "").strip() or "unknown"
    topocore_mode = _topocore_dependency_mode(workflow=workflow)
    return {
        "version": REPOBRAIN_VERSION,
        "repo_name": repo_name,
        "event_context": event_context,
        "query": str(query or "").strip(),
        "supported_commands": list(SUPPORTED_COMMANDS),
        "roadmap_commands": list(ROADMAP_COMMANDS),
        "fix_lite_guidance": FIX_LITE_GUIDANCE,
        "action_runtime_mode": _action_runtime_mode(),
        "topocore_dependency_mode": topocore_mode,
        "topocore_policy": [
            "v6-only runtime policy",
            "no v5 fallback",
            "private_checkout beta-only",
            "audit keeps a static baseline and may apply contract-validated private v6 enrichment when available",
            "score is a compact summary view of the same guarded audit engine",
        ],
        "safety_policy": [
            "no patch/autofix",
            "no RepoBrain-created branch/commit/PR",
            "verify is informational",
            "fix is proposal/governance only",
            "audit is informational only",
            "score is informational only",
        ],
        "workflow": workflow,
        "install_hints": [
            "Use /repobrain doctor for setup diagnostics.",
            "Use /repobrain audit for the 100-point repository score.",
            "Use /repobrain score for a compact score summary from the same audit engine.",
        ],
    }


def build_doctor_report(
    *,
    repo_root: Path,
    query: str,
    github_context: dict[str, Any] | None,
) -> dict[str, Any]:
    workflow = _workflow_snapshot(repo_root)
    event_context = _event_context_label(github_context)
    repo_name = str((github_context or {}).get("repository", "") or "").strip() or "unknown"
    checks: list[dict[str, str]] = []

    checks.append(
        _doctor_check(
            name="Workflow/action context",
            status=_workflow_context_status(workflow),
            detail=(
                f"Event context: {event_context}. "
                f"GitHub Actions runtime: `{_yes_no(_running_in_actions())}`. "
                f"Action path available: `{_yes_no(bool(os.environ.get('GITHUB_ACTION_PATH', '').strip()))}`. "
                f"Workspace available: `{_yes_no(bool(os.environ.get('GITHUB_WORKSPACE', '').strip()))}`. "
                f"Workflow file detected: `{_yes_no(workflow['exists'])}`."
            ),
        )
    )

    checks.append(
        _doctor_check(
            name="Permissions baseline",
            status=_permissions_status(workflow),
            detail=_permissions_detail(workflow),
        )
    )

    checks.append(
        _doctor_check(
            name="TopoCore v6 setup",
            status=_topocore_setup_status(workflow),
            detail=_topocore_setup_detail(workflow),
        )
    )

    backend_status, backend_detail = _backend_policy_check()
    checks.append(_doctor_check(name="Backend policy", status=backend_status, detail=backend_detail))

    checks.append(
        _doctor_check(
            name="Command surface",
            status="PASS",
            detail=(
                "Supported commands: help, ask, locate, explain, review, verify, fix, audit, doctor, status. "
                "Supported commands also include score as a compact summary of the same guarded audit engine. "
                "fix-lite is unsupported and redirects to /repobrain fix."
            ),
        )
    )

    checks.append(
        _doctor_check(
            name="Fork/private boundary",
            status=_fork_boundary_status(workflow=workflow, github_context=github_context),
            detail=_fork_boundary_detail(workflow=workflow, github_context=github_context),
        )
    )

    overall_status = _overall_doctor_status(checks)
    issues_found = [item["detail"] for item in checks if item["status"] in {"WARN", "FAIL"}]
    recommended_fixes = _doctor_recommended_fixes(workflow=workflow, checks=checks)
    limitations = [
        "Doctor is a report-only diagnostic and does not directly re-run private checkout or import probes.",
        "Secret values are never printed; some setup details may therefore remain unknown.",
    ]
    if github_context and bool(github_context.get("is_pr", False)) and not _fork_context_known(github_context):
        limitations.append("Fork state could not be fully verified from the current PR payload.")

    return {
        "overall_status": overall_status,
        "repo_name": repo_name,
        "event_context": event_context,
        "query": str(query or "").strip(),
        "checks": checks,
        "issues_found": issues_found[:6],
        "recommended_fixes": recommended_fixes[:6],
        "limitations": limitations[:4],
        "workflow": workflow,
        "supported_commands": list(SUPPORTED_COMMANDS),
    }


def _doctor_check(*, name: str, status: str, detail: str) -> dict[str, str]:
    normalized_status = str(status or "UNKNOWN").strip().upper()
    if normalized_status not in {"PASS", "WARN", "FAIL", "UNKNOWN"}:
        normalized_status = "UNKNOWN"
    return {
        "name": str(name or "").strip() or "Unnamed check",
        "status": normalized_status,
        "detail": str(detail or "").strip() or "No detail recorded.",
    }


def _workflow_context_status(workflow: dict[str, Any]) -> str:
    if workflow["exists"] and _running_in_actions():
        return "PASS"
    if workflow["exists"]:
        return "WARN"
    return "UNKNOWN"


def _permissions_status(workflow: dict[str, Any]) -> str:
    if not workflow["exists"]:
        return "UNKNOWN"
    if workflow["dangerous_permissions"]:
        return "WARN"
    if workflow["permissions_explicit"]:
        return "PASS"
    return "WARN"


def _permissions_detail(workflow: dict[str, Any]) -> str:
    if not workflow["exists"]:
        return "RepoBrain workflow file was not found, so permission posture could not be assessed."
    if workflow["dangerous_permissions"]:
        joined = ", ".join(f"`{item}`" for item in workflow["dangerous_permissions"])
        return (
            "Workflow permissions or triggers need review: "
            f"{joined}. Current external baseline should stay read-mostly."
        )
    if workflow["permissions_explicit"]:
        return "Workflow permissions are explicit and no dangerous write-heavy baseline was detected."
    return "Workflow permissions are not explicit in the detected RepoBrain workflow."


def _topocore_setup_status(workflow: dict[str, Any]) -> str:
    if _local_path_present():
        return "PASS"
    if workflow["topocore_secret_referenced"]:
        return "WARN"
    return "UNKNOWN"


def _topocore_setup_detail(workflow: dict[str, Any]) -> str:
    local_path_present = _local_path_present()
    secret_env_visible = _env_key_present("TOPOCORE_V6_REPO_TOKEN")
    expected_secret = "Expected secret name: `TOPOCORE_V6_REPO_TOKEN`."
    if local_path_present:
        return (
            "TopoCore v6 private runtime path is present for this run. "
            f"{expected_secret} Secret value remains hidden, and TopoCore source stays private."
        )
    if workflow["topocore_secret_referenced"]:
        return (
            "Workflow references `TOPOCORE_V6_REPO_TOKEN`, but the secret value is not directly inspectable "
            f"and local runtime path visibility is `{_yes_no(local_path_present)}`. "
            f"Verify token access and private checkout if setup fails. {expected_secret}"
        )
    if secret_env_visible:
        return (
            "`TOPOCORE_V6_REPO_TOKEN` is visible as an environment key for this run, but runtime path propagation "
            f"was not detected. {expected_secret}"
        )
    return (
        "TopoCore v6 setup could not be directly verified from runtime-safe signals. "
        f"{expected_secret}"
    )


def _backend_policy_check() -> tuple[str, str]:
    try:
        resolution = resolve_backend()
    except TopoCoreBackendError:
        return (
            "FAIL",
            "Legacy backend selection is configured or invalid. RepoBrain requires `RB_TOPOCORE_BACKEND=auto|v6` and never falls back to v5.",
        )

    return (
        "PASS",
        (
            f"Requested backend policy is `{resolution.requested_backend}` from `{resolution.source_env}`; "
            "selected backend stays `v6`, there is no v5 fallback, private_checkout is beta-only, "
            "and audit keeps a static baseline with optional contract-validated private v6 enrichment when the runtime exposes it."
        ),
    )


def _fork_boundary_status(*, workflow: dict[str, Any], github_context: dict[str, Any] | None) -> str:
    if workflow["uses_pull_request_target"]:
        return "FAIL"
    if not github_context or not bool(github_context.get("is_pr", False)):
        return "PASS"
    if _is_fork_pr(github_context) is True:
        return "WARN"
    if _is_fork_pr(github_context) is False:
        return "PASS"
    return "UNKNOWN"


def _fork_boundary_detail(*, workflow: dict[str, Any], github_context: dict[str, Any] | None) -> str:
    if workflow["uses_pull_request_target"]:
        return "Workflow uses `pull_request_target`, which is outside the supported external safety baseline."
    if not github_context or not bool(github_context.get("is_pr", False)):
        return (
            "No `pull_request_target` trigger was detected. "
            "No PR fork context is active for this run. Policy remains: no private token to untrusted fork code by default."
        )
    fork_state = _is_fork_pr(github_context)
    if fork_state is True:
        return (
            "No `pull_request_target` trigger was detected. Current PR appears to come from a fork or cross-repo head. "
            "Private token use for untrusted fork code should remain restricted."
        )
    if fork_state is False:
        return (
            "No `pull_request_target` trigger was detected. "
            "Current PR appears to be same-repository. No fork-boundary concern was detected from available metadata."
        )
    return "No `pull_request_target` trigger was detected. PR context is present, but fork status was not fully detectable from the current payload."


def _doctor_recommended_fixes(*, workflow: dict[str, Any], checks: list[dict[str, str]]) -> list[str]:
    fixes: list[str] = []
    if not workflow["exists"]:
        fixes.append("Add or restore `.github/workflows/repobrain.yml` from the canonical external install guide.")
    if workflow["dangerous_permissions"]:
        fixes.append("Reduce RepoBrain workflow permissions to the read-mostly external baseline.")
    if not workflow["topocore_secret_referenced"]:
        fixes.append("Wire `TOPOCORE_V6_REPO_TOKEN` into the TopoCore private checkout step.")
    if not _local_path_present():
        fixes.append("Confirm private checkout path propagation so `RB_TOPOCORE_V6_LOCAL_PATH` is available during the run.")
    if any(item["status"] == "FAIL" and item["name"] == "Fork/private boundary" for item in checks):
        fixes.append("Remove `pull_request_target` and keep private tokens away from untrusted fork code.")
    if not fixes:
        fixes.append("No immediate doctor fix is required from the current safe diagnostics.")
    return fixes


def _overall_doctor_status(checks: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    if "PASS" in statuses:
        return "PASS"
    return "UNKNOWN"


def _workflow_snapshot(repo_root: Path) -> dict[str, Any]:
    workflow_path = Path(repo_root) / ".github" / "workflows" / "repobrain.yml"
    exists = workflow_path.exists()
    text = _read_text(workflow_path).lower() if exists else ""
    dangerous_permissions = [
        label for label, pattern in _DANGEROUS_PERMISSION_PATTERNS if re.search(pattern, text)
    ]
    permissions_explicit = "permissions:" in text
    return {
        "path": workflow_path.as_posix(),
        "exists": exists,
        "permissions_explicit": permissions_explicit,
        "dangerous_permissions": dangerous_permissions,
        "uses_pull_request_target": bool(re.search(r"\bpull_request_target\b", text)),
        "uses_private_action": "alexworkingai/repobrain-action@" in text,
        "topocore_secret_referenced": "topocore_v6_repo_token" in text,
        "read_mostly_baseline": permissions_explicit and not dangerous_permissions,
    }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _event_context_label(github_context: dict[str, Any] | None) -> str:
    if github_context and bool(github_context.get("is_pr", False)):
        pr_number = github_context.get("pr_number")
        return f"pull_request #{pr_number}" if pr_number else "pull_request"
    event_name = str((github_context or {}).get("event_name", "") or "").strip()
    issue_number = (github_context or {}).get("issue_number")
    if issue_number:
        return f"{event_name or 'issue_comment'} #{issue_number}"
    return event_name or "unknown"


def _action_runtime_mode() -> str:
    if _running_in_actions():
        event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip() or "unknown"
        return f"github_actions:{event_name}"
    return "local_or_dry_run"


def _topocore_dependency_mode(*, workflow: dict[str, Any]) -> str:
    if _local_path_present():
        return "private_checkout_path_present"
    if workflow["topocore_secret_referenced"]:
        return "private_checkout_configured"
    return "not_detected"


def _running_in_actions() -> bool:
    return str(os.environ.get("GITHUB_ACTIONS", "") or "").strip().lower() == "true"


def _local_path_present() -> bool:
    return bool(str(os.environ.get("RB_TOPOCORE_V6_LOCAL_PATH", "") or "").strip())


def _env_key_present(name: str) -> bool:
    return name in os.environ and bool(str(os.environ.get(name, "") or "").strip())


def _is_fork_pr(github_context: dict[str, Any] | None) -> bool | None:
    if not github_context or not bool(github_context.get("is_pr", False)):
        return None
    if "pr_same_repo" in github_context:
        return not bool(github_context.get("pr_same_repo"))
    head_repo = str(github_context.get("head_repo_full_name", "") or "").strip().lower()
    repo = str(github_context.get("repository", "") or "").strip().lower()
    if head_repo and repo:
        return head_repo != repo
    return None


def _fork_context_known(github_context: dict[str, Any] | None) -> bool:
    return _is_fork_pr(github_context) is not None


def _yes_no(value: bool) -> str:
    return "yes" if bool(value) else "no"
