# TopoCore v6 Runtime Backend Selection

## 1. Purpose

Sprint 43 introduces selectable v5 and v6 backend support.

Current truth:

- v5 remains the default and fallback
- v6 is opt-in
- GitHub runtime default behavior is unchanged
- fix migration is not included
- v5 removal is not included

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 43:
  - `6bde17d Implement real TopoCore v6 adapter contract`
- Sprint 42 implemented the real v6 adapter
- real local adapter smoke passed
- GitHub runtime still used v5 before Sprint 43

## 3. Backend Selection Rules

Backend selector rules:

- `RB_TOPOCORE_BACKEND=v5|v6`
- `RB_TKYA_BACKEND=v5|v6` remains supported for backward compatibility
- precedence:
  - `RB_TOPOCORE_BACKEND`
  - `RB_TKYA_BACKEND`
  - default `v5`
- invalid backend values fail with a sanitized configuration error in direct or local calls
- strict local v6 behavior is controlled by `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 4. Runtime Boundary

Current runtime boundary:

- selector is introduced at the narrow TKY decision boundary
- GitHub runtime is not switched by default
- `action.yml` and workflows remain unchanged
- v5 fallback remains available

## 5. V6 Backend Behavior

Current v6 backend behavior:

- dynamic import only
- `create_topocore()` plus `decide_external()` through the real adapter
- safe `ExternalDecisionView` extraction only
- no `decide_raw`
- missing dependency falls back to v5 by default
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

- no v5 removal
- no workflow or `action.yml` change
- no default CI private dependency
- no `decide_raw`
- no fix migration
- no patch behavior change
- no PR, check, or comment behavior change
- no `repobrain-community` change
