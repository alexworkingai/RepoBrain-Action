from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "repobrain_public_cleanup.py"
SPEC = importlib.util.spec_from_file_location("repobrain_public_cleanup", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


@pytest.fixture()
def repo_identity() -> object:
    return MODULE.RepoIdentity(
        repo="alexworkingai/RepoBrain-Action",
        visibility="PUBLIC",
        is_private=False,
        viewer_permission="ADMIN",
        default_branch="main",
    )


@pytest.fixture()
def sample_inventory(repo_identity: object) -> dict[str, object]:
    return {
        "repo": "alexworkingai/RepoBrain-Action",
        "identity": repo_identity,
        "issues": [
            {"number": 1, "title": "Real issue", "state": "OPEN"},
            {"number": 10, "title": "PR issue mirror", "state": "OPEN"},
        ],
        "pull_requests": [
            {"number": 10, "title": "Old sprint PR", "state": "open", "headRefName": "codex/sprint-old", "baseRefName": "main"},
            {"number": 11, "title": "Current final PR", "state": "open", "headRefName": "codex/final-pr-premium-impact-and-public-cleanup", "baseRefName": "main"},
            {"number": 12, "title": "Merged PR", "state": "merged", "headRefName": "codex/merged-old", "baseRefName": "main"},
        ],
        "branches": [
            {"name": "main", "protected": True},
            {"name": "codex/final-pr-premium-impact-and-public-cleanup", "protected": False},
            {"name": "codex/sprint-old", "protected": False},
            {"name": "codex/merged-old", "protected": False},
            {"name": "feature/customer-branch", "protected": False},
        ],
        "labels": [
            {"name": "bug"},
            {"name": "smoke"},
            {"name": "documentation"},
        ],
        "milestones": [{"number": 1, "title": "Test milestone"}],
    }


def test_build_cleanup_plan_preserves_current_branch_and_current_pr_and_filters_pr_like_issues(sample_inventory: dict[str, object]) -> None:
    plan = MODULE._build_cleanup_plan(
        repo=sample_inventory["repo"],
        identity=sample_inventory["identity"],
        issues=sample_inventory["issues"],
        pull_requests=sample_inventory["pull_requests"],
        branches=sample_inventory["branches"],
        labels=sample_inventory["labels"],
        milestones=sample_inventory["milestones"],
        exclude_current_branch="codex/final-pr-premium-impact-and-public-cleanup",
        exclude_pr=None,
    )

    assert [item["number"] for item in plan["issue_delete_candidates"]] == [1]
    assert [item["number"] for item in plan["skipped_pr_like_issues"]] == [10]
    assert [item["number"] for item in plan["close_pr_candidates"]] == [10]
    assert [item["number"] for item in plan["kept_open_prs"]] == [11]
    assert plan["current_final_pr"]["number"] == 11


def test_build_cleanup_plan_never_deletes_main_protected_or_current_branch_and_only_marks_safe_candidates(sample_inventory: dict[str, object]) -> None:
    plan = MODULE._build_cleanup_plan(
        repo=sample_inventory["repo"],
        identity=sample_inventory["identity"],
        issues=sample_inventory["issues"],
        pull_requests=sample_inventory["pull_requests"],
        branches=sample_inventory["branches"],
        labels=sample_inventory["labels"],
        milestones=sample_inventory["milestones"],
        exclude_current_branch="codex/final-pr-premium-impact-and-public-cleanup",
        exclude_pr=None,
    )

    assert {item["name"] for item in plan["branch_delete_candidates"]} == {"codex/sprint-old", "codex/merged-old"}
    skipped = {item["name"]: item["reason"] for item in plan["skipped_branches"]}
    assert skipped["main"] == "protected_or_current"
    assert skipped["codex/final-pr-premium-impact-and-public-cleanup"] == "protected_or_current"
    assert skipped["feature/customer-branch"] == "not_safe_candidate"


def test_verify_repo_identity_blocks_mismatch_and_missing_admin(repo_identity: object) -> None:
    MODULE._verify_repo_identity(repo_identity, expected_repo="alexworkingai/RepoBrain-Action")

    with pytest.raises(MODULE.CleanupBlocked, match="repo mismatch"):
        MODULE._verify_repo_identity(
            MODULE.RepoIdentity(
                repo="alexworkingai/OtherRepo",
                visibility="PUBLIC",
                is_private=False,
                viewer_permission="ADMIN",
                default_branch="main",
            ),
            expected_repo="alexworkingai/RepoBrain-Action",
        )

    with pytest.raises(MODULE.CleanupBlocked, match="viewer permission mismatch"):
        MODULE._verify_repo_identity(
            MODULE.RepoIdentity(
                repo="alexworkingai/RepoBrain-Action",
                visibility="PUBLIC",
                is_private=False,
                viewer_permission="WRITE",
                default_branch="main",
            ),
            expected_repo="alexworkingai/RepoBrain-Action",
        )


def test_backup_path_must_be_outside_repo_and_backup_files_required(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    backup_dir = outside / "cleanup"
    MODULE._ensure_backup_outside_repo(backup_dir, repo_root=tmp_path / "repo")

    with pytest.raises(MODULE.CleanupBlocked, match="outside repo root"):
        MODULE._ensure_backup_outside_repo(tmp_path / "repo" / "nested", repo_root=tmp_path / "repo")

    backup_dir.mkdir()
    with pytest.raises(MODULE.CleanupBlocked, match="Required backup file missing or empty"):
        MODULE._verify_backup_files(backup_dir)


def test_execute_requires_auto_approved_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_inventory: dict[str, object]) -> None:
    monkeypatch.setattr(MODULE, "_run_gh", lambda args: (0, "ok", ""))
    monkeypatch.setattr(
        MODULE,
        "_collect_inventory",
        lambda repo: {
            "repo_metadata": {
                "nameWithOwner": "alexworkingai/RepoBrain-Action",
                "visibility": "PUBLIC",
                "isPrivate": False,
                "viewerPermission": "ADMIN",
                "defaultBranchRef": {"name": "main"},
            },
            "issues": sample_inventory["issues"],
            "pull_requests": sample_inventory["pull_requests"],
            "branches": sample_inventory["branches"],
            "labels": sample_inventory["labels"],
            "milestones": sample_inventory["milestones"],
            "workflows": [],
            "rulesets": [],
            "releases": [],
            "comments": {},
        },
    )
    monkeypatch.setattr(MODULE, "_backup_dir", lambda: tmp_path / "outside-backup")

    args = MODULE.parse_args([
        "--repo",
        "alexworkingai/RepoBrain-Action",
        "--execute",
        "--exclude-current-branch",
        "codex/final-pr-premium-impact-and-public-cleanup",
    ])

    with pytest.raises(MODULE.CleanupBlocked, match="auto-approved-from-operator-prompt"):
        MODULE.run_cleanup(args)


def test_dry_run_creates_manifest_without_destructive_calls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_inventory: dict[str, object]) -> None:
    monkeypatch.setattr(MODULE, "_run_gh", lambda args: (0, "ok", ""))
    monkeypatch.setattr(
        MODULE,
        "_collect_inventory",
        lambda repo: {
            "repo_metadata": {
                "nameWithOwner": "alexworkingai/RepoBrain-Action",
                "visibility": "PUBLIC",
                "isPrivate": False,
                "viewerPermission": "ADMIN",
                "defaultBranchRef": {"name": "main"},
            },
            "issues": sample_inventory["issues"],
            "pull_requests": sample_inventory["pull_requests"],
            "branches": sample_inventory["branches"],
            "labels": sample_inventory["labels"],
            "milestones": sample_inventory["milestones"],
            "workflows": [],
            "rulesets": [],
            "releases": [],
            "comments": {"issue_comments": [], "pull_comments": []},
        },
    )
    monkeypatch.setattr(MODULE, "_backup_dir", lambda: tmp_path / "outside-backup")

    called = {"execute": False}
    monkeypatch.setattr(MODULE, "_execute_cleanup", lambda **kwargs: called.__setitem__("execute", True))

    result = MODULE.main([
        "--repo",
        "alexworkingai/RepoBrain-Action",
        "--dry-run",
        "--exclude-current-branch",
        "codex/final-pr-premium-impact-and-public-cleanup",
    ])

    assert result == 0
    assert called["execute"] is False
    manifest = tmp_path / "outside-backup" / "cleanup_manifest.json"
    dry_run = tmp_path / "outside-backup" / "cleanup_dry_run_report.md"
    assert manifest.exists()
    assert dry_run.exists()


def test_labels_and_milestones_remain_allowlist_or_manual_review(sample_inventory: dict[str, object]) -> None:
    plan = MODULE._build_cleanup_plan(
        repo=sample_inventory["repo"],
        identity=sample_inventory["identity"],
        issues=sample_inventory["issues"],
        pull_requests=sample_inventory["pull_requests"],
        branches=sample_inventory["branches"],
        labels=sample_inventory["labels"],
        milestones=sample_inventory["milestones"],
        exclude_current_branch="codex/final-pr-premium-impact-and-public-cleanup",
        exclude_pr=None,
    )

    assert plan["manual_review_labels"] == [{"name": "smoke", "reason": "allowlist_manual_review_only"}]
    assert plan["manual_review_milestones"] == [{"number": 1, "title": "Test milestone", "reason": "manual_review_only"}]


def test_source_does_not_generate_force_push_or_release_delete_commands() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "--force" not in text
    assert "force-push" in text
    assert "release delete" not in text.lower()
    assert "git push origin --delete" not in text
