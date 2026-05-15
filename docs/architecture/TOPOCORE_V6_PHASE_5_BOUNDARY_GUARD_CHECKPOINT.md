# TopoCore v6 Phase 5 Boundary Guard Checkpoint

## 1. Purpose

Sprint 35 adds boundary guard tests and closes Phase 5.

Current truth:

- Sprint 35 does not activate advisory shadow mode
- Sprint 35 does not create canary behavior
- Sprint 35 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint exists to verify the still-disabled advisory boundary remains safe, inert, and non-user-visible, then record a checkpoint decision before any future experiment proposal can be considered.

See also:

- `docs/architecture/TOPOCORE_V6_PHASE_6_CONTROLLED_ADVISORY_EXPERIMENT_PROPOSAL.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`
- `docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 35:
  - `c656287 Add still-disabled TopoCore v6 advisory boundary`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 complete:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-30
- Phase 4 complete:
  - Controlled Advisory Shadow Experiment Planning, Sprints 31-33
- Phase 5 in review:
  - Still-Disabled Runtime-Adjacent Advisory Integration Boundary, Sprints 34-35
- validation from Sprint 34:
  - `pytest` passed with `690` tests
- no runtime behavior was intentionally changed through Sprint 34

## 3. Phase 5 Scope Recap

Phase 5 definition:

- Phase 5 - Still-Disabled Runtime-Adjacent Advisory Integration Boundary

Scope:

- add a still-disabled advisory boundary skeleton
- keep it no-op by default
- keep it non-user-visible
- add boundary-specific guard tests
- prove no dependency drift, no runtime wiring, and no artifact publication

Explicit non-scope:

- no live advisory activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no user-visible output change

## 4. Sprint 34 Review

Sprint 34 summary:

- added `repobrain/topocore_v6_advisory_boundary.py`
- added `tests/test_topocore_v6_advisory_boundary.py`
- added `docs/architecture/TOPOCORE_V6_STILL_DISABLED_ADVISORY_BOUNDARY.md`
- boundary is disabled by default
- enabled flag remains non-operational
- no `topocore_v6` import exists
- no v6 facade call exists
- no artifact persistence or publication exists
- no runtime wiring was introduced

Decision:

- accepted as still-disabled boundary skeleton

## 5. Sprint 35 Review

Sprint 35 summary:

- added boundary guardrail coverage
- verified no-op behavior
- verified explicit disabled override
- verified enabled-still-disabled behavior
- verified artifact flag safety
- verified fail-closed recording without behavior change
- verified forbidden input and forbidden output isolation
- verified no runtime wiring
- verified no `topocore_v6` dependency
- verified fix conservatism
- verified manual harness default behavior remains unchanged

Decision:

- accepted as guard layer for Phase 5

## 6. Evidence Ledger

| Evidence area | Supporting sprint/artifact | Status | Notes |
|---|---|---|---|
| v5/TKYA remains active primary runtime | Sprints 16-35 docs/tests | Confirmed | No runtime routing changes were introduced. |
| TopoCore v6 not wired into live runtime | Sprints 27-35 docs/tests | Confirmed | Shadow path and advisory boundary remain disconnected from protected runtime files. |
| advisory boundary exists | Sprint 34 module | Confirmed | `repobrain/topocore_v6_advisory_boundary.py` is present and isolated. |
| advisory boundary disabled by default | Sprint 34 module and Sprint 35 tests | Confirmed | Default mode remains safe no-op. |
| explicit disabled overrides artifact/fail-closed flags | Sprint 35 guard tests | Confirmed | Disabled mode still wins even when other flags are set. |
| enabled flag does not call real v6 | Sprint 34 module and Sprint 35 tests | Confirmed | Enabled mode remains still-disabled and non-operational. |
| no `topocore_v6` dependency in default CI | Sprints 18-35 validation | Confirmed | Validation remains green without private dependency access. |
| no `topocore_v6` import in runtime modules | Sprint 35 tests | Confirmed | Boundary and shadow modules import cleanly without v6 installed. |
| no artifact persistence or publication | Sprints 28, 34, and 35 tests/docs | Confirmed | Artifact writing and publishing remain absent. |
| forbidden input is blocked | Sprints 29 and 35 guard tests | Confirmed | Flat and nested forbidden fields are blocked. |
| forbidden output is blocked | Sprints 29 and 35 guard tests | Confirmed | Unsafe output-like payloads are rejected. |
| no runtime wiring into `github_flow`/`tky`/`tkya`/`action`/workflows | Sprint 35 guard tests | Confirmed | Protected runtime surfaces remain unchanged. |
| fix command remains conservative | Sprints 29, 34, and 35 tests | Confirmed | No patch authorization or repo action fields are introduced. |
| manual local harness still skips cleanly | Sprints 21-35 validation | Confirmed | Default local harness path still exits `0` with the same skip message. |
| validation remains green | Sprint 35 validation | Confirmed | Full repo validation passed. |

## 7. Gaps and Non-Proven Items

The following is not proven:

- no live advisory shadow experiment is proven
- no real GitHub runtime advisory path is wired
- no real PR runtime v5/v6 comparison evidence exists
- no real `topocore_v6` runtime call is proven in GitHub runtime
- no canary is proven
- no route migration is proven
- no v5 replacement path is proven
- no fix migration is proven
- no private dependency CI strategy is approved
- no production TopoCore v6 package/install strategy is approved
- no external/community runtime change is approved
- no user-visible product impact is validated because none was introduced

## 8. Phase 5 Decision

Decision:

- Phase 5 complete

GO for proposing a future controlled advisory experiment design branch only if it remains:

- disabled by default
- non-user-visible
- v5-primary
- no private dependency in default CI
- no artifact publication
- no PR comment/check changes
- no patch/fix behavior changes

NO-GO for:

- activation
- canary
- route migration
- v5 replacement
- fix migration
- user-visible output changes
- default-CI private dependency
- external/community runtime change

## 9. Next Phase Placeholder

High-level next possible phase only:

- Phase 6 - Controlled Advisory Experiment Proposal

Purpose:

- propose how to move from a still-disabled boundary to a controlled advisory experiment design
- define exact experiment branch rules
- define exact approval requirements
- define whether any runtime connection can be attempted while remaining non-user-visible

Limit:

- must be explicitly approved before starting
- should be limited to `1` to `2` sprints before checkpoint

Clarifications:

- Phase 6 is not automatically approved by Sprint 35
- Phase 6 must not mean canary or route migration
- Phase 6 must not mean v5 replacement
- Phase 6 must not mean fix migration

## 10. Phase 6 Entry Gates

Before Phase 6 may begin, require:

- Sprint 35 accepted
- validation green
- no runtime behavior changes through Phase 5
- no unresolved forbidden-output findings
- no unresolved boundary guardrail failures
- explicit human approval
- explicit statement whether Phase 6 remains docs-only or permits runtime-adjacent design/proposal
- no `topocore_v6` dependency in default CI
- v5-only behavior preserved

## 11. Stop Conditions

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
- any external/community behavior change is required

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
- still-disabled advisory boundary and guard tests

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

## 13. Explicit Non-Goals for Sprint 35

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

Sprint 35 is complete only if:

- boundary guardrail tests exist
- boundary no-op behavior is tested
- explicit disabled override is tested
- enabled-still-disabled behavior is tested
- artifact flag safety is tested
- fail-closed recording without behavior change is tested
- forbidden input/output isolation is tested
- no runtime wiring is verified
- no `topocore_v6` dependency is verified
- manual harness default behavior remains unchanged
- Phase 5 checkpoint document exists
- Phase 5 decision is explicit
- next phase is only a high-level placeholder
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
