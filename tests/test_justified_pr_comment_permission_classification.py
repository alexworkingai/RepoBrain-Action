from __future__ import annotations

from repobrain.workflow_permission_classifier import (
    DANGEROUS_WORKFLOW_POLICY,
    JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION,
    SAFE_READ_MOSTLY,
    WRITE_HEAVY_REVIEW_REQUIRED,
    classify_workflow_permission_policy,
)


def test_safe_read_mostly_classification_remains_safe() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text=(
            "name: repobrain\n"
            "permissions:\n"
            "  contents: read\n"
            "  issues: write\n"
            "  pull-requests: read\n"
            "  checks: read\n"
        ),
        docs_text="read-mostly workflow permissions only",
    )

    assert policy["classification"] == SAFE_READ_MOSTLY


def test_pull_requests_write_can_be_justified_for_pr_comment_responses() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text=(
            "name: repobrain\n"
            "on:\n"
            "  issue_comment:\n"
            "permissions:\n"
            "  contents: read\n"
            "  issues: write\n"
            "  pull-requests: write\n"
            "  checks: read\n"
            "jobs:\n"
            "  qa:\n"
            "    steps:\n"
            "      - uses: alexworkingai/RepoBrain-Action@main\n"
        ),
        docs_text=(
            "pull-requests: write is only for PR command response comments. "
            "no patch/autofix. no branch/commit/pr created by RepoBrain."
        ),
    )

    assert policy["classification"] == JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION
    assert policy["justified_pr_comment_permission"] is True
    assert policy["effective_risky_permissions"] == []


def test_contents_write_remains_dangerous() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text="permissions:\n  contents: write\n  issues: write\n  pull-requests: write\n",
        docs_text="pull-requests: write is only for PR command response comments",
    )

    assert policy["classification"] == DANGEROUS_WORKFLOW_POLICY


def test_checks_write_without_justification_stays_review_required() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text="permissions:\n  contents: read\n  checks: write\n  issues: write\n",
        docs_text="read-mostly workflow permissions",
    )

    assert policy["classification"] == WRITE_HEAVY_REVIEW_REQUIRED


def test_pull_request_target_remains_dangerous() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text="on:\n  pull_request_target:\npermissions:\n  contents: read\n",
        docs_text="",
    )

    assert policy["classification"] == DANGEROUS_WORKFLOW_POLICY


def test_missing_documentation_without_product_constraint_stays_review_required() -> None:
    policy = classify_workflow_permission_policy(
        workflow_text="permissions:\n  contents: read\n  issues: write\n  pull-requests: write\n",
        docs_text="generic workflow docs only",
    )

    assert policy["classification"] == WRITE_HEAVY_REVIEW_REQUIRED
