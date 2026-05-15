# TopoCore v6 Default Lab Runtime Policy

## 1. Purpose

Sprint 46 makes v6 the preferred default for lab and local runtime policy.

Current truth:

- v5 remains fallback and explicit selectable backend
- GitHub Actions default behavior remains unchanged because `action.yml` still pins the v5-side backend
- v5 removal is not included
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

- `RB_TOPOCORE_BACKEND=v5|v6|auto`
- `RB_TKYA_BACKEND=v5|v6|lite` remains backward-compatible
- `RB_TOPOCORE_BACKEND` takes precedence over `RB_TKYA_BACKEND`
- no-env local or lab default is now `auto`
- `auto` is v6-preferred and falls back to v5 when v6 is unavailable
- `action.yml` pin keeps GitHub default on the v5-side backend
- missing v6 falls back safely unless strict local mode is enabled
- strict local mode is controlled by `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 4. Lab/Local Default

Current lab or local default:

- when no backend env is set, the local or lab path attempts v6 first
- if v6 is available, local or lab runtime uses v6
- if v6 is unavailable, runtime falls back to v5
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

- explicit `v5` always uses v5
- explicit `v6` tries v6 and falls back to v5 unless strict local mode is enabled
- `auto` tries v6 and falls back to v5 unless strict local mode is enabled
- invalid backend values fail safely
- no raw paths or secrets appear in surfaced errors

## 9. Sprint 47 Target

Sprint 47 target:

- Sprint 47 - GitHub Runtime v6 Lab Switch Proposal or Implementation Gate

Expected scope:

- decide whether GitHub Action default remains pinned to v5 or gets a lab-only v6 switch
- if implementation is allowed, make it explicit and reversible
- preserve v5 fallback
- no v5 removal yet

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
