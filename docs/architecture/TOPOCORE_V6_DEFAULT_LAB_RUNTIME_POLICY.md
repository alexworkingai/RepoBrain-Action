# TopoCore v6 Default Lab Runtime Policy

> Sprint 67 status: This file is retained only as a historical checkpoint. For current runtime policy use `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`, `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`, and `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`.

> Historical note: references below to v5 fallback or legacy `lite` execution are superseded. Sprint 65 removed deprecated v5 runtime execution, and Sprint 66 removed orphaned vendor assets. Current supported runtime policy is v6-only.


## 1. Purpose

Sprint 46 makes v6 the preferred default for lab and local runtime policy.

Current truth:

- historical note: Sprint 46 still treated v5 as fallback; current runtime is v6-only
- historical note: GitHub Actions later moved away from any supported v5-side backend
- Sprint 65 later removed v5 runtime execution
- patch application is not included

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 46:
  - `a15f7b4 Add guarded TopoCore v6 fix lite path`
- Sprint 43 introduced selectable backend
- Sprint 44 expanded review and verify coverage
- Sprint 45 added guarded fix-lite decision
- v6 local smoke had already passed across low-risk, review or verify, and fix-lite paths

## 3. Backend Policy

Current backend policy:

- historical selector set at Sprint 46 time; current supported selectors are `auto` and `v6` only
- `RB_TKYA_BACKEND` legacy values are now unsupported diagnostics only
- `RB_TOPOCORE_BACKEND` takes precedence over `RB_TKYA_BACKEND`
- no-env local or lab default is now `auto`
- `auto` is now v6-only and fails safely when v6 is unavailable
- current workflow and action defaults no longer expose a v5-side backend
- missing v6 now fails safely; there is no v5 fallback
- strict local mode is controlled by `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 4. Lab/Local Default

Current lab or local default:

- when no backend env is set, the local or lab path attempts v6 first
- if v6 is available, local or lab runtime uses v6
- if v6 is unavailable today, runtime fails safely
- this does not make `topocore_v6` required in default CI

## 5. GitHub Runtime Boundary

Current GitHub runtime boundary:

- `action.yml` is unchanged
- workflows are unchanged
- default GitHub runtime behavior is unchanged
- the current GitHub Action path remains pinned to v5 unless a later explicit sprint changes it

## 6. Command Coverage

Current v6 command coverage under the lab or local policy:

- ask, explain, and locate-like paths
- review-like paths
- verify-like paths
- guarded fix-lite decision path

## 7. Fix/Patch Boundary

Current boundary:

- fix-lite remains decision and governance only
- no patch application
- no file modification
- no commit, branch, or PR creation
- no safe-to-merge, security, or approval claims

## 8. Fallback and Failure Behavior

Current fallback and failure behavior:

- explicit `v5` is now an unsupported legacy input
- explicit `v6` now requires v6 and fails safely if unavailable
- `auto` now tries v6 and fails safely if unavailable
- invalid backend values fail safely
- no raw paths or secrets appear in surfaced errors

## 9. Sprint 47 Target

Sprint 47 target:

- Sprint 47 - GitHub Runtime v6 Lab Switch Proposal or Implementation Gate

Expected scope:

- decide whether GitHub Action default remains pinned to v5 or gets a lab-only v6 switch
- if implementation is allowed, make it explicit and reversible
- no v5 fallback remains in current runtime
- historical note only; v5 runtime was removed in Sprint 65

## 10. Non-Goals

Current non-goals:

- no v5 removal
- no workflow or `action.yml` change in Sprint 46
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change

See also:

- `docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md`
- `docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
