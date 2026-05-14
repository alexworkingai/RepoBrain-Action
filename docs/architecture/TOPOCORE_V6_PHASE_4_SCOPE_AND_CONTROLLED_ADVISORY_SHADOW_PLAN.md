# TopoCore v6 Phase 4 Scope and Controlled Advisory Shadow Plan

## 1. Purpose

Sprint 31 starts Phase 4 as docs-only.

Current truth:

- Sprint 31 defines Phase 4 scope and boundaries
- Sprint 31 does not implement advisory shadow mode
- Sprint 31 does not activate shadow mode
- Sprint 31 does not create a canary
- Sprint 31 does not change runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint is a documentation and checkpoint sprint. Its job is to start Phase 4 without crossing into runtime work, preserve the Sprint 30 go/no-go decision, and keep the future advisory experiment tightly bounded.

See also:

- `docs/architecture/TOPOCORE_V6_CONTROLLED_ADVISORY_EXPERIMENT_RUNBOOK.md`
- `docs/architecture/TOPOCORE_V6_PHASE_4_CHECKPOINT_RUNTIME_ADJACENT_APPROVAL.md`
- `docs/architecture/TOPOCORE_V6_STILL_DISABLED_ADVISORY_BOUNDARY.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 31:
  - `9ea8e07 Docs: review TopoCore v6 phase 3 go-no-go`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 complete:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-30
- validation from Sprint 30:
  - `pytest` passed with `656` tests
- no runtime behavior was intentionally changed through Sprint 30

## 3. Phase 4 Definition

Phase 4 definition:

- Phase 4 - Controlled Advisory Shadow Experiment Planning

Scope:

- plan a controlled advisory-only experiment
- keep v5/TKYA as the only product decision path
- keep TopoCore v6 advisory non-user-visible
- require any future advisory path to be disabled by default
- require any future advisory path to fail safely to v5-only behavior
- limit any future advisory output to sanitized internal artifacts only
- require explicit approval after this docs-only sprint before any runtime-adjacent implementation

Clarifications:

- Phase 4 is not canary
- Phase 4 is not route migration
- Phase 4 is not v5 replacement
- Phase 4 is not fix migration
- Phase 4 is not external or community runtime work

## 4. Phase 4 Sprint Limit

Hard planning limit:

- `2` to `3` sprints maximum before another checkpoint

Proposed shape:

Sprint 31 - Phase 4 Scope and Controlled Advisory Shadow Experiment Plan

- docs-only
- define scope, gates, and experiment boundaries

Sprint 32 - Controlled Advisory Experiment Runbook and Evidence Checklist

- docs and test planning
- define exact runbook, evidence capture, rollback, and PR/CI validation expectations
- no activation

Sprint 33 - Optional Runtime-Adjacent Approval Gate

- checkpoint only
- decide whether any still-disabled runtime-adjacent implementation is allowed
- no canary or route migration

Rules:

- Phase 4 must not expand beyond this without explicit reset

## 5. Phase 4 Allowed Scope

Allowed:

- docs-only experiment planning
- exact env-gate design
- kill-switch design
- evidence checklist
- sanitized artifact review checklist
- manual/local evidence requirements
- PR/CI validation plan
- rollback plan
- stop/go criteria
- no-op and failure-isolation requirements
- future still-disabled advisory path proposal

## 6. Phase 4 Hard Boundaries

Not allowed:

- canary
- route migration
- v5 replacement
- fix migration
- patch application
- patch behavior change
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

## 7. Controlled Advisory Experiment Definition

Future controlled advisory experiment means:

- disabled by default
- enabled only by explicit environment flag in an approved branch or PR validation context
- v5/TKYA remains primary
- v6 advisory runs only after a sanitized summary bundle exists
- v6 advisory cannot alter routing, comments, checks, patch behavior, or final user-visible result
- v6 advisory failure cannot fail the main command
- v6 advisory output is captured only as sanitized internal artifact
- no artifact is published to PR comments/checks by default

Important:

- this is a future definition only
- Sprint 31 does not implement it

## 8. Required Future Environment Gates

Future design targets:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0`
- `RB_TOPOCORE_V6_SHADOW_REQUIRE_LOCAL=0|1`
- `RB_TOPOCORE_V6_SHADOW_MAX_FIXTURES=<optional>`
- `RB_TOPOCORE_V6_SHADOW_OUTPUT_MODE=summary|json`

Rules:

- defaults must be safe
- disabled means no-op
- missing `topocore_v6` means v5-only
- fail-closed must not be the default for GitHub runtime
- artifact persistence must remain off by default
- raw or internal output must remain forbidden

## 9. Evidence Requirements Before Any Activation

Before any future controlled advisory experiment can be activated, require:

- manual/local harness evidence exists
- disabled skeleton guard tests pass
- forbidden-output scans pass
- default CI remains green without private `topocore_v6`
- no `topocore_v6` import at runtime module import time
- no raw or internal output appears
- no `decide_raw` call
- no patch or fix behavior change
- no user-visible output change
- rollback and kill-switch instructions exist
- explicit human approval exists

## 10. Advisory Artifact Review Checklist

For each future advisory artifact, the reviewer must confirm:

- artifact is sanitized
- no forbidden fields exist
- v5 primary remains authoritative
- v6 advisory is non-user-visible
- decision-diff severity is recorded
- go/no-go hint is present
- failure category is sanitized
- fix-like cases do not authorize patching
- high-severity mismatch is reviewed
- v6 more permissive than v5 is blocked or escalated
- private dependency or install issues are recorded

## 11. Stop Conditions

Future Phase 4 work must stop or downgrade to docs-only if:

- `topocore_v6` becomes required in default CI
- runtime output changes
- PR comments/checks change
- v6 failure can fail the main command
- forbidden raw or internal output appears
- `decide_raw` is called or exposed
- patch/fix behavior changes
- v6 advisory appears more permissive in sensitive, fix, or blocked cases
- high-severity decision-diff mismatches remain unresolved
- branch discipline or validation becomes unstable
- any external or community behavior change is required

## 12. Repository Boundary Confirmation

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

## 13. Phase 4 Non-Goals

- no runtime implementation in Sprint 31
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

## 14. Acceptance Criteria

Sprint 31 is complete only if:

- the new Phase 4 scope document exists
- it clearly states Sprint 31 is docs-only
- it defines Phase 4
- it limits Phase 4 to `2` to `3` sprints before checkpoint
- it defines allowed scope
- it defines hard boundaries
- it defines the controlled advisory experiment concept
- it defines future environment gate targets
- it defines evidence requirements before activation
- it defines an advisory artifact review checklist
- it defines stop conditions
- it confirms repository boundaries
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
