# TopoCore v6 Phase 1-2 Closeout and Phase 3 Scope

## 1. Purpose

Sprint 26 closes Phase 1 and Phase 2.

Current truth:

- Sprint 26 defines Phase 3 scope
- Sprint 26 does not implement Phase 3
- Sprint 26 does not activate shadow mode
- Sprint 26 does not change runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains manual, local, and advisory only

This sprint is a documentation and checkpoint sprint. Its job is to close the early migration-preparation phases cleanly and prevent uncontrolled expansion into runtime-adjacent work without explicit approval.

## 2. Current Main Baseline

Current accepted baseline:

- `main` includes Sprints 16-25
- latest accepted main commit before Sprint 26:
  - `93ec0e0 Integrate manual TopoCore v6 advisory artifact harness`
- validation from Sprint 25:
  - `pytest` passed with `595` tests
- no runtime behavior was intentionally changed through Sprint 25

## 3. Phase 1 Closeout

Phase 1 definition:

- Phase 1 - Controlled Migration Foundation
- Sprints 16-22
- Status: complete

Sprint outcomes:

Sprint 16:

- v5 -> v6 controlled migration blueprint

Sprint 17:

- GitHub Models LLM summary contract

Sprint 18:

- inert `RepoBrainTopoCoreV6Adapter` skeleton

Sprint 19:

- fake/stub TopoCore v6 compatibility tests

Sprint 20:

- local/private validation harness plan

Sprint 21:

- manual/disabled local TopoCore v6 validation harness

Sprint 22:

- sanitized decision-diff strategy

Phase 1 result:

- RepoBrain has the non-runtime foundation required to reason about a controlled v5 -> v6 migration
- v5/TKYA remains the active primary runtime
- TopoCore v6 is not wired into GitHub runtime
- default CI does not require private TopoCore v6

## 4. Phase 2 Closeout

Phase 2 definition:

- Phase 2 - Shadow Readiness / Advisory Evidence Layer
- Sprints 23-25
- Status: complete

Sprint outcomes:

Sprint 23:

- shadow-mode design and go/no-go criteria

Sprint 24:

- advisory artifact format and shadow implementation plan

Sprint 25:

- manual decision-diff advisory artifact harness integration

Phase 2 result:

- RepoBrain can manually and locally produce sanitized advisory evidence artifacts
- advisory artifacts are in-memory or stdout only
- JSON output is opt-in and sanitized
- no artifact persistence or publication was introduced
- no shadow mode was activated
- no canary was introduced
- no runtime behavior changed

## 5. What Is Proven

The following is proven now:

- current v5/TKYA runtime baseline is preserved
- GitHub Models remains the current LLM provider path
- adapter skeleton exists and is dependency-free
- stub compatibility tests exist
- manual/local TopoCore v6 validation harness exists
- decision-diff helper exists
- advisory artifact helper exists
- the manual harness can integrate decision-diff and advisory artifact helpers in explicit opt-in local mode
- the disabled/default harness path exits cleanly without private TopoCore v6
- default CI does not require `topocore_v6`
- validation remains green

## 6. What Is Not Proven Yet

The following is not proven:

- no live shadow-mode behavior is proven
- no GitHub runtime v6 advisory path is wired
- no v5/v6 parity is proven on real PR runtime traffic
- no canary is proven
- no route migration is proven
- no fix migration is proven
- no private dependency CI strategy is approved
- no production packaging strategy for TopoCore v6 is approved
- no user-visible product behavior is changed

## 7. Phase 3 Definition

Phase 3 definition:

- Phase 3 - Disabled Advisory Shadow Path Preparation

Recommended limit:

- `3` to `4` sprints maximum

Purpose:

- prepare a disabled-by-default advisory shadow path without activating it by default
- define exact runtime-adjacent integration seams
- define env-gated kill-switch behavior
- define safe internal artifact handling
- define PR/CI validation expectations before any advisory path can run in real GitHub workflow context

Rules:

- Phase 3 is still not canary
- Phase 3 is still not v5 replacement
- Phase 3 is still not fix migration
- Phase 3 should end with either:
  - `A.` approved disabled-by-default advisory path design/implementation readiness, or
  - `B.` blocked status with reasons

## 8. Proposed Phase 3 Sprint Scope

Proposed Phase 3 scope is `3` to `4` sprints:

