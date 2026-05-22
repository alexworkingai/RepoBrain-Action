# External Repository Pilot Install

## Purpose

This document defines the direct external repository pilot install path after Sprint 68 v6-only closeout and Sprint 69 product transition.

## Supported Architecture

Current supported install shape:

- `topocore`: private TopoCore v6 repository
- `RepoBrain-Action`: main product action repository
- external repository: consumer project with its own caller workflow
- `repobrain-community`: retired and not used

`repobrain-community` is not required for current pilot onboarding or runtime wiring.

## Repository Roles

- `topocore`: private engine and decision internals; do not copy into consumer repositories
- `RepoBrain-Action`: product action, workflow truth, docs, tests, and pilot onboarding
- external repository: installs the caller workflow and owns smoke evidence
- `repobrain-community`: retired from runtime, install, docs, onboarding, and bridge responsibilities

## Required Secrets and Variables

Required secret in the consumer repository:

- `TOPOCORE_V6_REPO_TOKEN`
  - must grant read access to the private `topocore` repository
  - do not print or commit the token

Current RepoBrain-Action repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Operator note:

- this variable remains part of the current RepoBrain-Action repository setup
- the direct external pilot workflow documented here does not depend on `repobrain-community`
- if you keep the direct issue_comment private-checkout steps unconditional, the external caller repository does not need a separate `RB_ENABLE_ISSUE_COMMENT_V6_LAB` gate variable

## Minimal Workflow

Start from:

- `docs/examples/repobrain_external_pilot_workflow.yml`

Install it as:

- `.github/workflows/repobrain.yml`

Optional repo guidance example:

- `docs/examples/repobrain.instructions.md`
- copy to `.github/repobrain.instructions.md` only if you want concise repo-specific review hints

## TopoCore v6 Private Dependency Setup

The consumer workflow must:

1. checkout the consumer repository at the correct PR/issue ref
2. checkout private `alexworkingai/topocore`
3. expose the private checkout path through `RB_TOPOCORE_V6_LOCAL_PATH` and `PYTHONPATH`
4. call `alexworkingai/RepoBrain-Action@main`

Recommended caller-workflow permissions for external verify:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Why this is the current minimum for the direct pilot:

- `contents: read`
  - read repository files and diffs
- `models: read`
  - allow the current GitHub Models-backed external runtime path
- `issues: write`
  - post issue comments and PR issue-comment replies
- `pull-requests: read`
  - read PR metadata and changed-file context
- `checks: read`
  - read check-run state for `/repobrain verify`
- `statuses: read`
  - read combined commit status for `/repobrain verify`
- `actions: read`
  - read workflow-run state for `/repobrain verify`

Permissions not required for the current external product path:

- `contents: write`
- `checks: write`
- `pull-requests: write`
- `pull_request_target`
- deployment/package write permissions

Important:

- internal `RepoBrain-Action` maintenance workflows may retain broader permissions for deferred check publication
- consumer repositories should not copy those broader permissions into the external pilot workflow

Do not vendor or copy TopoCore v6 into `RepoBrain-Action` or the consumer repository.

## Commands For First Smoke

Safe first smoke on issue:

```text
/repobrain ask Summarize current RepoBrain TopoCore backend status.
```

Safe first smoke on PR:

```text
/repobrain ask Summarize this PR with RepoBrain backend diagnostics.
```

Validated command surface after Sprint 70:

- issue scope:
  - `/repobrain help`
  - `/repobrain ask ...`
  - `/repobrain locate ...`
  - `/repobrain explain ...`
  - `/repobrain review` returns honest scoped unsupported guidance
  - `/repobrain verify` returns honest scoped unsupported guidance
  - `/repobrain fix ...` returns honest scoped unsupported guidance
- PR scope:
  - `/repobrain ask ...`
  - `/repobrain review ...`
  - `/repobrain verify ...` as informational PR verification with explicit `PASS/WARN/FAIL/PENDING/NOT_RUN/UNKNOWN` status labels
  - `/repobrain fix ...` as safe proposal/governance with explicit no-mutation safety gates

Retrieval quality note after Sprint 71:

- setup-oriented issue queries should surface `.github/workflows/repobrain.yml` as primary evidence
- `.github/repobrain.instructions.md` and `docs/repobrain_pilot.md` should appear as supporting evidence rather than replacing the workflow file

## Expected Backend Evidence

Expected evidence in a healthy smoke run:

