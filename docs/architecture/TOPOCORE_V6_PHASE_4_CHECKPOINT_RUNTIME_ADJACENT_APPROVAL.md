# TopoCore v6 Phase 4 Checkpoint / Runtime-Adjacent Approval

## 1. Purpose

Sprint 33 is the Phase 4 checkpoint and runtime-adjacent approval gate.

Current truth:

- Sprint 33 is docs-only
- Sprint 33 does not implement runtime-adjacent work
- Sprint 33 does not activate advisory shadow mode
- Sprint 33 does not create canary behavior
- Sprint 33 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint exists to review the Phase 4 planning work completed so far, decide whether a narrowly bounded still-disabled implementation step may be proposed next, and keep all activation-risk boundaries explicit.

See also:

- `docs/architecture/TOPOCORE_V6_STILL_DISABLED_ADVISORY_BOUNDARY.md`
- `docs/architecture/TOPOCORE_V6_PHASE_5_BOUNDARY_GUARD_CHECKPOINT.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 33:
  - `3ab66f0 Docs: add TopoCore v6 advisory experiment runbook`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 complete:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-30
- Phase 4 planning in progress:
  - Controlled Advisory Shadow Experiment Planning, Sprints 31-32
- validation from Sprint 32:
  - `pytest` passed with `656` tests
- no runtime behavior was intentionally changed through Sprint 32

## 3. Phase 4 Review

Phase 4 work so far:

Sprint 31:

- defined Phase 4 scope and controlled advisory shadow experiment plan
- set Phase 4 as planning-first
- defined allowed scope, hard boundaries, environment gate targets, evidence requirements, artifact review checklist, and stop conditions

Sprint 32:

- defined controlled advisory experiment runbook
- defined operator steps
- defined evidence capture checklist
- defined human artifact review checklist
- defined rollback/disable procedure
- defined reviewer roles and future report template

Review conclusion:

- Phase 4 planning artifacts are sufficient for a checkpoint decision
- Phase 4 has not activated runtime behavior

## 4. Evidence Ledger

| Evidence area | Supporting sprint/artifact | Status | Notes |
|---|---|---|---|
| v5/TKYA remains active primary runtime | Sprints 16-32 docs/tests | Confirmed | No runtime routing changes were introduced. |
| TopoCore v6 not wired into live runtime | Sprints 27-32 docs/tests | Confirmed | Shadow-path work remains disconnected from protected runtime files. |
| disabled advisory skeleton exists | Sprint 28 module | Confirmed | `repobrain/topocore_v6_shadow_path.py` is present and isolated. |
| disabled/no-op default behavior exists | Sprint 28 module and Sprint 29 tests | Confirmed | Default and explicit-disabled modes remain no-op. |
| enabled flag does not call real v6 | Sprint 28 module and Sprint 29 tests | Confirmed | Enabled mode still returns safe unavailable/not-implemented status only. |
| guard tests cover forbidden input/output | Sprint 29 guard suite | Confirmed | Nested forbidden data, output safety, and failure categories are covered. |
| manual local harness exists | Sprint 21 harness and tests | Confirmed | Manual/local validation remains opt-in and dependency-tolerant. |
| decision-diff helper exists | Sprint 22 module | Confirmed | Safe snapshot diffing is available for advisory analysis. |
| advisory artifact helper exists | Sprint 24 module | Confirmed | Safe in-memory advisory artifact construction exists. |
| controlled experiment runbook exists | Sprint 32 doc | Confirmed | Future operator procedure is documented. |
| evidence checklist exists | Sprint 32 doc | Confirmed | Required evidence and forbidden evidence are documented. |
| rollback procedure exists | Sprint 32 doc | Confirmed | Disable/rollback steps are explicit. |
| human review checklist exists | Sprint 31-32 docs | Confirmed | Artifact review expectations are recorded. |
| default CI has no private TopoCore v6 dependency | Sprints 18-32 validation | Confirmed | Validation remains green without private dependency access. |
| validation remains green | Sprint 32 validation | Confirmed | `pytest` passed with `656` tests. |
| no user-visible output has changed | Sprints 16-32 scope and guards | Confirmed | No PR comments, checks, routes, or final outputs were altered. |

## 5. Gaps and Non-Proven Items

The following remains not proven:

- no real live advisory shadow behavior is proven
- no real GitHub runtime advisory path is wired
- no real PR runtime v5/v6 comparison evidence exists
- no canary behavior is proven
- no route migration is proven
- no v5 replacement path is proven
- no fix migration is proven
- no private dependency CI strategy is approved
- no production TopoCore v6 package or install strategy is approved
- no external or community runtime change is approved
- no user-visible product impact is validated because none was introduced

## 6. Approval Decision

Decision:

- GO for one narrowly bounded, still-disabled, non-user-visible runtime-adjacent implementation step

NO-GO for:

- advisory shadow activation
- canary
- route migration
- v5 replacement
- fix migration
- patch behavior change
- user-visible output change
- PR comment/check change
- default CI private dependency
- external or community runtime change

Clarification:

- Sprint 33 does not itself implement anything
- this GO permits only a future sprint to implement a still-disabled integration boundary
- any implementation must remain no-op by default and must be reversible

## 7. Next Phase Definition

Next phase:

- Phase 5 - Still-Disabled Runtime-Adjacent Advisory Integration Boundary

Purpose:

- introduce a still-disabled, no-op-by-default runtime-adjacent boundary around the existing shadow-path skeleton
- keep v5/TKYA as primary
- keep TopoCore v6 non-user-visible
- avoid live v6 calls by default
- avoid private dependency in default CI
- prove that the boundary can exist without affecting GitHub runtime behavior

Recommended limit:

- `2` sprints maximum before checkpoint

Suggested shape:

Sprint 34 - Still-Disabled Advisory Boundary Skeleton

- implementation-adjacent
- no-op by default
- behind explicit env gates
- no live v6 call by default
- no user-visible output change
- no artifact persistence or publishing

Sprint 35 - Boundary Guard Tests and Phase 5 Checkpoint

- guard tests for no-op, kill-switch, failure isolation, forbidden output, and no runtime output changes
- decide whether future controlled advisory experiment activation can even be proposed

## 8. Phase 5 Allowed Scope

Allowed:

- still-disabled boundary module or wrapper
- explicit no-op behavior
- env-gate parsing
- kill-switch handling
- tests proving no user-visible behavior changes
- tests proving no private dependency is required in default CI
- tests proving missing `topocore_v6` does not fail runtime
- tests proving no artifacts are published
- documentation of rollback and stop conditions

## 9. Phase 5 Hard Boundaries

Not allowed:

- live advisory shadow activation
- live v6 call in default runtime
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
- approval or rejection verdicts
- user-visible output changes
- PR comment/check changes
- external or community workflow changes
- marketplace or package strategy
- default CI dependency on private TopoCore v6
- `decide_raw` exposure
- raw or internal artifact persistence

## 10. Phase 5 Entry Gates

Before Phase 5 may begin, require:

- Sprint 33 accepted
- default CI green
- disabled/default harness check passes
- no runtime behavior changes through Sprint 33
- no unresolved forbidden-output findings
- no unresolved high-severity guardrail failures
- explicit human approval for Sprint 34 implementation-adjacent work
- explicit statement that Sprint 34 is still-disabled and non-user-visible

## 11. Runtime-Adjacent Implementation Gates

Before any future boundary can be merged, require:

- disabled by default
- no-op when disabled
- kill switch
- no private dependency required in default CI
- missing dependency falls back to v5-only
- no `topocore_v6` import at runtime module import time
- v6 failure cannot fail the main command
- v6 output cannot change final user-visible result
- no PR comment/check change
- no patch/fix behavior change
- no `decide_raw`
- no raw query, code, diff, prompts, or secrets in artifacts
- forbidden-output tests
- failure-isolation tests
- rollback instructions
- branch discipline and validation green

## 12. Stop Conditions

Future work must stop or downgrade to docs-only if:

- `topocore_v6` becomes required in default CI
- runtime output changes
- PR comments/checks change
- v6 failure can fail the main command
- forbidden raw/internal output appears
- `decide_raw` is called or exposed
- patch/fix behavior changes
- v6 advisory appears more permissive in sensitive, fix, or blocked cases
- high-severity decision-diff mismatches remain unresolved
- branch discipline or validation becomes unstable
- any external or community behavior change is required

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
- disabled advisory skeleton and guard tests
- Phase 4 controlled advisory planning
- future still-disabled boundary work only if approved

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

## 14. Explicit Non-Goals for Sprint 33

- no runtime code changes
- no tests required unless a docs validation issue requires it
- no implementation-adjacent code in Sprint 33
- no shadow-mode activation
- no advisory experiment activation
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
- no user-visible PR comment/check changes

## 15. Acceptance Criteria

Sprint 33 is complete only if:

- the new Phase 4 checkpoint/runtime-adjacent approval document exists
- Phase 4 work from Sprint 31 and Sprint 32 is reviewed
- evidence ledger exists
- gaps and non-proven items are listed
- approval decision is explicit
- next phase is defined
- next phase is limited to `2` sprints maximum before checkpoint
- allowed scope is defined
- hard boundaries are defined
- entry gates are defined
- runtime-adjacent implementation gates are defined
- stop conditions are defined
- repository boundaries are confirmed
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