Sprint 27 - Shadow Path Runtime Seam Design

- design the exact insertion seam for future advisory-only runtime work
- define where the sanitized summary bundle would be produced
- define where advisory result would be collected
- define what must remain non-user-visible
- docs/tests only unless explicitly approved

Sprint 28 - Disabled Advisory Path Skeleton

- optional skeleton behind hard-disabled env flags
- no default activation
- no default CI private dependency
- no user-visible output change
- v5 remains primary
- must safely no-op when disabled

Sprint 29 - Advisory Path Internal Artifact Guard Tests

- tests for kill switch, no-op behavior, forbidden output, and failure isolation
- no PR/check/comment publication
- no route migration
- no fix behavior change

Sprint 30 - Phase 3 Review / Go-No-Go for Runtime-Adjacent Experiment

- decide whether a future advisory shadow experiment is allowed
- define required PR/CI validation
- define rollback plan
- explicitly approve or block the next phase

If fewer sprints are possible, Sprint 29 and Sprint 30 may be consolidated only if risk remains low.

## 9. Phase 3 Hard Boundaries

Phase 3 must not include:

- canary
- route migration
- v5 replacement
- fix migration
- patch behavior change
- patch application
- file modification
- commit creation
- branch creation
- PR creation
- safe-to-merge claims
- security verdicts
- approval/rejection verdicts
- public external runtime behavior changes
- `repobrain-community` changes unless explicitly scoped later

## 10. Phase 3 Runtime-Adjacent Gates

Before any runtime-adjacent work is allowed, require:

- explicit sprint prompt approval
- default disabled behavior
- kill switch
- no-op behavior when disabled
- no private dependency requirement in default CI
- no user-visible output change
- no `decide_raw` usage
- forbidden-output tests
- failure isolation tests
- v5-only fallback preserved
- clear rollback instructions

## 11. Stop Conditions

Phase 3 must stop or downgrade to docs-only if:

- private TopoCore v6 dependency becomes required by default CI
- the disabled path can affect user-visible output
- v6 failure can fail the main RepoBrain command
- forbidden raw/internal data appears
- patch/fix behavior changes
- v6 advisory appears more permissive in sensitive, fix, or blocked cases
- high-severity diff mismatches are unresolved
- workflow or `action.yml` changes are required before approval
- branch discipline or validation becomes unstable

## 12. Phase 4 Placeholder

High-level placeholder only:

- Phase 4 may be Controlled Advisory Shadow Experiment

But only after Phase 3 closeout.

Phase 4 would still not automatically mean:

- canary
- route migration
- fix migration
- v5 retirement

Sprint 26 does not define a detailed Phase 4 roadmap.

## 13. Repository Boundary Confirmation

Repository boundaries remain:

RepoBrain-Action owns:

- primary/private GitHub runtime
- current v5/TKYA contract truth
- future v6 adapter around the public facade
- GitHub Models LLM orchestration
- safe product-level output mapping
- tests/docs/regression guards
- manual/local advisory validation and artifact helpers

TopoCore v6 owns:

- foundation decision library
- public facade
- decision contracts
- typed-summary ingestion
- safe external decision boundary

`repobrain-community` owns:

- public external GitHub foundation host
- reusable external workflow
- public install template
- bounded external command surface

`elen-mcp-prod_v2`:

- validation-only surface

## 14. Explicit Non-Goals for Sprint 26

- no runtime code changes
- no shadow-mode implementation
- no disabled advisory path implementation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency
- no `topocore_v6` import
- no `create_topocore()` call
- no `decide()` call
- no `decide_external()` call
- no `decide_raw()` call
- no LLM provider change
- no GitHub Models prompt behavior change
- no `repobrain-community` change
- no live GitHub API usage
- no live GitHub Models usage
- no artifact disk write/upload/publish behavior

## 15. Acceptance Criteria

Sprint 26 is complete only if:

- the new phase closeout document exists
- Phase 1 is clearly closed as Sprints 16-22
- Phase 2 is clearly closed as Sprints 23-25
- Phase 3 scope is clearly defined
- Phase 3 is limited to `3` to `4` sprints
- Phase 3 hard boundaries are defined
- Phase 3 runtime-adjacent gates are defined
- stop conditions are defined
- Phase 4 is only a high-level placeholder
- repository boundaries are confirmed
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains manual/local/advisory only
- no runtime behavior changes are introduced
