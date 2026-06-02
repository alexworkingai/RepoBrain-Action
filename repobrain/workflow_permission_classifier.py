from __future__ import annotations

import re
from typing import Any


SAFE_READ_MOSTLY = "SAFE_READ_MOSTLY"
JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION = "JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION"
WRITE_HEAVY_REVIEW_REQUIRED = "WRITE_HEAVY_REVIEW_REQUIRED"
DANGEROUS_WORKFLOW_POLICY = "DANGEROUS_WORKFLOW_POLICY"

_PERMISSION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("contents: write", r"contents\s*:\s*write"),
    ("checks: write", r"checks\s*:\s*write"),
    ("pull-requests: write", r"pull-requests\s*:\s*write"),
    ("issues: write", r"issues\s*:\s*write"),
    ("actions: write", r"actions\s*:\s*write"),
    ("statuses: write", r"statuses\s*:\s*write"),
    ("deployments: write", r"deployments\s*:\s*write"),
    ("packages: write", r"packages\s*:\s*write"),
    ("security-events: write", r"security-events\s*:\s*write"),
    ("administration: write", r"administration\s*:\s*write"),
)

_DANGEROUS_POLICY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("pull_request_target", r"\bpull_request_target\b"),
    ("contents: write", r"contents\s*:\s*write"),
)

_PR_COMMENT_DOC_PATTERNS: tuple[str, ...] = (
    "pr command response comment",
    "pr command response comments",
    "publish pr command response comments",
    "publish repobrain pr command responses",
    "pr comment response permission",
    "pull-requests: write is for publishing pr command response comments only",
    "pull-requests: write is only for pr command response comments",
)

_NO_MUTATION_DOC_PATTERNS: tuple[str, ...] = (
    "no patch/autofix",
    "no patch",
    "no repobrain-created branch/commit/pr",
    "no branch/commit/pr created by repobrain",
    "does not create branches",
    "does not create commits",
    "does not create prs",
    "proposal/governance only",
)


def classify_workflow_permission_policy(
    *,
    workflow_text: str,
    docs_text: str = "",
) -> dict[str, Any]:
    workflow_lower = str(workflow_text or "").lower()
    docs_lower = str(docs_text or "").lower()
    permissions = sorted(
        permission
        for permission, pattern in _PERMISSION_PATTERNS
        if re.search(pattern, workflow_lower)
    )
    dangerous_policy_signals = sorted(
        signal
        for signal, pattern in _DANGEROUS_POLICY_PATTERNS
        if re.search(pattern, workflow_lower)
    )
    permissions_explicit = "permissions:" in workflow_lower
    uses_repo_brain = "alexworkingai/repobrain-action@" in workflow_lower
    issues_write = "issues: write" in permissions
    pr_write = "pull-requests: write" in permissions
    checks_write = "checks: write" in permissions
    contents_write = "contents: write" in permissions
    uses_pull_request_target = "pull_request_target" in dangerous_policy_signals
    purpose_documented = any(pattern in docs_lower for pattern in _PR_COMMENT_DOC_PATTERNS) or (
        "pr command response" in workflow_lower or "publish pr command response" in workflow_lower
    )
    mutation_policy_documented = any(pattern in docs_lower for pattern in _NO_MUTATION_DOC_PATTERNS)
    no_mutation_policy_active = mutation_policy_documented or uses_repo_brain

    justified_pr_comment_permission = (
        pr_write
        and issues_write
        and not contents_write
        and not checks_write
        and not uses_pull_request_target
        and no_mutation_policy_active
        and (purpose_documented or uses_repo_brain)
    )

    write_heavy_permissions = sorted(
        permission
        for permission in permissions
        if permission in {
            "contents: write",
            "checks: write",
            "pull-requests: write",
            "actions: write",
            "statuses: write",
            "deployments: write",
            "packages: write",
            "security-events: write",
            "administration: write",
        }
    )
    if justified_pr_comment_permission and "pull-requests: write" in write_heavy_permissions:
        write_heavy_permissions.remove("pull-requests: write")

    if uses_pull_request_target or contents_write:
        classification = DANGEROUS_WORKFLOW_POLICY
    elif justified_pr_comment_permission:
        classification = JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION
    elif write_heavy_permissions:
        classification = WRITE_HEAVY_REVIEW_REQUIRED
    else:
        classification = SAFE_READ_MOSTLY

    effective_risky_permissions = sorted(
        signal
        for signal in {*dangerous_policy_signals, *write_heavy_permissions}
        if signal != "pull_request_target" or classification == DANGEROUS_WORKFLOW_POLICY
    )

    if classification == JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION:
        rationale = (
            "`pull-requests: write` appears constrained to RepoBrain PR command response comments. "
            "No `contents: write`, no `checks: write`, no `pull_request_target`, and no mutation-capable RepoBrain path were detected."
        )
        monitor_note = "Document and monitor PR comment response permission."
    elif classification == SAFE_READ_MOSTLY:
        rationale = "Workflow permissions remain read-mostly and no dangerous trigger baseline was detected."
        monitor_note = "Keep workflow permissions explicit and read-mostly."
    elif classification == DANGEROUS_WORKFLOW_POLICY:
        rationale = (
            "Workflow includes dangerous trigger or mutation-capable permission posture "
            f"({', '.join(f'`{item}`' for item in effective_risky_permissions or dangerous_policy_signals)})."
        )
        monitor_note = "Reduce dangerous triggers and write-heavy permissions before wider rollout."
    else:
        rationale = (
            "Workflow uses write permissions that need explicit justification and review: "
            + ", ".join(f"`{item}`" for item in write_heavy_permissions)
            + "."
        )
        monitor_note = "Review whether write permissions are strictly required and document them."

    return {
        "classification": classification,
        "permissions_explicit": permissions_explicit,
        "permissions": permissions,
        "dangerous_policy_signals": dangerous_policy_signals,
        "effective_risky_permissions": effective_risky_permissions,
        "write_heavy_permissions": write_heavy_permissions,
        "justified_pr_comment_permission": justified_pr_comment_permission,
        "purpose_documented": purpose_documented,
        "mutation_policy_documented": mutation_policy_documented,
        "no_mutation_policy_active": no_mutation_policy_active,
        "uses_pull_request_target": uses_pull_request_target,
        "uses_repo_brain": uses_repo_brain,
        "rationale": rationale,
        "monitor_note": monitor_note,
    }
