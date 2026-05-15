# TopoCore v6 GitHub Lab Dependency Gate

## 1. Purpose

Sprint 48 adds a manual-only GitHub lab dependency gate for TopoCore v6.
Default `issue_comment` runtime remains v5.
`workflow_dispatch` default remains v5 and dependency mode `none`.
Private checkout is opt-in only.
Sprint 48 does not make TopoCore v6 a default CI dependency.
Sprint 48 does not remove v5.
Sprint 48 does not enable patch application.

## 2. Current Baseline

- latest accepted `main` before Sprint 48: `5a82c36 Add GitHub runtime TopoCore v6 lab switch`
- Sprint 47 added manual `workflow_dispatch` backend selection
- no private TopoCore install existed before Sprint 48
- default `issue_comment` runtime remained v5-pinned

## 3. Dependency Modes

### `none`

- runs for the default `workflow_dispatch` case
- requires no private secret or private checkout
- leaves TopoCore v6 unavailable unless the runner already has it
- keeps fallback behavior available when `v6` or `auto` is requested without an installed dependency

### `private_checkout`

- runs only for manual `workflow_dispatch`
- requires backend selection `v6` or `auto`
- requires `TOPOCORE_V6_REPO_TOKEN`
- checks out and installs TopoCore v6 for that job only
- fails the manual lab run clearly if checkout or install cannot complete

## 4. Manual Private Checkout Flow

- `workflow_dispatch` only
- backend must be `v6` or `auto`
- dependency mode must be `private_checkout`
- ref is controlled by `topocore_v6_ref`
- repository slug is provided through `topocore_v6_repository`
- token comes from `secrets.TOPOCORE_V6_REPO_TOKEN`
- checkout path is temporary: `./.topocore-v6`
- install is job-local only: `python -m pip install -e ./.topocore-v6`

## 5. Default Runtime Safety

- `issue_comment` does not checkout or install private TopoCore v6
- default `workflow_dispatch` does not checkout or install private TopoCore v6
- default CI does not require `topocore_v6`
- v5 fallback remains available

## 6. Secret Handling

- secret name used: `TOPOCORE_V6_REPO_TOKEN`
- no secret value is committed
- no token is printed
- no token is embedded in a URL
- no private dependency metadata is added to PR comments or checks

## 7. Failure Behavior

### dependency mode `none`

- if v6 is unavailable, the runtime falls back to v5 unless strict mode is explicitly set elsewhere

### dependency mode `private_checkout`

- checkout or install failure may fail the manual lab run
- default `issue_comment` path remains unaffected

### missing secret

- a manual `private_checkout` lab run fails clearly
- default `issue_comment` path remains unaffected

## 8. What Sprint 48 Enables

- a manual GitHub lab run can try real v6 when private checkout is configured
- the v6 backend can now be exercised in GitHub Actions context without changing default comment-driven behavior
- a future sprint can evaluate whether manual GitHub v6 validation should become more common

## 9. What Sprint 48 Does Not Enable

- no default v6 `issue_comment` runtime
- no production or Marketplace switch
- no v5 removal
- no patch application
- no commit, branch, or PR creation
- no `repobrain-community` change

## 10. Sprint 49 Target

Sprint 49 - GitHub Lab v6 Run Validation and Default Runtime Decision

Expected:
- run manual `workflow_dispatch` v6 `private_checkout` validation
- review sanitized outcomes
- decide whether `issue_comment` remains v5 or gets an explicitly approved v6 lab mode
- keep v5 fallback
- no v5 removal unless separately approved

## 11. Non-Goals

- no v5 removal
- no default v6 `issue_comment` runtime
- no default private dependency install
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change
