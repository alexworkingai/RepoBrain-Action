# Sprint 69 - External Repo Pilot And Community Removal

## Purpose

Sprint 69 starts product validation after the v6-only closeout.
It removes `repobrain-community` from the working architecture and connects the first external pilot repository: `Elen-MCP-v.2.2.0`.

## Baseline

- RepoBrain-Action latest accepted `main` before Sprint 69:
  - `fa14451 Close v6-only TopoCore transition`
- v6-only closeout passed
- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- TopoCore v6 remains private
- pilot repository local path:
  - `D:\ARIADNA_Minsk\1MyProjects\Elen-MCP-v.2.2.0`
- pilot repository GitHub:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0`

## Repository Structure Decision

- `topocore`
  - private permanently
  - engine and private decision internals
- `RepoBrain-Action`
  - main product action
  - workflow truth, docs, tests, onboarding, and static guards
- `Elen-MCP-v.2.2.0`
  - private pilot external consumer repository
- `repobrain-community`
  - removed from the working product architecture
  - read-only audited only during this sprint
  - optional archival later

## repobrain-community Audit

- read-only audit performed:
  - yes
- useful material migrated:
  - yes
- migrated/adapted material:
  - caller workflow shape
  - repo guidance example
  - quick-install wording adapted into direct pilot docs
- resulting policy:
  - no runtime dependency remains
  - no install bridge remains
  - no onboarding bridge remains

## Elen-MCP Sync

Initial state:

- branch:
  - `test/sprint-73-guidance-live-validation`
- local `HEAD` before sync work:
  - `0835bd2 Add Sprint 73 live validation marker`
- remote `main`:
  - `d68e52d Merge pull request #10 from alexworkingai/codex/sprint-73-guidance-validation-file`
- worktree:
  - dirty local state with many tracked modifications and untracked source/docs/config additions

Sync strategy:

- preserve local state
- create dedicated sync branch
- avoid direct overwrite of `main`
- avoid force-push

Execution:

- branch created:
  - `codex/sprint-69-sync-local-elen-mcp`
- sync commit:
  - `301d5c3 Sync local project state and install RepoBrain pilot workflow`
- push mode:
  - normal push to new branch
- PR created:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/12`

## Workflow Install

- workflow path:
  - `.github/workflows/repobrain.yml`
- replaced:
  - `.github/workflows/repobrain-smoke.yml`
- action ref:
  - `alexworkingai/RepoBrain-Action@main`
- TopoCore v6 dependency mode:
  - `private_checkout`
- additional pilot doc:
  - `docs/repobrain_pilot.md`
- repo guidance file updated:
  - `.github/repobrain.instructions.md`
- no `repobrain-community` dependency:
  - yes

Secrets and variables:

- `gh secret list --repo alexworkingai/Elen-MCP-v.2.2.0`
  - no visible secrets configured at sprint execution time
- `gh variable list --repo alexworkingai/Elen-MCP-v.2.2.0`
  - no visible repo variables configured at sprint execution time
- required secret for live v6 private checkout:
  - `TOPOCORE_V6_REPO_TOKEN`
- blocker status:
  - not available in the operator environment or target repository during this sprint

## Live Smoke Results

Issue smoke:

- run:
  - not run
- reason:
  - live issue-comment v6 smoke requires the direct pilot workflow on the default branch and a configured `TOPOCORE_V6_REPO_TOKEN`
- requested/resolved backend:
  - not executed

PR smoke:

- run:
  - not run
- reason:
  - same blocker as issue smoke; direct pilot workflow exists on the sync branch/PR, but private TopoCore access was not configured
- requested/resolved backend:
  - not executed

## Blockers

- missing `TOPOCORE_V6_REPO_TOKEN` in the pilot repository
- no `TOPOCORE_V6_REPO_TOKEN` present in the local operator environment
- local `Elen-MCP-v.2.2.0` Node validation blocked because `npm` / `npx` are not installed in the current operator environment
- direct issue-comment smoke should not be run against `main` until the direct workflow is merged and the secret exists

## Current Product Status

`BLOCKED_ON_SECRET_OR_ACCESS`

What is complete:

- `repobrain-community` removed from active product architecture
- direct external pilot docs/examples added to `RepoBrain-Action`
- remote-safe composite action install path fixed
- pilot repository sync branch pushed
- pilot PR opened
- direct pilot workflow prepared in the consumer repo

What remains blocked:

- live issue smoke
- live PR smoke
- workflow_dispatch v6 private-checkout proof on the pilot repo

## Sprint 70 Follow-up

Sprint 70 removed the remaining pilot blockers:

- `TOPOCORE_V6_REPO_TOKEN` was configured in `Elen-MCP-v.2.2.0`
- GitHub Actions policy in `Elen-MCP-v.2.2.0` was changed from `local_only` to `all`
- external issue and PR `ask` smoke passed on the direct `RepoBrain-Action` install path
- the full external command matrix is recorded in:
  - `docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md`

## Next Step

Recommended Sprint 70:

- External Repo Command Matrix
- once `TOPOCORE_V6_REPO_TOKEN` is configured in `Elen-MCP-v.2.2.0`, run:
  - issue `/repobrain ask`
  - PR `/repobrain ask`
  - bounded workflow_dispatch v6/private-checkout sanity if helpful
- then expand to:
  - `help/status`
  - `ask`
  - `explain/locate`
  - `review`
  - `verify`
  - `fix-lite`

## Non-Goals

- no v5
- no `repobrain-community` dependency
- no patch/autofix
- no production/Marketplace switch
- no `repobrain-community` modifications
