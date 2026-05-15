# TopoCore v6 Phase 6 Controlled Advisory Experiment Proposal

## 1. Purpose

Sprint 36 creates a Phase 6 proposal only.

Current truth:

- Sprint 36 is docs-only
- Sprint 36 does not implement a controlled advisory experiment
- Sprint 36 does not activate advisory shadow mode
- Sprint 36 does not create canary behavior
- Sprint 36 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint exists to define what a future controlled advisory experiment proposal would mean while preserving every Phase 5 safety boundary and keeping the current runtime untouched.

See also:

- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 36:
  - `d2cb8f7 Add TopoCore v6 advisory boundary guard checkpoint`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 complete:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-30
- Phase 4 complete:
  - Controlled Advisory Shadow Experiment Planning, Sprints 31-33
- Phase 5 complete:
  - Still-Disabled Runtime-Adjacent Advisory Integration Boundary, Sprints 34-35
- validation from Sprint 35:
  - `pytest` passed with `725` tests
- no runtime behavior was intentionally changed through Sprint 35

## 3. Phase 6 Definition

Phase 6 definition:

- Phase 6 name:
  - Controlled Advisory Experiment Proposal
- purpose:
  - propose how the project could move from a still-disabled advisory boundary toward a controlled advisory experiment
  - define exactly what must remain disabled
  - define what evidence is required before any implementation
  - define what would be allowed in a future experiment branch
  - define what remains blocked

Current truth:

- Phase 6 is proposal-only until separately approved
- Phase 6 is not activation
- Phase 6 is not canary
- Phase 6 is not route migration
- Phase 6 is not v5 replacement
- Phase 6 is not fix migration

## 4. Phase 6 Recommended Limit

Hard limit:

- `1` to `2` sprints maximum before another checkpoint

Suggested shape:

- Sprint 36:
  - Phase 6 Controlled Advisory Experiment Proposal
  - docs-only proposal
  - define exact experiment shape, scope, gates, and evidence requirements
- Sprint 37:
  - Phase 6 Approval / No-Go Checkpoint
  - decide whether a controlled advisory experiment implementation branch is allowed
  - no activation by default
  - no canary
  - no route migration

Constraint:

- Phase 6 must not expand beyond `2` sprints without explicit reset

## 5. What Is Already Proven

The following is already proven by accepted work:

- v5/TKYA remains the active primary runtime
- TopoCore v6 is not wired into live runtime
- adapter skeleton exists
- decision-diff helper exists
- advisory artifact helper exists
- manual/local validation harness exists
- disabled shadow skeleton exists
- still-disabled advisory boundary exists
- boundary guard tests exist
- default disabled/no-op behavior is tested
- forbidden input/output blocking is tested
- no `topocore_v6` dependency is required in default CI
- disabled/default harness skips cleanly
- validation remains green
- no user-visible output has changed

## 6. What Is Not Proven

The following remains not proven:

- no real live advisory experiment has run
- no real GitHub runtime advisory path is wired
- no real PR runtime v5/v6 comparison evidence exists
- no real `topocore_v6` call exists in GitHub runtime
- no canary is proven
- no route migration is proven
- no v5 replacement path is proven
- no fix migration is proven
- no private dependency CI strategy is approved
- no production TopoCore v6 package/install strategy is approved
- no external/community runtime change is approved
- no user-visible product impact is validated because none has been introduced

## 7. Proposed Controlled Advisory Experiment Shape

Future experiment concept:

- v5/TKYA remains the only product decision path
- controlled advisory path is disabled by default
- advisory path can be enabled only in an explicitly approved experiment branch/context
- v6 advisory remains non-user-visible
- v6 advisory cannot alter command routing
- v6 advisory cannot alter PR comments
- v6 advisory cannot alter check-runs
- v6 advisory cannot alter patch/fix behavior
- v6 advisory failure cannot fail the main command
- missing `topocore_v6` must fall back to v5-only
- artifacts must be sanitized
- artifacts must not be published to users
- `decide_raw` remains forbidden

## 8. Proposed Experiment Branch Rules

Future branch rules:

- experiment must run on a dedicated branch
- experiment branch must not be `main`
- experiment branch must not be released as public external behavior
- experiment must not modify `repobrain-community`
- experiment must not change external install templates
- experiment must not require `topocore_v6` in default CI
- experiment must include rollback instructions
- experiment must include clear env gating
- experiment must include no-op tests
- experiment must include forbidden-output tests
- experiment must include failure-isolation tests

## 9. Proposed Environment Gates

