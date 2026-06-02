from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "alexworkingai/RepoBrain-Action"
DEFAULT_BRANCH = "main"


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["gh", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _json_api(path: str) -> tuple[str, Any, str | None]:
    code, stdout, stderr = _run_gh(["api", path])
    if code == 0:
        try:
            return "PASS", json.loads(stdout), None
        except json.JSONDecodeError:
            return "UNKNOWN", None, "invalid_json"
    lowered = f"{stdout}\n{stderr}".lower()
    if "403" in lowered or "upgrade to github pro" in lowered or "forbidden" in lowered:
        return "UNKNOWN", None, "api_403_or_plan_limited"
    if "404" in lowered:
        return "UNKNOWN", None, "api_404_or_not_found"
    return "UNKNOWN", None, "api_error"


def _content_exists(repo: str, path: str) -> tuple[str, str]:
    status, payload, reason = _json_api(f"repos/{repo}/contents/{path}")
    if status == "PASS" and isinstance(payload, dict):
        return "present", "ok"
    return "unknown", reason or "not_checked"


def _ruleset_targets_default_branch(ruleset: dict[str, Any], *, default_branch: str) -> bool:
    conditions = ruleset.get("conditions", {})
    if not isinstance(conditions, dict):
        return False
    ref_name = conditions.get("ref_name", {})
    if not isinstance(ref_name, dict):
        return False
    include = ref_name.get("include", [])
    if not isinstance(include, list):
        return False
    normalized = {str(item).strip() for item in include if str(item).strip()}
    if "~DEFAULT_BRANCH" in normalized:
        return True
    branch_patterns = {default_branch, f"refs/heads/{default_branch}"}
    return any(item in branch_patterns for item in normalized)


def _extract_ruleset_flags(ruleset: dict[str, Any]) -> dict[str, str]:
    rules = ruleset.get("rules", [])
    if not isinstance(rules, list):
        rules = []

    flags = {
        "required_pr": "unknown",
        "required_approvals": "unknown",
        "dismiss_stale_approvals": "unknown",
        "conversation_resolution": "unknown",
        "force_push_blocked": "unknown",
        "deletion_restricted": "unknown",
        "required_checks": "unknown",
        "codeowner_review": "unknown",
        "linear_history": "unknown",
    }

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_type = str(rule.get("type", "") or "").strip().lower()
        parameters = rule.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}
        if rule_type == "pull_request":
            flags["required_pr"] = "yes"
            flags["required_approvals"] = str(
                parameters.get("required_approving_review_count", "unknown")
            )
            flags["dismiss_stale_approvals"] = (
                "yes" if bool(parameters.get("dismiss_stale_reviews_on_push", False)) else "no"
            )
            flags["conversation_resolution"] = (
                "yes" if bool(parameters.get("required_review_thread_resolution", False)) else "no"
            )
            flags["codeowner_review"] = (
                "yes" if bool(parameters.get("require_code_owner_review", False)) else "no"
            )
        elif rule_type == "required_status_checks":
            required_checks = parameters.get("required_status_checks", [])
            if isinstance(required_checks, list) and required_checks:
                flags["required_checks"] = "enabled"
            else:
                flags["required_checks"] = "configured_empty"
        elif rule_type == "non_fast_forward":
            flags["force_push_blocked"] = "yes"
        elif rule_type == "deletion":
            flags["deletion_restricted"] = "yes"
        elif rule_type == "required_linear_history":
            flags["linear_history"] = "yes"

    for key in ("force_push_blocked", "deletion_restricted", "linear_history"):
        if flags[key] == "unknown":
            flags[key] = "no"
    if flags["required_pr"] == "unknown":
        flags["required_pr"] = "no"
    if flags["required_checks"] == "unknown":
        flags["required_checks"] = "deferred"
    return flags


def _find_protect_main_ruleset(rulesets: Any, *, default_branch: str) -> dict[str, Any] | None:
    if not isinstance(rulesets, list):
        return None
    matches = [
        item
        for item in rulesets
        if isinstance(item, dict)
        and str(item.get("enforcement", "") or "").strip().lower() == "active"
        and _ruleset_targets_default_branch(item, default_branch=default_branch)
    ]
    if not matches:
        for item in rulesets:
            if not isinstance(item, dict):
                continue
            if str(item.get("name", "") or "").strip().lower() == "protect main":
                return item
        return None
    for item in matches:
        if str(item.get("name", "") or "").strip().lower() == "protect main":
            return item
    return matches[0]


