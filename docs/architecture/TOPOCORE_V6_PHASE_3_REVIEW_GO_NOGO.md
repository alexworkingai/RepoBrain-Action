# TopoCore v6 Phase 3 Review / Go-No-Go

## 1. Purpose

Sprint 30 reviews and closes Phase 3.

Current truth:

- Sprint 30 defines go/no-go status for a future Phase 4
- Sprint 30 does not activate shadow mode
- Sprint 30 does not create a canary
- Sprint 30 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint is a documentation and checkpoint sprint. Its job is to close Phase 3 cleanly, record the evidence gathered so far, and prevent accidental escalation into runtime-affecting work without a fresh explicit approval.

See also:

- `docs/architecture/TOPOCORE_V6_PHASE_4_SCOPE_AND_CONTROLLED_ADVISORY_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_CONTROLLED_ADVISORY_EXPERIMENT_RUNBOOK.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 30:
  - `6890a09 Add TopoCore v6 advisory path guard tests`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 in review:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-29
- validation from Sprint 29:
  - `pytest` passed with `656` tests
- no runtime behavior was intentionally changed through Sprint 29

## 3. Phase 3 Scope Recap

Phase 3 definition:

- Phase 3 - Disabled Advisory Shadow Path Preparation

Scope:

- design the future advisory shadow runtime seam
- create a hard-disabled no-op advisory skeleton
- strengthen guard tests around the skeleton
- keep everything disabled, isolated, and non-user-visible

Explicit non-scope:

- no live shadow activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no public or external runtime change

## 4. Sprint 27 Review

Sprint 27 outcome:

- Sprint 27 - Shadow Path Runtime Seam Design

Captured:

- future seam location before final rendering
- v5 primary path remains protected
- v6 advisory branch remains non-user-visible
- sanitized summary bundle boundary
- sanitized advisory snapshot boundary
- no-op and kill-switch requirements
- failure isolation requirements
- artifact handling boundaries

Decision:

- accepted as design foundation for Phase 3

## 5. Sprint 28 Review

Sprint 28 outcome:

- Sprint 28 - Disabled Advisory Path Skeleton

Captured:

- dependency-free `repobrain/topocore_v6_shadow_path.py`
- disabled and no-op by default
- explicit disabled flag behavior
- enabled flag still does not call v6
- artifact flag recognized but does not persist or publish
- fail-closed flag recorded but does not affect runtime
- forbidden input rejection
- product-safe JSON-serializable result

Decision:

- accepted as hard-disabled skeleton
- not active runtime wiring

## 6. Sprint 29 Review

Sprint 29 outcome:

- Sprint 29 - Advisory Path Internal Artifact Guard Tests

Captured:

- guard tests for no-op behavior
- artifact flag safety
- fail-closed recording
- forbidden input and nested forbidden-field blocking
- forbidden output prevention
- sanitized failure categories
- no runtime wiring checks
- no `topocore_v6` dependency checks
- fix-command conservatism
- stable JSON serialization

Decision:

- accepted as safety guard layer for the disabled skeleton

## 7. Evidence Ledger

| Evidence area | Supporting sprint/artifact | Status | Notes |
|---|---|---|---|
| v5/TKYA remains active primary runtime | Sprints 16-29 docs and guardrails | Confirmed | No runtime routing changes were introduced. |
| TopoCore v6 is not wired into live runtime | Sprints 27-29 docs/tests | Confirmed | Runtime files remain free of shadow-path wiring. |
| no `topocore_v6` dependency in default CI | Sprints 18-29 tests and validation | Confirmed | Default validation remains green without private dependency access. |
| no `topocore_v6` import in runtime modules | Sprint 29 guard tests | Confirmed | Dependency-free module imports are enforced by tests. |
| disabled advisory skeleton exists | Sprint 28 module | Confirmed | `repobrain/topocore_v6_shadow_path.py` is present and isolated. |
| skeleton no-ops by default | Sprint 28 module and Sprint 29 guard tests | Confirmed | Disabled/default path returns safe no-op result. |
| enabled flag does not call real v6 | Sprint 28 module and Sprint 29 guard tests | Confirmed | Enabled mode remains `enabled_not_implemented` or artifact-unavailable only. |
| artifact flag does not persist or publish | Sprint 28 module and Sprint 29 guard tests | Confirmed | No disk writes, uploads, or publication behaviors are present. |
| forbidden fields are blocked | Sprint 28 module and Sprint 29 guard tests | Confirmed | Input and output boundaries reject forbidden keys, including nested cases. |
| decision-diff helper exists | Sprint 22 module | Confirmed | Safe snapshot diff helper is in place. |
| advisory artifact helper exists | Sprint 24 module | Confirmed | Safe in-memory artifact builder exists. |
| manual harness exists | Sprint 21 script and tests | Confirmed | Manual/local validation harness is available and opt-in only. |
| manual artifact integration exists | Sprint 25 harness integration | Confirmed | Manual harness can build diff/artifact evidence in explicit local mode. |
| disabled/default harness skips cleanly | Sprints 21-29 validation | Confirmed | Default path exits `0` with the same manual-only skip message. |
| tests are green | Sprint 29 validation | Confirmed | `pytest` passed with `656` tests. |

## 8. Gaps and Non-Proven Items

The following is not proven:

- no real live shadow-mode behavior is proven
- no real GitHub workflow advisory path is proven
- no real PR runtime v5/v6 diff evidence is proven
- no canary behavior is proven
- no route migration is proven
- no fix migration is proven
- no v5 retirement path is proven
- no private dependency CI strategy is approved
- no production TopoCore v6 package strategy is approved
- no public or external community integration is changed
- no user-visible product impact is validated because none was introduced

## 9. Go/No-Go Decision

Decision:

- GO for Phase 4 planning and strictly disabled advisory shadow experiment design

NO-GO for:

- canary
- route migration
- v5 replacement
- fix migration
- patch behavior change
- user-visible output change
- default CI private dependency
- external or community runtime change

Clarification:

- Phase 3 does not authorize live advisory activation by itself
- Phase 3 authorizes only a future Phase 4 proposal under strict gates

## 10. Phase 4 Definition

High-level next phase only:

- Phase 4 - Controlled Advisory Shadow Experiment Planning

Purpose:

- prepare a tightly controlled advisory-only experiment where v5 remains primary
- keep v6 advisory non-user-visible
- keep outputs limited to sanitized internal artifacts only
- require the experiment to be default-disabled
- require failure to fall back safely to v5-only behavior
- prevent changes to comments, checks, routes, or fix behavior

Recommended limit:

- `2` to `3` sprints maximum before another checkpoint

## 11. Phase 4 Allowed Scope

Allowed:

- design an explicit disabled-by-default advisory experiment plan
- define exact env gates and kill switch
- define private or local dependency handling
- define artifact collection strategy
- define PR/CI validation branch requirements
- define rollback and stop procedures
- define runtime-adjacent tests before activation
- possibly implement a still-disabled integration seam only after explicit approval

## 12. Phase 4 Hard Boundaries

Not allowed without separate explicit approval:

- canary
- route migration
- v5 replacement
- fix migration
- patch application
- user-visible output changes
- PR comment/check changes
- external or community workflow changes
- marketplace or package strategy
- default CI dependency on private TopoCore v6
- any `decide_raw` exposure
- any raw or internal artifact persistence

## 13. Phase 4 Entry Gates

Before Phase 4 may begin, require:

- Sprint 30 closeout accepted
- default CI green
- disabled/default harness still cleanly skips
- no runtime behavior changes through Phase 3
- no unresolved forbidden-output findings
- no unresolved high-severity guardrail failures
- explicit human approval for any runtime-adjacent implementation work
- explicit statement whether Phase 4 is docs-only or implementation-adjacent

## 14. Future Runtime-Adjacent Gates

Before any future advisory runtime seam can be implemented or connected, require:

- hard-disabled default
- kill switch
- no-op when disabled
- no private dependency required by default CI
- missing dependency falls back to v5-only
- v6 failure cannot fail the main command
- v6 failure cannot block PR comment/check publication
- v6 output cannot change final user-visible result
- no `decide_raw`
- no raw query, code, diff, prompts, or secrets in artifacts
- forbidden-output tests
- failure-isolation tests
- rollback instructions
- manual validation evidence

## 15. Stop Conditions

Future work must stop or downgrade to docs-only if:

- private TopoCore v6 dependency becomes required by default CI
- disabled path can affect user-visible output
- v6 failure can fail the main RepoBrain command
- forbidden raw/internal data appears
- patch/fix behavior changes
- v6 advisory appears more permissive in sensitive, fix, or blocked cases
- high-severity diff mismatches are unresolved
- workflow or `action.yml` changes are required before approval
- branch discipline or validation becomes unstable
- user-visible behavior changes without explicit approval

## 16. Repository Boundary Confirmation

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

## 17. Explicit Non-Goals for Sprint 30

- no runtime code changes
- no tests required unless a docs validation issue requires it
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

## 18. Acceptance Criteria

Sprint 30 is complete only if:

- the new Phase 3 review/go-no-go document exists
- Phase 3 is clearly reviewed
- Sprint 27, Sprint 28, and Sprint 29 outcomes are summarized
- evidence ledger exists
- gaps and non-proven items are listed
- go/no-go decision is explicit
- Phase 4 is defined only at high level
- Phase 4 allowed scope and hard boundaries are defined
- Phase 4 entry gates are defined
- future runtime-adjacent gates are defined
- stop conditions are defined
- repository boundaries are confirmed
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
