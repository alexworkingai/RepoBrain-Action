# TopoCore v6 Issue Comment Lab Gate Propagation Fix

## 1. Purpose

Sprint 53 fixes `issue_comment` TopoCore v6 lab gate and environment propagation.
Sprint 52 added the gate, but post-merge operational checks showed both `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1` and `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` still reported the v5-side runtime.
This sprint ensures the gated `issue_comment` path actually passes the intended backend path into the action and runtime.

## 2. Current Baseline

- latest accepted `main` before Sprint 53: `4e433a9 Enable issue comment TopoCore v6 lab runtime`
- post-Sprint-52 checks showed:
  - `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1` still reported legacy TKYA v5 diagnostics
  - `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` also reported legacy TKYA v5 diagnostics
- safety stayed intact:
  - no patch application
  - no commit, branch, or PR creation

## 3. Root Cause

The blocker was primarily a workflow-to-runtime provider-mode propagation issue.

- the workflow already passed `topocore_backend: auto` for gated `issue_comment`
- but the same action invocation still passed `tky_mode: auto`
- in `repobrain/github_flow.py`, `resolve_tky_mode()` resolves `auto` to `baseline` unless the remote path is enabled
- that meant gated `issue_comment` never reached `LocalTKYProvider`, so the TopoCore backend selector never ran
- operational diagnostics only showed legacy `TKYA backend` / `TKYA mode`, which was not enough to prove TopoCore v6 resolution even when local selector fields existed

This was not primarily an `action.yml` default-input override problem. The action already received an explicit `topocore_backend` expression; the missing piece was the provider mode needed to enter the local selector seam.

## 4. Fix

Sprint 53 applies four narrow changes:

1. effective `issue_comment` backend path:
   - gated `/repobrain` issue comments now pass `tky_mode=local`
   - gated `/repobrain` issue comments continue to pass `topocore_backend=auto`
2. disabled or absent gate behavior:
   - `issue_comment` continues to use the v5-side path with `topocore_backend=v5`
3. private dependency gating:
   - private checkout, install, path propagation, and issue-comment diagnostic remain gated by:
     - `github.event_name == 'issue_comment'`
     - `/repobrain` comment guard
     - `vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'`
4. backend evidence visibility:
   - GitHub runtime audit and rendered diagnostics now export safe TopoCore fields:
     - `requested_backend`
     - `resolved_backend`
     - `backend_mode`
     - `fallback_used`
     - `fallback_reason`

## 5. Gate Behavior

`RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`:

- `issue_comment` uses the local TopoCore-capable path
- private checkout and install can run
- path propagation and runtime import diagnostic can run
- `RB_TOPOCORE_BACKEND=auto` is passed into the action/runtime
- v5 fallback remains preserved because strict mode is still off by default

`RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` or variable absent:

- `issue_comment` remains on the v5-side path
- private checkout, install, path propagation, and import diagnostic do not run
- effective backend remains v5-side

## 6. Evidence

Expected safe evidence fields now include:

- `requested_backend`
- `resolved_backend`
- `fallback_used`
- `fallback_reason`
- legacy `TKYA backend`
- legacy `TKYA mode`

Clarification:

- legacy `TKYA backend` alone is not sufficient to prove TopoCore v6
- Sprint 53 adds explicit TopoCore backend evidence so operational checks can distinguish:
  - gated v6 lab success
  - safe fallback to v5
  - gate-disabled v5-side behavior

## 7. Safety Boundaries

- no `decide_raw`
- no patch application
- no file modification
- no commit, branch, or PR creation
- no safe-to-merge claim
- no security approval verdict
- no PR approval or rejection claim
- no `repobrain-community` change

## 8. Expected Post-Merge Operational Check

### A. Gate enabled

Set repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Comment:

- `/repobrain ask Summarize current RepoBrain TopoCore backend status.`

Expected:

- workflow success
- private checkout and install ran
- diagnostic ran
- `requested_backend=auto` or `v6`
- `resolved_backend=v6`
- `fallback_used=false`
- no patch application
- no commit, branch, or PR creation

### B. Kill switch

Set repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

Comment:

- `/repobrain ask Summarize current RepoBrain TopoCore backend status.`

Expected:

- workflow success
- private checkout and install did not run
- resolved backend stays v5-side
- no patch application
- no commit, branch, or PR creation

## 9. Sprint 54 Decision

If Sprint 53 post-merge operational checks pass, Sprint 54 can either:

- keep issue-comment v6 lab runtime as the active lab default, or
- start v5 deprecation planning

If the checks fail, Sprint 54 should fix only the specific remaining blocker.

## 10. Operational Follow-Up

The Sprint 53 operational checks succeeded and are frozen in the Sprint 54 closeout note:

- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`

Current frozen operational state after those checks:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
- issue-comment default remains the safe v5-side path
- controlled v6 lab mode remains available without a code change when the gate is intentionally enabled

## 11. Non-Goals

- no v5 removal
- no production or Marketplace switch
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no unsafe PR, check, or comment behavior
- no `repobrain-community` change
