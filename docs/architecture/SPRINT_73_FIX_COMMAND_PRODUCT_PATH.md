# Sprint 73 - Fix Command Product Path

## 1. Purpose

Sprint 73 productizes `/repobrain fix` as a safe proposal/governance path on external PRs.
It follows Sprint 72 verify productionization.
This sprint does not enable patch/autofix.

## 2. Baseline

Baseline before Sprint 73:

- RepoBrain-Action latest main before Sprint 73:
  - `45b4f37 Productionize external verify command`
- Sprint 70 command matrix passed.
- Sprint 71 retrieval quality passed.
- Sprint 72 verify productionization passed.
- fix behavior before Sprint 73:
  - issue scope: scoped unsupported
  - PR scope: conservative `no_patch` output with grounded evidence but thin proposal/governance framing

## 3. Fix Product Semantics

Current fix status model:

- `PROPOSAL_READY`
  - enough PR evidence exists to produce a safe proposal/governance response
  - patch remains unapplied
- `NO_ACTION_NEEDED`
  - no clear useful fix proposal was identified from the available evidence
- `NEEDS_MORE_INFORMATION`
  - the request is too vague or the evidence is too thin for a stronger proposal
- `UNSUPPORTED_SCOPE`
  - issue-only or otherwise unsupported scope
- `BLOCKED_BY_SAFETY`
  - the request asked for mutation behavior that is disabled in the product path
- `ERROR_SANITIZED`
  - unexpected failure was contained without leaking raw stack traces or secrets

No-patch guarantee:

- `patch_authorized=false`
- `patch_applied=false`
- `files_modified=false`
- `branch_created=false`
- `commit_created=false`
- `pr_created=false`

RepoBrain fix output is informational/governance only.
It does not apply patches, create branches, create commits, create PRs, or claim merge/security approval.

## 4. Implementation Summary

Code changes landed in Sprint 73:

- `repobrain/github_flow.py`
  - adds explicit fix-request analysis for unsafe mutation prompts and vague prompts
  - propagates visible no-mutation safety markers into scoped and PR fix audit state
  - hard-stops product-path patch/apply and auto-PR behavior in the live fix route
- `repobrain/output_md.py`
  - adds a top-level `Fix proposal / governance` section
  - renders status, scope, affected files, validation suggestions, and visible safety gates
  - exposes `files_modified`, `branch_created`, `commit_created`, and `pr_created` in runtime evidence
- tests added:
  - `tests/test_fix_command_product_path.py`

## 5. Unit/Static Test Coverage

Sprint 73 coverage now includes:

- proposal/governance section rendering
- visible safety markers:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- blocked unsafe mutation request semantics
- issue-scope scoped unsupported preservation
- no unsafe merge/security/approval wording
- no v5 / no repobrain-community drift
- no patch/autofix activation
- no RepoBrain-created branch/commit/PR behavior in the product fix path

## 6. External Fix Live Results

Issue fix:

- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/19`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26241566122`
- conclusion:
  - `success`
- status:
  - `PASS_SCOPED_UNSUPPORTED`
- scope behavior:
  - issue-only fix remains scoped unsupported and explicitly reports no patch, branch, commit, or PR action
- patch status:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `not_applicable`
  - fallback reason: `unsupported_issue_context`
- safety result:
  - no mutation claim
  - no patch application
  - no branch/commit/PR creation

PR fix normal:

- PR URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/20`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26241605575`
- conclusion:
  - `success`
- status:
  - `PROPOSAL_READY`
- PR metadata used:
  - `yes`
- selected evidence:
  - `2`
- changed files:
  - `docs/repobrain_fix_fixture.md`
  - `docs/repobrain_fix_notes.md`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `v6`
  - fallback used: `no`
  - fallback reason: `none`
- patch status:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- safety result:
  - no actual modification
  - no merge/security/approval claim

PR fix unsafe mutation request:

- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26241654468`
- conclusion:
  - `success`
- status:
  - `BLOCKED_BY_SAFETY`
- patch status:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- safety result:
  - unsafe mutation request was blocked
  - patch/autofix stayed disabled
  - no repo mutation occurred

Optional vague fix:

- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26241695469`
- result:
  - `NEEDS_MORE_INFORMATION`

## 7. Defects / Gaps

Fixed now:

- product-path fix output now shows visible proposal/governance framing instead of a patch-first surface
- no-mutation markers are visible in both scoped and PR fix output
- unsafe mutation prompts are blocked explicitly rather than relying on implicit `no_patch` behavior
- live fix path no longer attempts patch apply or auto-PR side effects

Deferred:

- normal `PROPOSAL_READY` output on a tiny docs-only PR is still somewhat generic in the proposal text
- next step if this becomes product-significant:
  - enrich proposal text from evidence/changed-file context without widening patch behavior

Not defects:

- issue-scope fix remains scoped unsupported by design
- `PROPOSAL_READY` does not mean patch applied or merge approved

## 8. Product Status

- `FIX_PRODUCT_PATH_PASSED`

## 9. Next Step

Recommended next sprint:

- Sprint 74 - Security, Permissions, and Fork Safety

Focus:

- validate external product behavior under tighter permission/fork boundaries
- keep fix/verify/ask safety contracts explicit
- keep private action access, token degradation, and fork policy explicit

## 10. Non-Goals

- no v5
- no repobrain-community
- no patch/autofix
- no production/Marketplace switch
- no RepoBrain-created branch/commit/PR behavior
