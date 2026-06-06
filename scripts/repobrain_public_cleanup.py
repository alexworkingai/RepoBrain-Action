from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "alexworkingai/RepoBrain-Action"
DEFAULT_BRANCH = "main"
DEFAULT_EXCLUDE_BRANCH = "codex/final-pr-premium-impact-and-public-cleanup"
CLEANUP_COMMENT = (
    "Closing obsolete internal development/test PR during public repository cleanup before "
    "selected partner/public use. No product signal, release approval, or security decision is implied."
)
SAFE_LABEL_ALLOWLIST = {"smoke", "test", "sprint-fixture", "temporary", "internal-validation"}
PRESERVE_LABELS = {"bug", "enhancement", "documentation", "security", "good first issue", "help wanted"}
BRANCH_CANDIDATE_PATTERNS = (
    r"^codex/sprint-",
    r"^codex/.+test",
    r"^smoke/",
    r"^test/",
    r"^temp/",
    r"^temporary/",
    r"^sprint-",
)
REQUIRED_BACKUP_FILES = (
    "repo_metadata.json",
    "issues_backup.json",
    "pull_requests_backup.json",
    "comments_backup.json",
    "branches_backup.json",
    "labels_backup.json",
    "milestones_backup.json",
    "workflows_backup.json",
    "rulesets_backup.json",
    "releases_backup.json",
    "cleanup_manifest.json",
    "cleanup_manifest.md",
    "cleanup_dry_run_report.md",
)


class CleanupBlocked(RuntimeError):
    """Raised when a hard cleanup safety gate fails."""


