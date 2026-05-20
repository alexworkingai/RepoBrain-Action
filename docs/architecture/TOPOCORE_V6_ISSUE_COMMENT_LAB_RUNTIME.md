# TopoCore v6 Issue Comment Lab Runtime

> Historical note: references below to v5 fallback or legacy `lite` execution are superseded. Sprint 65 removed deprecated v5 runtime execution, and Sprint 66 removed orphaned vendor assets. Current supported runtime policy is v6-only.


## 1. Purpose

Sprint 52 enables controlled GitHub `issue_comment` TopoCore v6 lab runtime with v5 fallback.
It follows the successful `workflow_dispatch` v6 `private_checkout` operational check after Sprint 51.
It is a lab runtime step, not a production or Marketplace switch.
v5 remains the fallback backend.
Patch application remains disabled.

## 2. Current Baseline

- latest accepted `main` before Sprint 52: `daf034d Make TKYA evidence upload optional for v6 lab`
- the post-Sprint-51 `workflow_dispatch` run succeeded
- evidence confirmed:
  - `requested_backend=v6`
  - `resolved_backend=v6`
  - `fallback_used=false`
  - `status=ready`
  - `action=proceed`
  - `message_code=DECISION_READY`
  - `confidence_band=high`
  - `decide_raw_used=false`
  - `patch_application=false`
  - `commit_branch_pr_creation=false`

## 3. issue_comment Lab Runtime Policy

`issue_comment` now uses a controlled lab gate:

- repository variable: `RB_ENABLE_ISSUE_COMMENT_V6_LAB`
- enable value: `1`
- disabled or absent value: fallback to the legacy safe path

Backend selection policy:

- when the gate is enabled for `/repobrain` comments:
  - `RB_TOPOCORE_BACKEND=auto`
- when the gate is disabled or absent:
  - backend remains effectively v5-pinned

Strict mode is off by default for `issue_comment`.

## 4. Private Dependency Handling

For gated `issue_comment` lab runs:

- private checkout and install are allowed
- token secret: `TOPOCORE_V6_REPO_TOKEN`
- no token values are committed
- no private URLs with credentials are printed
- checkout path: `.topocore-v6`
- ref defaults to `main`
- optional repository variables may override repository and ref:
  - `RB_ISSUE_COMMENT_TOPOCORE_V6_REPOSITORY`
  - `RB_ISSUE_COMMENT_TOPOCORE_V6_REF`

## 5. Fallback and Kill Switch

Fallback behavior:

- `auto` attempts v6 when the dependency is available
- if v6 is unavailable, the runtime falls back to v5 when strict mode is off

Kill switch behavior:

- set `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- or remove the variable entirely

Emergency revert path:

- disable the gate
- or force workflow-level backend handling back to v5 in a follow-up if needed

No v5 removal is included.

## 6. Safety Boundaries

- no `decide_raw`
- no patch application
- no file modification
- no commit, branch, or PR creation
- no safe-to-merge claim
- no security approval verdict
- no PR approval or rejection claim
- no `repobrain-community` change

## 7. workflow_dispatch Preservation

- the manual `workflow_dispatch` v6 `private_checkout` path remains available
- the lab backend evidence artifact remains available
- `workflow_dispatch` defaults remain safe

## 8. Expected Post-Merge Operational Check

Prerequisites:

- `TOPOCORE_V6_REPO_TOKEN` secret exists
- if repository-variable gating is used:
  - `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Run on a safe issue or PR comment:

- `/repobrain ask Summarize current RepoBrain TopoCore backend status.`

Expected:

- workflow success
- private TopoCore v6 checkout and install if the lab gate is enabled
- backend evidence in logs or artifacts shows `resolved_backend=v6`
- no patch application
- no commit, branch, or PR creation
- safe output only

Also test the kill switch:

- disable the gate or force v5
- rerun the same safe comment
- confirm v5 or fallback behavior

## 9. Sprint 53 Decision

If the Sprint 52 `issue_comment` operational check succeeds, Sprint 53 may either:

- make v6 lab runtime the maintained default for `issue_comment`, or
- start v5 deprecation planning

If it fails, Sprint 53 should fix only the specific remaining blocker.

## 10. Current State

Sprint 53 proved the controlled `issue_comment` v6 lab path and the v5 kill-switch path.

Current frozen operational state:

- v6 lab mode is proven
- the repository variable is intentionally left disabled at `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- normal `issue_comment` operational behavior is therefore still the v5-side path

See:

- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`

## 11. Non-Goals

- no v5 removal
- no production or Marketplace switch
- no default private dependency install outside gated `issue_comment` and `workflow_dispatch` lab paths
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment unsafe behavior change
- no `repobrain-community` change
