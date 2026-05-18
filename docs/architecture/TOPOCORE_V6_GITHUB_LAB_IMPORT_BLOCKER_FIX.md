# TopoCore v6 GitHub Lab Import Blocker Fix

## 1. Purpose

Sprint 50 fixes the GitHub `workflow_dispatch` TopoCore v6 import and public-API blocker.
Sprint 48 proved private checkout and install.
Sprint 49 added a meaningful lab decision path.
The post-Sprint-49 manual run failed because the action runtime reported that the TopoCore v6 public API was unavailable.
Sprint 50 adds runtime import diagnostics and explicit path propagation.

## 2. Current Baseline

- latest accepted `main` before Sprint 50: `080d6be Add workflow dispatch v6 decision path`
- manual run after Sprint 49 confirmed:
  - private checkout passed
  - private install passed
  - `topocore-v6-0.30.0` installed
  - `Run ./` failed with:
    - `LAB_BACKEND_EVIDENCE_FAILED=TopoCore v6 public API is unavailable.`

## 3. Root Problem

- dependency access is solved
- private install is solved
- the remaining blocker is Python runtime import and public-API visibility during the action execution step

## 4. Fix

Sprint 50 adds:

- `RB_TOPOCORE_V6_LOCAL_PATH` propagation for manual private-checkout lab runs
- `PYTHONPATH` propagation for manual private-checkout lab runs
- `scripts/check_topocore_v6_runtime_import.py`
- stricter sanitized runtime failure categories
- sanitized failure evidence for the meaningful lab command path

## 5. Workflow Scope

The new path propagation and runtime diagnostic run only when all of the following are true:

- `workflow_dispatch`
- `topocore_v6_dependency_mode=private_checkout`
- `topocore_backend=v6` or `topocore_backend=auto`

`issue_comment` is unchanged.
Default `workflow_dispatch` remains `v5` plus `none` plus `help`.

## 6. Safe Diagnostic Output

Allowed fields:

- import ok or fail
- version
- public API status
- health status
- failure category

Forbidden output:

- tokens
- private clone URLs
- raw env dump
- full `sys.path`
- raw stack traces
- raw code, diff, or prompt content
- `decide_raw`

## 7. Expected Post-Merge Operational Check

Manual run:

- `topocore_backend=v6`
- `topocore_v6_dependency_mode=private_checkout`
- `topocore_v6_ref=main`
- `repobrain_lab_command=ask`
- `repobrain_lab_query="Summarize current RepoBrain TopoCore backend status."`
- `repobrain_lab_fixture=minimal`

Expected evidence:

- `requested_backend=v6`
- `resolved_backend=v6`
- `fallback_used=false`
- `status` present
- `action` present
- `message_code` present
- `confidence_band` present

## 8. Non-Goals

- no v5 removal
- no default v6 `issue_comment` runtime
- no default private dependency install
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change