@dataclass(frozen=True)
class RepoIdentity:
    repo: str
    visibility: str
    is_private: bool
    viewer_permission: str
    default_branch: str


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["gh", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.returncode, (completed.stdout or "").strip(), (completed.stderr or "").strip()


def _run_gh_json(args: list[str], *, allow_failure: bool = False) -> Any:
    code, stdout, stderr = _run_gh(args)
    if code != 0:
        if allow_failure:
            return None
        raise CleanupBlocked(f"GitHub CLI command failed: gh {' '.join(args)} :: {(stderr or stdout).strip()}")
    if not stdout:
        if allow_failure:
            return None
        raise CleanupBlocked(f"GitHub CLI command returned no JSON: gh {' '.join(args)}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        if allow_failure:
            return None
        raise CleanupBlocked(f"Invalid JSON from gh {' '.join(args)}: {exc}") from exc


def _flatten_paginated(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        flattened: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, list):
                flattened.extend(sub for sub in item if isinstance(sub, dict))
            elif isinstance(item, dict):
                flattened.append(item)
        return flattened
    return []


def _gh_paginated_json(path: str, *, allow_failure: bool = False) -> list[dict[str, Any]]:
    payload = _run_gh_json(["api", "--paginate", "--slurp", path], allow_failure=allow_failure)
    return _flatten_paginated(payload)


def _repo_identity_from_payload(repo: str, payload: dict[str, Any]) -> RepoIdentity:
    default_branch_ref = payload.get("defaultBranchRef") or {}
    default_branch_name = ""
    if isinstance(default_branch_ref, dict):
        default_branch_name = str(default_branch_ref.get("name") or "").strip()
    return RepoIdentity(
        repo=str(payload.get("nameWithOwner") or repo).strip(),
        visibility=str(payload.get("visibility") or "unknown").strip().upper(),
        is_private=bool(payload.get("isPrivate", False)),
        viewer_permission=str(payload.get("viewerPermission") or "UNKNOWN").strip().upper(),
        default_branch=default_branch_name or DEFAULT_BRANCH,
    )


def _verify_repo_identity(identity: RepoIdentity, *, expected_repo: str) -> None:
    problems: list[str] = []
    if identity.repo != expected_repo:
        problems.append(f"repo mismatch: expected {expected_repo}, got {identity.repo}")
    if identity.visibility != "PUBLIC":
        problems.append(f"visibility mismatch: expected PUBLIC, got {identity.visibility}")
    if identity.default_branch != DEFAULT_BRANCH:
        problems.append(f"default branch mismatch: expected {DEFAULT_BRANCH}, got {identity.default_branch}")
    if identity.viewer_permission != "ADMIN":
        problems.append(f"viewer permission mismatch: expected ADMIN, got {identity.viewer_permission}")
    if problems:
        raise CleanupBlocked("; ".join(problems))


def _backup_dir(base_dir: Path | None = None, *, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    root = (base_dir or ROOT.parent).resolve()
    return root / f"repobrain-action-public-cleanup-backup-{stamp}"


def _ensure_backup_outside_repo(backup_dir: Path, repo_root: Path = ROOT) -> None:
    backup_resolved = backup_dir.resolve()
    repo_resolved = repo_root.resolve()
    try:
        backup_resolved.relative_to(repo_resolved)
    except ValueError:
        return
    raise CleanupBlocked(f"Backup directory must be outside repo root: {backup_resolved}")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(str(text), encoding="utf-8")


def _branch_is_candidate(name: str) -> bool:
    lowered = str(name or "").strip().lower()
    return any(re.match(pattern, lowered) for pattern in BRANCH_CANDIDATE_PATTERNS)


def _issue_is_pr_like(issue: dict[str, Any], pr_numbers: set[int]) -> bool:
    number = int(issue.get("number", 0) or 0)
    if number in pr_numbers:
        return True
    return isinstance(issue.get("pull_request"), dict)


def _build_cleanup_plan(
    *,
    repo: str,
    identity: RepoIdentity,
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    branches: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    milestones: list[dict[str, Any]],
    exclude_current_branch: str,
    exclude_pr: int | None,
) -> dict[str, Any]:
    pr_numbers = {int(item.get("number", 0) or 0) for item in pull_requests if int(item.get("number", 0) or 0) > 0}
    current_final_pr: dict[str, Any] | None = None
    issue_delete_candidates: list[dict[str, Any]] = []
    skipped_pr_like_issues: list[dict[str, Any]] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        if _issue_is_pr_like(issue, pr_numbers):
            skipped_pr_like_issues.append(issue)
            continue
        issue_delete_candidates.append(issue)

    open_prs = [
        pr for pr in pull_requests if isinstance(pr, dict) and str(pr.get("state") or "").strip().lower() == "open"
    ]
    plan_historical = [
        pr for pr in pull_requests if isinstance(pr, dict) and str(pr.get("state") or "").strip().lower() != "open"
    ]
    close_pr_candidates: list[dict[str, Any]] = []
    kept_open_prs: list[dict[str, Any]] = []
    for pr in open_prs:
        pr_number = int(pr.get("number", 0) or 0)
        head_ref = str(pr.get("headRefName") or "").strip()
        if exclude_pr is not None and pr_number == exclude_pr:
            current_final_pr = pr
            kept_open_prs.append(pr)
            continue
        if head_ref == exclude_current_branch:
            current_final_pr = pr
            kept_open_prs.append(pr)
            continue
        close_pr_candidates.append(pr)

    protected_branch_names = {
        str(branch.get("name") or "").strip()
        for branch in branches
        if isinstance(branch, dict) and bool(branch.get("protected", False))
    }
    protected_branch_names.update({identity.default_branch, DEFAULT_BRANCH, exclude_current_branch})

    remaining_open_pr_heads = {
        str(pr.get("headRefName") or "").strip()
        for pr in kept_open_prs
        if str(pr.get("headRefName") or "").strip()
    }
    close_candidate_heads = {
        str(pr.get("headRefName") or "").strip()
        for pr in close_pr_candidates
        if str(pr.get("headRefName") or "").strip()
    }
    historical_pr_heads = {
        str(pr.get("headRefName") or "").strip()
        for pr in plan_historical
        if str(pr.get("headRefName") or "").strip()
    }

    branch_delete_candidates: list[dict[str, Any]] = []
    skipped_branches: list[dict[str, Any]] = []
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        name = str(branch.get("name") or "").strip()
        if not name:
            continue
        reason = None
        if name in protected_branch_names:
            reason = "protected_or_current"
        elif name in remaining_open_pr_heads:
            reason = "used_by_kept_open_pr"
        elif not _branch_is_candidate(name) and name not in close_candidate_heads and name not in historical_pr_heads:
            reason = "not_safe_candidate"
        if reason is not None:
            skipped_branches.append({"name": name, "reason": reason})
            continue
        branch_delete_candidates.append({"name": name})

    manual_review_labels: list[dict[str, Any]] = []
    for label in labels:
        if not isinstance(label, dict):
            continue
        name = str(label.get("name") or "").strip()
        if not name:
            continue
        lowered = name.lower()
        if lowered in PRESERVE_LABELS:
            continue
        if lowered in SAFE_LABEL_ALLOWLIST:
            manual_review_labels.append({"name": name, "reason": "allowlist_manual_review_only"})

    manual_review_milestones = [
        {"number": milestone.get("number"), "title": milestone.get("title"), "reason": "manual_review_only"}
        for milestone in milestones
        if isinstance(milestone, dict)
    ]

    plan = {
        "repo": repo,
        "identity": {
            "repo": identity.repo,
            "visibility": identity.visibility,
            "viewer_permission": identity.viewer_permission,
            "default_branch": identity.default_branch,
        },
        "exclude_current_branch": exclude_current_branch,
        "exclude_pr": exclude_pr,
        "current_final_pr": current_final_pr,
        "issue_delete_candidates": issue_delete_candidates,
        "skipped_pr_like_issues": skipped_pr_like_issues,
        "close_pr_candidates": close_pr_candidates,
        "kept_open_prs": kept_open_prs,
        "branch_delete_candidates": branch_delete_candidates,
        "skipped_branches": skipped_branches,
        "manual_review_labels": manual_review_labels,
        "manual_review_milestones": manual_review_milestones,
        "historical_closed_or_merged_prs": plan_historical,
    }
    return plan


def _manifest_summary(plan: dict[str, Any]) -> dict[str, Any]:
    current_final_pr = plan.get("current_final_pr") or {}
    return {
        "repo": plan.get("repo"),
        "identity": plan.get("identity"),
        "exclude_current_branch": plan.get("exclude_current_branch"),
        "exclude_pr": plan.get("exclude_pr"),
        "current_final_pr_number": current_final_pr.get("number"),
        "current_final_pr_branch": current_final_pr.get("headRefName") or plan.get("exclude_current_branch"),
        "issue_delete_candidate_count": len(plan.get("issue_delete_candidates", [])),
        "skipped_pr_like_issue_count": len(plan.get("skipped_pr_like_issues", [])),
        "close_pr_candidate_count": len(plan.get("close_pr_candidates", [])),
        "kept_open_pr_count": len(plan.get("kept_open_prs", [])),
        "branch_delete_candidate_count": len(plan.get("branch_delete_candidates", [])),
        "manual_review_label_count": len(plan.get("manual_review_labels", [])),
        "manual_review_milestone_count": len(plan.get("manual_review_milestones", [])),
    }


def _render_manifest_markdown(plan: dict[str, Any]) -> str:
    summary = _manifest_summary(plan)
    lines = [
        "# RepoBrain Public Cleanup Manifest",
        "",
        f"- Repo: `{summary['repo']}`",
        f"- Visibility: `{summary['identity']['visibility']}`",
        f"- Viewer permission: `{summary['identity']['viewer_permission']}`",
        f"- Default branch: `{summary['identity']['default_branch']}`",
        f"- Excluded current branch: `{summary['exclude_current_branch']}`",
        f"- Excluded current PR: `{summary['current_final_pr_number'] or 'not_open_yet'}`",
        f"- True issues to delete: `{summary['issue_delete_candidate_count']}`",
        f"- PR-like issues skipped: `{summary['skipped_pr_like_issue_count']}`",
        f"- Open PRs to close: `{summary['close_pr_candidate_count']}`",
        f"- Branches to delete: `{summary['branch_delete_candidate_count']}`",
        f"- Labels for manual review only: `{summary['manual_review_label_count']}`",
        f"- Milestones for manual review only: `{summary['manual_review_milestone_count']}`",
        "",
        "Historical PR records are preserved. GitHub pull requests are closed, not deleted, during safe public cleanup.",
    ]
    return "\n".join(lines)


def _render_dry_run_report(plan: dict[str, Any], backup_dir: Path) -> str:
    summary = _manifest_summary(plan)
    return "\n".join(
        [
            "# RepoBrain Public Cleanup Dry Run",
            "",
            f"- Repo confirmed: `{summary['repo']}`",
            f"- ADMIN confirmed: `{summary['identity']['viewer_permission'] == 'ADMIN'}`",
            f"- Backup location: `{backup_dir}`",
            f"- Issues planned for deletion: `{summary['issue_delete_candidate_count']}`",
            f"- PR-like issue records skipped: `{summary['skipped_pr_like_issue_count']}`",
            f"- Open PRs planned for close: `{summary['close_pr_candidate_count']}`",
            f"- Safe stale branches planned for deletion: `{summary['branch_delete_candidate_count']}`",
            f"- Current final branch preserved: `{summary['exclude_current_branch']}`",
            f"- Current final PR preserved: `{summary['current_final_pr_number'] or 'not_open_yet'}`",
            "- Labels and milestones: manual review only in this run.",
            "- Future manual runs should require an explicit confirmation flag or environment confirmation gate.",
        ]
    )


def _backup_file_map(backup_dir: Path) -> dict[str, Path]:
    return {name: backup_dir / name for name in REQUIRED_BACKUP_FILES}


def _verify_backup_files(backup_dir: Path) -> None:
    for name, path in _backup_file_map(backup_dir).items():
        if not path.exists() or path.stat().st_size == 0:
            raise CleanupBlocked(f"Required backup file missing or empty: {name}")


def _create_backup(
    *,
    backup_dir: Path,
    repo_metadata: dict[str, Any],
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    comments: dict[str, Any],
    branches: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    milestones: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
    rulesets: list[dict[str, Any]],
    releases: list[dict[str, Any]],
    plan: dict[str, Any],
) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    _ensure_backup_outside_repo(backup_dir)
    _write_json(backup_dir / "repo_metadata.json", repo_metadata)
    _write_json(backup_dir / "issues_backup.json", issues)
    _write_json(backup_dir / "pull_requests_backup.json", pull_requests)
    _write_json(backup_dir / "comments_backup.json", comments)
    _write_json(backup_dir / "branches_backup.json", branches)
    _write_json(backup_dir / "labels_backup.json", labels)
    _write_json(backup_dir / "milestones_backup.json", milestones)
    _write_json(backup_dir / "workflows_backup.json", workflows)
    _write_json(backup_dir / "rulesets_backup.json", rulesets)
    _write_json(backup_dir / "releases_backup.json", releases)
    _write_json(backup_dir / "cleanup_manifest.json", _manifest_summary(plan))
    _write_text(backup_dir / "cleanup_manifest.md", _render_manifest_markdown(plan))
    _write_text(backup_dir / "cleanup_dry_run_report.md", _render_dry_run_report(plan, backup_dir))


def _delete_issue(repo: str, issue_number: int) -> None:
    code, stdout, stderr = _run_gh(["issue", "delete", str(issue_number), "--repo", repo, "--yes"])
    if code == 0:
        return
    detail = (stderr or stdout).strip().lower()
    if "unknown flag" in detail or "usage:" in detail or "not a valid subcommand" in detail:
        payload = _run_gh_json(["api", f"repos/{repo}/issues/{issue_number}"], allow_failure=False)
        node_id = str((payload or {}).get("node_id") or "").strip()
        if not node_id:
            raise CleanupBlocked(f"Issue delete fallback failed: node_id unavailable for issue {issue_number}")
        mutation = "mutation($id:ID!){deleteIssue(input:{issueId:$id}){clientMutationId}}"
        code2, stdout2, stderr2 = _run_gh([
            "api",
            "graphql",
            "-f",
            f"query={mutation}",
            "-F",
            f"id={node_id}",
        ])
        if code2 == 0:
            return
        raise CleanupBlocked(f"Issue delete fallback failed for issue {issue_number}: {(stderr2 or stdout2).strip()}")
    raise CleanupBlocked(f"Issue delete failed for issue {issue_number}: {(stderr or stdout).strip()}")


def _close_pull_request(repo: str, pr_number: int) -> None:
    code, stdout, stderr = _run_gh(["pr", "comment", str(pr_number), "--repo", repo, "--body", CLEANUP_COMMENT])
    if code != 0:
        raise CleanupBlocked(f"PR comment failed for PR {pr_number}: {(stderr or stdout).strip()}")
    code, stdout, stderr = _run_gh(["pr", "close", str(pr_number), "--repo", repo])
    if code != 0:
        raise CleanupBlocked(f"PR close failed for PR {pr_number}: {(stderr or stdout).strip()}")


def _delete_branch(repo: str, branch_name: str) -> None:
    code, stdout, stderr = _run_gh(["api", "-X", "DELETE", f"repos/{repo}/git/refs/heads/{branch_name}"])
    if code != 0:
        raise CleanupBlocked(f"Branch delete failed for {branch_name}: {(stderr or stdout).strip()}")


def _collect_inventory(repo: str) -> dict[str, Any]:
    repo_metadata = _run_gh_json(
        [
            "repo",
            "view",
            repo,
            "--json",
            "nameWithOwner,visibility,isPrivate,viewerPermission,defaultBranchRef,description,homepageUrl",
        ]
    )
    issues = _run_gh_json(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,state,author,createdAt,updatedAt,closedAt,labels,milestone,assignees,url",
        ]
    )
    pull_requests = _run_gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,state,author,createdAt,updatedAt,closedAt,mergedAt,headRefName,baseRefName,isDraft,labels,milestone,assignees,url",
        ]
    )
    branches = _gh_paginated_json(f"repos/{repo}/branches?per_page=100")
    labels = _gh_paginated_json(f"repos/{repo}/labels?per_page=100")
    milestones = _gh_paginated_json(f"repos/{repo}/milestones?state=all&per_page=100", allow_failure=True)
    workflows_payload = _run_gh_json(["api", f"repos/{repo}/actions/workflows"], allow_failure=True)
    workflows = []
    if isinstance(workflows_payload, dict):
        raw_workflows = workflows_payload.get("workflows", [])
        workflows = [item for item in raw_workflows if isinstance(item, dict)] if isinstance(raw_workflows, list) else []
    rulesets = _gh_paginated_json(f"repos/{repo}/rulesets?per_page=100", allow_failure=True)
    releases = _run_gh_json(
        [
            "release",
            "list",
            "--repo",
            repo,
            "--limit",
            "100",
            "--json",
            "tagName,name,isDraft,isPrerelease,createdAt,publishedAt,url",
        ],
        allow_failure=True,
    )
    issue_comments = _gh_paginated_json(f"repos/{repo}/issues/comments?per_page=100", allow_failure=True)
    pull_comments = _gh_paginated_json(f"repos/{repo}/pulls/comments?per_page=100", allow_failure=True)
    return {
        "repo_metadata": repo_metadata,
        "issues": issues if isinstance(issues, list) else [],
        "pull_requests": pull_requests if isinstance(pull_requests, list) else [],
        "branches": branches,
        "labels": labels,
        "milestones": milestones,
        "workflows": workflows,
        "rulesets": rulesets,
        "releases": releases if isinstance(releases, list) else [],
        "comments": {
            "issue_comments": issue_comments,
            "pull_comments": pull_comments,
        },
    }