- requested backend: `auto` or `v6`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`
- no `repobrain-community` dependency
- no v5 fallback
- no patch/autofix behavior
- no commit/branch/PR creation by RepoBrain behavior

Expected verify truth after Sprint 72:

- issue-scope `/repobrain verify` remains scoped unsupported and points users to PR context
- PR-scope `/repobrain verify` is informational only
- `PASS` means observed verification signals are passing, not that merge is approved
- `NOT_RUN` means no concrete checks/statuses/workflow runs were observed for the PR head SHA
- limitations and source availability should appear directly in the comment

Expected fix truth after Sprint 73:

- issue-scope `/repobrain fix` remains scoped unsupported and no-mutation
- PR-scope `/repobrain fix` may return:
  - `PROPOSAL_READY`
  - `NO_ACTION_NEEDED`
  - `NEEDS_MORE_INFORMATION`
  - `BLOCKED_BY_SAFETY`
- visible safety gates should show:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- unsafe requests such as “apply the patch and commit the changes” should be blocked explicitly

## Troubleshooting

### Missing private dependency access

Symptoms:

- private checkout step fails
- runtime import diagnostics fail
- backend does not resolve to `v6`

Check:

- `TOPOCORE_V6_REPO_TOKEN` exists in the consumer repository
- token has read access to `alexworkingai/topocore`
- workflow still checks out the private repo before running RepoBrain

Expected failure shape:

- the workflow may fail during checkout or install before RepoBrain comment rendering starts
- the secret name can appear in setup logs
- the secret value must not appear
- private local paths or raw token material should not be printed

### Invalid private dependency token or private repo access mismatch

Symptoms:

- checkout of `alexworkingai/topocore` fails even though the secret exists
- RepoBrain never reaches backend execution

Check:

- `TOPOCORE_V6_REPO_TOKEN` still has read access to `alexworkingai/topocore`
- the token has not expired or been rotated without updating the repository secret
- the workflow still uses `secrets.TOPOCORE_V6_REPO_TOKEN`

Treat this as a sanitized setup failure, not as a runtime fallback case.

### Private action access or Actions policy failure

Symptoms:

- setup fails before RepoBrain starts
- GitHub Actions shows:
  - `Unable to resolve action ... repository not found`

This does not always mean the action ref is wrong.
It can also mean private action access is blocked.

Check:

- caller workflow uses `alexworkingai/RepoBrain-Action@main`
- `RepoBrain-Action` private action sharing is enabled for repositories owned by `alexworkingai`
- the consumer repository Actions policy does not stay on `local_only`
- if using selected actions, allow `alexworkingai/RepoBrain-Action`

Known pilot root cause from Sprint 69:

- `alexworkingai/Elen-MCP-v.2.2.0` had `allowed_actions=local_only`
- GitHub then surfaced `Unable to resolve action ... repository not found`

### Insufficient workflow permissions

Symptoms:

- `/repobrain verify` returns source limitations or permission guidance
- PR metadata or workflow-run evidence is incomplete

Check:

- the caller workflow still grants:
  - `models: read`
  - `issues: write`
  - `pull-requests: read`
  - `checks: read`
  - `statuses: read`
  - `actions: read`
- no one tightened the workflow by removing read scopes needed for verification

### Fork PR restricted behavior

Current direct-pilot policy:

- do not use `pull_request_target` for the RepoBrain external pilot
- do not expose `TOPOCORE_V6_REPO_TOKEN` to untrusted fork code
- do not checkout untrusted fork head code with the private TopoCore token

Current example workflow is conservative:

- same-repo PR comments use the PR head SHA
- fork PR comments stay on the default workflow/runtime SHA
- private TopoCore checkout still happens only inside the trusted base repository workflow context

If you need richer fork support later, treat it as separate hardening work rather than widening the current pilot by default.

### Wrong action install shape

Symptoms:

- workflow tries to execute consumer-repo scripts instead of RepoBrain-Action scripts

Check:

- caller workflow uses `alexworkingai/RepoBrain-Action@main`
- RepoBrain-Action action steps run from `GITHUB_ACTION_PATH`, not consumer workspace paths

### Missing backend evidence

Symptoms:

- comment appears but backend evidence is absent or incomplete

Check:

- current caller workflow still passes `topocore_backend`
- private TopoCore v6 install completed
- workflow did not silently downgrade to a different install path

## What Not To Use

Do not use:

- `repobrain-community`
- `v5`
- `lite`
- `pull_request_target` for the current external pilot
- patch/autofix by default