Future env gate proposal:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0`
- `RB_TOPOCORE_V6_SHADOW_REQUIRE_LOCAL=0|1`
- `RB_TOPOCORE_V6_SHADOW_OUTPUT_MODE=summary|json`
- `RB_TOPOCORE_V6_SHADOW_EXPERIMENT_LABEL=<safe-label>`
- `RB_TOPOCORE_V6_SHADOW_MAX_CASES=<optional numeric limit>`

Rules:

- default disabled
- disabled means complete no-op
- artifacts default off
- fail-closed default is `0`
- missing dependency means v5-only
- no `decide_raw` under any mode
- no artifact publication by default
- output mode must remain sanitized

## 10. Proposed Experiment Evidence

Required future evidence:

- baseline commit
- experiment branch
- env flags used
- command type
- v5 primary safe snapshot
- v6 advisory safe snapshot
- decision-diff severity
- advisory artifact go/no-go hint
- failure category if any
- forbidden-output scan result
- missing dependency behavior
- rollback test result
- reviewer decision

Forbidden evidence:

- raw query
- raw code
- raw diff
- prompt
- system prompt
- hidden prompt
- secrets
- tokens
- api keys
- private keys
- `.env` contents
- `decide_raw`
- `compression_stats`
- raw traces
- governance internals
- event internals
- artifact internals

## 11. Proposed Stop Conditions

Future experiment proposal must stop if:

- default CI requires private `topocore_v6`
- disabled mode is not no-op
- v6 failure can fail main command
- user-visible output changes
- PR comments/checks change
- patch/fix behavior changes
- forbidden raw/internal output appears
- `decide_raw` is called or exposed
- v6 advisory appears more permissive than v5 in blocked/fix/security-sensitive cases
- high-severity decision-diff mismatch remains unresolved
- artifact is persisted or published without explicit approval
- branch discipline or validation becomes unstable
- external/community changes become necessary

## 12. Proposed Rollback Requirements

Rollback requirements:

- disable `RB_TOPOCORE_V6_SHADOW_ENABLED`
- unset all experiment-only env flags
- confirm v5-only behavior
- rerun validation
- rerun disabled/default harness check
- confirm no user-visible output changes
- document rollback reason
- do not attempt automatic recovery by enabling broader behavior

## 13. Approval Requirements for Any Future Implementation

Before any future implementation beyond proposal, require:

- Sprint 36 accepted
- Sprint 37 approval checkpoint accepted
- explicit human approval
- default CI green
- disabled/default harness check green
- no unresolved forbidden-output findings
- no unresolved high-severity boundary guard failures
- no runtime output changes
- no private dependency requirement in default CI
- exact sprint prompt with implementation scope

## 14. Phase 6 Decision Options

Possible outcomes for Sprint 37:

- Option A:
  - GO for controlled advisory experiment implementation branch
  - still disabled by default
  - non-user-visible
  - no canary
  - no route migration
  - no v5 replacement
  - no fix migration
- Option B:
  - GO for more docs/test planning only
  - no implementation
  - more evidence required
- Option C:
  - NO-GO
  - remain at still-disabled boundary
  - document blockers

## 15. Repository Boundary Confirmation

Repository boundaries:

RepoBrain-Action owns:

- primary/private GitHub runtime
- current v5/TKYA contract truth
- future v6 adapter around public facade
- GitHub Models LLM orchestration
- safe product-level output mapping
- tests/docs/regression guards
- manual/local advisory validation and artifact helpers
- disabled advisory skeleton and guard tests
- still-disabled advisory boundary and guard tests
- Phase 6 controlled advisory experiment proposal

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

## 16. Explicit Non-Goals for Sprint 36

Current non-goals:

- no runtime code changes
- no tests required unless a documentation validation issue requires it
- no implementation-adjacent code in Sprint 36
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
- no `create_topocore` call
- no `decide` call
- no `decide_external` call
- no `decide_raw` call
- no LLM provider change
- no GitHub Models prompt behavior change
- no `repobrain-community` change
- no live GitHub API usage
- no live GitHub Models usage
- no artifact disk write/upload/publish behavior
- no user-visible PR comment/check changes

## 17. Acceptance Criteria

Sprint 36 is complete only if:

- the new Phase 6 proposal document exists
- it clearly states Sprint 36 is docs-only
- it defines Phase 6
- it limits Phase 6 to `1` to `2` sprints before checkpoint
- it defines what is already proven
- it defines what is not proven
- it defines proposed experiment shape
- it defines proposed experiment branch rules
- it defines proposed env gates
- it defines evidence requirements
- it defines stop conditions
- it defines rollback requirements
- it defines approval requirements
- it defines Sprint 37 decision options
- repository boundaries are confirmed
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
