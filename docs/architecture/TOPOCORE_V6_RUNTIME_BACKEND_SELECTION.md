# TopoCore v6 Runtime Backend Selection

> Sprint 67 status: This file is retained only as a historical checkpoint. For current runtime policy use `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`, `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`, and `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`.

> Historical note: references below to v5 fallback or legacy `lite` execution are superseded. Sprint 65 removed deprecated v5 runtime execution, and Sprint 66 removed orphaned vendor assets. Current supported runtime policy is v6-only.


## 1. Purpose

Sprint 43 originally introduced selectable v5 and v6 backend support. This file is now historical only.

Current truth:

- historical only: v5 was once the default and fallback; current runtime is v6-only
- current supported selectors are `auto` and `v6`; v6 is no longer optional in the same sense
- GitHub runtime default behavior is unchanged
- fix migration is not included
- Sprint 65 later removed v5 runtime execution

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 43:
  - `6bde17d Implement real TopoCore v6 adapter contract`
- Sprint 42 implemented the real v6 adapter
- real local adapter smoke passed
- GitHub runtime still used v5 before Sprint 43

## 3. Backend Selection Rules

Backend selector rules:

- historical selector set at Sprint 43 time; current supported selectors are `auto` and `v6`
- `RB_TKYA_BACKEND` legacy values are now unsupported diagnostics only
- precedence:
  - `RB_TOPOCORE_BACKEND`
  - `RB_TKYA_BACKEND`
  - historical only: current runtime default is v6-oriented `auto`
- invalid backend values fail with a sanitized configuration error in direct or local calls
- strict local v6 behavior is controlled by `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 4. Runtime Boundary

Current runtime boundary:

- selector is introduced at the narrow TKY decision boundary
- GitHub runtime is not switched by default
- `action.yml` and workflows remain unchanged
- no v5 fallback remains in current runtime

## 5. V6 Backend Behavior

Current v6 backend behavior:

- dynamic import only
- `create_topocore()` plus `decide_external()` through the real adapter
- safe `ExternalDecisionView` extraction only
- no `decide_raw`
- missing dependency now fails safely without any v5 fallback
- strict local mode can fail safely when `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 6. Low-Risk Scope

Sprint 43 scope:

- low-risk lab or runtime backend selection for the current local TKY decision path
- fix path is not migrated
- patch behavior is unchanged
- PR comment and check behavior is unchanged by default

## 7. What Sprint 43 Enables

Sprint 43 enables:

- local or lab runs can select v6 backend explicitly
- Sprint 44 can expand review or verify paths
- Sprint 45 can separately decide fix migration
- Sprint 46 can consider v6 default lab runtime

## 8. Non-Goals

Current non-goals:

- historical note only; v5 runtime was removed in Sprint 65
- no workflow or `action.yml` change
- no default CI private dependency
- no `decide_raw`
- no fix migration
- no patch behavior change
- no PR, check, or comment behavior change
- no `repobrain-community` change

See also:

- `docs/architecture/TOPOCORE_V6_REVIEW_VERIFY_BACKEND_EXPANSION.md`
- `docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_DEFAULT_LAB_RUNTIME_POLICY.md`
