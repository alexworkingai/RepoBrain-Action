from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_workflow_example_uses_minimal_read_mostly_permissions() -> None:
    text = _read("docs/examples/repobrain_external_pilot_workflow.yml")

    assert "contents: read" in text
    assert "models: read" in text
    assert "issues: write" in text
    assert "pull-requests: read" in text
    assert "checks: read" in text
    assert "statuses: read" in text
    assert "actions: read" in text
    assert "contents: write" not in text
    assert "pull-requests: write" not in text
    assert "checks: write" not in text
    assert "pull_request_target" not in text


def test_external_workflow_example_keeps_no_mutation_flags_and_private_token_reference() -> None:
    text = _read("docs/examples/repobrain_external_pilot_workflow.yml")

    assert 'RB_APPLY_PATCH: "0"' in text
    assert 'RB_CREATE_PR: "0"' in text
    assert "TOPOCORE_V6_REPO_TOKEN" in text
    assert "fork_pr_uses_default_branch_runtime" in text


def test_onboarding_docs_cover_private_action_access_secret_degradation_and_fork_policy() -> None:
    text = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "TOPOCORE_V6_REPO_TOKEN" in text
    assert "must not appear" in text
    assert "Unable to resolve action" in text
    assert "allowed_actions=local_only" in text
    assert "pull_request_target" in text
    assert "untrusted fork" in text
    assert "repobrain-community" in text
    assert "not required" in text
    assert "`v5`" in text
    assert "`lite`" in text


def test_permissions_and_user_docs_do_not_recommend_broad_write_or_fork_secret_exposure() -> None:
    permissions = _read("docs/onboarding/permissions.md")
    guide = _read("docs/USER_GUIDE.md")

    assert "contents: write" in permissions
    assert "not required" in permissions.lower()
    assert "pull_request_target" in permissions
    assert "consumer repository actions policy" in guide.lower() or "external actions" in guide.lower()
    assert "untrusted fork" in guide.lower()
    assert "no patch/autofix" in guide.lower() or "no-patch" in guide.lower()


def test_sprint_74_doc_and_indexes_record_security_hardening() -> None:
    sprint = _read("docs/architecture/SPRINT_74_SECURITY_PERMISSIONS_FORK_SAFETY.md")
    migration = _read("docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md")
    coverage = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md")

    assert "Security Model" in sprint
    assert "Permissions Model" in sprint
    assert "Fork Safety Policy" in sprint
    assert "TOPOCORE_V6_REPO_TOKEN" in sprint
    assert "allowed_actions=local_only" in sprint
    assert "BLOCKED_BY_SAFETY" in sprint
    assert "SECURITY_PERMISSION_FORK_SAFETY_PASSED" in sprint
    assert "no repobrain-community" in sprint
    assert "SPRINT_74_SECURITY_PERMISSIONS_FORK_SAFETY.md" in migration
    assert "tests/test_external_security_permissions_fork_safety.py" in coverage


def test_security_hardening_does_not_reintroduce_v5_community_or_unsafe_verify_fix_claims() -> None:
    verify_doc = _read("docs/architecture/SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md").lower()
    fix_doc = _read("docs/architecture/SPRINT_73_FIX_COMMAND_PRODUCT_PATH.md").lower()

    assert "safe to merge" not in verify_doc
    assert "security approved" not in verify_doc
    assert "patch applied" in fix_doc
    assert "repobrain-community" not in _read("docs/examples/repobrain_external_pilot_workflow.yml")