def _admin_bypass_label(ruleset: dict[str, Any]) -> str:
    bypass = ruleset.get("bypass_actors", [])
    if not isinstance(bypass, list):
        return "unknown"
    for actor in bypass:
        if not isinstance(actor, dict):
            continue
        actor_type = str(actor.get("actor_type", "") or "").strip().lower()
        if actor_type == "repositoryrole":
            return "allowed"
    return "restricted"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository governance visibility safely.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repository slug owner/name")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Branch to inspect")
    args = parser.parse_args()

    repo = str(args.repo).strip() or DEFAULT_REPO
    branch = str(args.branch).strip() or DEFAULT_BRANCH

    overall = "PASS"

    repo_status, repo_payload, repo_reason = _json_api(f"repos/{repo}")
    visibility = "unknown"
    default_branch = branch
    if repo_status == "PASS" and isinstance(repo_payload, dict):
        visibility = str(repo_payload.get("visibility") or "unknown").lower()
        default_branch = str(repo_payload.get("default_branch") or branch)
    else:
        overall = "UNKNOWN"

    codeowners_state, codeowners_reason = _content_exists(repo, ".github/CODEOWNERS")
    if codeowners_state != "present" and overall == "PASS":
        overall = "WARN"

    protection_status, _, protection_reason = _json_api(
        f"repos/{repo}/branches/{default_branch}/protection"
    )
    ruleset_status, ruleset_payload, ruleset_reason = _json_api(f"repos/{repo}/rulesets")

    ruleset_count = "unknown"
    main_protection = "unknown"
    protect_main_name = "unknown"
    required_pr = "unknown"
    required_approvals = "unknown"
    dismiss_stale_approvals = "unknown"
    conversation_resolution = "unknown"
    force_push_blocked = "unknown"
    deletion_restricted = "unknown"
    required_checks = "unknown"
    codeowner_review = "unknown"
    linear_history = "unknown"
    admin_bypass = "unknown"

    if ruleset_status == "PASS" and isinstance(ruleset_payload, list):
        ruleset_count = str(len(ruleset_payload))
        detailed_rulesets: list[dict[str, Any]] = []
        for item in ruleset_payload:
            if not isinstance(item, dict):
                continue
            ruleset_id = item.get("id")
            if ruleset_id is None:
                detailed_rulesets.append(item)
                continue
            detail_status, detail_payload, _ = _json_api(f"repos/{repo}/rulesets/{ruleset_id}")
            if detail_status == "PASS" and isinstance(detail_payload, dict):
                detailed_rulesets.append(detail_payload)
            else:
                detailed_rulesets.append(item)
        protect_main_ruleset = _find_protect_main_ruleset(detailed_rulesets, default_branch=default_branch)
        if protect_main_ruleset is not None:
            protect_main_name = str(protect_main_ruleset.get("name", "") or "unknown").strip() or "unknown"
            main_protection = "enabled"
            flags = _extract_ruleset_flags(protect_main_ruleset)
            required_pr = flags["required_pr"]
            required_approvals = flags["required_approvals"]
            dismiss_stale_approvals = flags["dismiss_stale_approvals"]
            conversation_resolution = flags["conversation_resolution"]
            force_push_blocked = flags["force_push_blocked"]
            deletion_restricted = flags["deletion_restricted"]
            required_checks = flags["required_checks"]
            codeowner_review = flags["codeowner_review"]
            linear_history = flags["linear_history"]
            admin_bypass = _admin_bypass_label(protect_main_ruleset)
        else:
            main_protection = "not_detected"
    elif overall == "PASS":
        overall = "UNKNOWN"

    if main_protection == "enabled":
        if required_checks == "deferred":
            overall = "PARTIAL"
        elif overall == "PASS":
            overall = "PASS"
    elif main_protection == "not_detected" and overall == "PASS":
        overall = "WARN"
    elif protection_status != "PASS" and ruleset_status != "PASS" and overall == "PASS":
        overall = "UNKNOWN"

    print(f"REPO={repo}")
    print(f"VISIBILITY={visibility}")
    print(f"DEFAULT_BRANCH={default_branch}")
    print(f"CODEOWNERS={codeowners_state}")
    print(f'BRANCH_PROTECTION={"present" if protection_status == "PASS" else protection_status}')
    print(f'RULESETS={ruleset_count if ruleset_status == "PASS" else ruleset_status}')
    print(f"MAIN_PROTECTION={main_protection}")
    print(f"RULESET_PROTECT_MAIN={protect_main_name}")
    print(f"REQUIRED_PR={required_pr}")
    print(f"REQUIRED_APPROVALS={required_approvals}")
    print(f"DISMISS_STALE_APPROVALS={dismiss_stale_approvals}")
    print(f"CONVERSATION_RESOLUTION={conversation_resolution}")
    print(f"FORCE_PUSH_BLOCKED={force_push_blocked}")
    print(f"DELETION_RESTRICTED={deletion_restricted}")
    print(f"REQUIRED_CHECKS={required_checks}")
    print(f"CODEOWNER_REVIEW={codeowner_review}")
    print(f"LINEAR_HISTORY={linear_history}")
    print(f"ADMIN_BYPASS={admin_bypass}")
    if main_protection == "enabled" and required_checks == "deferred":
        print("GOVERNANCE_BASELINE=PROTECTED_MAIN_BASELINE_ENABLED")
        print("GOVERNANCE_REASON=GOVERNANCE_PARTIAL_REQUIRED_CHECKS_DEFERRED")
    if repo_reason:
        print(f"REPO_REASON={repo_reason}")
    if codeowners_reason and codeowners_reason != "ok":
        print(f"CODEOWNERS_REASON={codeowners_reason}")
    if protection_reason:
        print(f"BRANCH_PROTECTION_REASON={protection_reason}")
    if ruleset_reason:
        print(f"RULESETS_REASON={ruleset_reason}")
    print(f"GOVERNANCE_STATUS={overall}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