def _execute_cleanup(
    *,
    repo: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    deleted_issue_count = 0
    failed_issue_count = 0
    closed_pr_count = 0
    deleted_branch_count = 0
    issue_failures: list[dict[str, Any]] = []
    pr_failures: list[dict[str, Any]] = []
    branch_failures: list[dict[str, Any]] = []

    for issue in plan.get("issue_delete_candidates", []):
        number = int(issue.get("number", 0) or 0)
        try:
            _delete_issue(repo, number)
            deleted_issue_count += 1
        except CleanupBlocked as exc:
            failed_issue_count += 1
            issue_failures.append({"number": number, "reason": str(exc)})

    for pr in plan.get("close_pr_candidates", []):
        number = int(pr.get("number", 0) or 0)
        try:
            _close_pull_request(repo, number)
            closed_pr_count += 1
        except CleanupBlocked as exc:
            pr_failures.append({"number": number, "reason": str(exc)})

    for branch in plan.get("branch_delete_candidates", []):
        name = str(branch.get("name") or "").strip()
        try:
            _delete_branch(repo, name)
            deleted_branch_count += 1
        except CleanupBlocked as exc:
            branch_failures.append({"name": name, "reason": str(exc)})

    return {
        "deleted_issue_count": deleted_issue_count,
        "failed_issue_count": failed_issue_count,
        "closed_pr_count": closed_pr_count,
        "deleted_branch_count": deleted_branch_count,
        "issue_failures": issue_failures,
        "pr_failures": pr_failures,
        "branch_failures": branch_failures,
        "manual_review_label_count": len(plan.get("manual_review_labels", [])),
        "manual_review_milestone_count": len(plan.get("manual_review_milestones", [])),
    }


def _render_execution_report(
    *,
    backup_dir: Path,
    plan: dict[str, Any],
    execution: dict[str, Any],
    remaining_inventory: dict[str, Any],
) -> str:
    current_final_pr = plan.get("current_final_pr") or {}
    remaining_open_prs = [
        pr for pr in remaining_inventory.get("pull_requests", []) if str(pr.get("state") or "").strip().lower() == "open"
    ]
    remaining_issue_count = len(remaining_inventory.get("issues", []))
    lines = [
        "# RepoBrain Public Cleanup Execution Report",
        "",
        f"1. Repo confirmed: {plan.get('repo')}",
        "2. Permissions: ADMIN confirmed",
        f"3. Backup location: {backup_dir}",
        f"4. Issues: deleted={execution.get('deleted_issue_count', 0)}, failed={execution.get('failed_issue_count', 0)}, skipped_pr_like={len(plan.get('skipped_pr_like_issues', []))}",
        (
            "5. PRs: "
            f"closed_obsolete_open={execution.get('closed_pr_count', 0)}, "
            f"kept_current_final_pr={current_final_pr.get('number') or 'not_open_yet'} / {current_final_pr.get('headRefName') or plan.get('exclude_current_branch')}, "
            f"historical_retained={len(plan.get('historical_closed_or_merged_prs', []))}"
        ),
        (
            "6. Branches: "
            f"deleted_stale={execution.get('deleted_branch_count', 0)}, "
            f"skipped_protected_or_current={sum(1 for item in plan.get('skipped_branches', []) if item.get('reason') == 'protected_or_current')}"
        ),
        (
            "7. Labels/milestones: "
            f"cleaned=0, manual_review_labels={execution.get('manual_review_label_count', 0)}, "
            f"manual_review_milestones={execution.get('manual_review_milestone_count', 0)}"
        ),
        "8. Safety: no force-push, no main deletion, no protected branch deletion, no tags/releases deleted, no workflow/ruleset removal, no source-history rewrite",
        f"9. Remaining public items: issues={remaining_issue_count}, open_prs={len(remaining_open_prs)}",
        "10. Recommended next step: merge final PR, run final live retest, then partner onboarding / public metadata polish.",
        "",
        "GitHub pull requests are historical repository records and cannot be safely deleted like normal issues. The safe cleanup path is to close obsolete PRs, delete stale head branches, remove test-only labels/milestones/comments where allowed, and keep a private cleanup manifest.",
    ]
    if remaining_open_prs:
        lines.extend(["", "## Remaining open PRs"])
        for pr in remaining_open_prs:
            lines.append(f"- #{pr.get('number')}: {pr.get('title')} ({pr.get('headRefName')})")
    return "\n".join(lines)


def run_cleanup(args: argparse.Namespace) -> int:
    repo = str(args.repo or DEFAULT_REPO).strip() or DEFAULT_REPO
    exclude_current_branch = str(args.exclude_current_branch or DEFAULT_EXCLUDE_BRANCH).strip() or DEFAULT_EXCLUDE_BRANCH
    exclude_pr = int(args.exclude_pr) if args.exclude_pr is not None else None

    auth_code, _, auth_err = _run_gh(["auth", "status"])
    if auth_code != 0:
        raise CleanupBlocked(f"GitHub auth missing or invalid: {auth_err.strip()}")

    inventory = _collect_inventory(repo)
    identity = _repo_identity_from_payload(repo, inventory["repo_metadata"])
    _verify_repo_identity(identity, expected_repo=repo)

    plan = _build_cleanup_plan(
        repo=repo,
        identity=identity,
        issues=inventory["issues"],
        pull_requests=inventory["pull_requests"],
        branches=inventory["branches"],
        labels=inventory["labels"],
        milestones=inventory["milestones"],
        exclude_current_branch=exclude_current_branch,
        exclude_pr=exclude_pr,
    )

    backup_dir = _backup_dir()
    _create_backup(
        backup_dir=backup_dir,
        repo_metadata=inventory["repo_metadata"],
        issues=inventory["issues"],
        pull_requests=inventory["pull_requests"],
        comments=inventory["comments"],
        branches=inventory["branches"],
        labels=inventory["labels"],
        milestones=inventory["milestones"],
        workflows=inventory["workflows"],
        rulesets=inventory["rulesets"],
        releases=inventory["releases"],
        plan=plan,
    )
    _verify_backup_files(backup_dir)

    if args.dry_run and not args.execute:
        print(_render_dry_run_report(plan, backup_dir))
        return 0

    if not args.execute:
        raise CleanupBlocked("Choose either --dry-run or --execute.")
    if not args.auto_approved_from_operator_prompt:
        raise CleanupBlocked("Execution requires --auto-approved-from-operator-prompt for this script.")

    execution = _execute_cleanup(repo=repo, plan=plan)
    remaining_inventory = _collect_inventory(repo)
    execution_report = _render_execution_report(
        backup_dir=backup_dir,
        plan=plan,
        execution=execution,
        remaining_inventory=remaining_inventory,
    )
    _write_text(backup_dir / "cleanup_execution_report.md", execution_report)
    print(execution_report)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely clean obsolete public RepoBrain repository surface after backup and verification.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repository slug owner/name")
    parser.add_argument("--dry-run", action="store_true", help="Generate backup and manifest without destructive actions.")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup after backup and safety checks.")
    parser.add_argument(
        "--auto-approved-from-operator-prompt",
        action="store_true",
        help="Allow destructive execution only when the operator authorization is embedded in the controlling prompt.",
    )
    parser.add_argument(
        "--exclude-current-branch",
        default=DEFAULT_EXCLUDE_BRANCH,
        help="Branch name that must never be deleted or associated PR closed.",
    )
    parser.add_argument("--exclude-pr", type=int, default=None, help="PR number that must never be closed.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run_cleanup(args)
    except CleanupBlocked as exc:
        print(f"PUBLIC_CLEANUP_BLOCKED={exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
