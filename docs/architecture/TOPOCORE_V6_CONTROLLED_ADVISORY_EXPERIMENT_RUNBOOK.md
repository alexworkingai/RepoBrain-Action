# TopoCore v6 Controlled Advisory Experiment Runbook

## 1. Purpose

Sprint 32 defines the controlled advisory experiment runbook and evidence checklist.

Current truth:

- Sprint 32 is docs-only
- Sprint 32 does not implement or activate advisory shadow mode
- Sprint 32 does not create a canary
- Sprint 32 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only

This sprint exists to operationalize the Phase 4 planning into a future runbook and evidence checklist without crossing into live runtime behavior.

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 32:
  - `f3bce78 Docs: define TopoCore v6 phase 4 scope`
- Phase 1 complete:
  - Controlled Migration Foundation, Sprints 16-22
- Phase 2 complete:
  - Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Phase 3 complete:
  - Disabled Advisory Shadow Path Preparation, Sprints 27-30
- Phase 4 started docs-only in Sprint 31
- validation from Sprint 31:
  - `pytest` passed with `656` tests
- no runtime behavior was intentionally changed through Sprint 31

## 3. Phase 4 Context

See:

- `docs/architecture/TOPOCORE_V6_PHASE_4_SCOPE_AND_CONTROLLED_ADVISORY_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_PHASE_3_REVIEW_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_DISABLED_ADVISORY_PATH_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_PATH_GUARD_TESTS.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_PATH_RUNTIME_SEAM_DESIGN.md`

Context summary:

- Sprint 31 defined Phase 4 scope
- Sprint 32 operationalizes that planning into a runbook and evidence checklist
- Sprint 32 still does not authorize activation

## 4. Controlled Advisory Experiment Definition

Future controlled advisory experiment means:

- disabled by default
- explicitly enabled only in an approved validation context
- v5/TKYA remains the only product decision path
- v6 advisory is non-user-visible
- v6 advisory output cannot alter route, comments, checks, patch behavior, or final response
- missing `topocore_v6` falls back to v5-only
- v6 failure cannot fail the main RepoBrain command
- evidence is sanitized and reviewed by humans before any next step

Clarifications:

- controlled advisory experiment is not canary
- controlled advisory experiment is not route migration
- controlled advisory experiment is not v5 replacement
- controlled advisory experiment is not fix migration

## 5. Required Experiment Preconditions

Before any future controlled advisory experiment can run, require:

- Sprint 32 runbook accepted
- default CI green
- disabled/default local harness check passes
- disabled advisory skeleton guard tests pass
- `topocore_v6` is not required in default CI
- no `topocore_v6` import at runtime module import time
- all advisory path flags default to safe values
- rollback/disable procedure exists
- artifact review checklist exists
- forbidden-output scan rules exist
- human approval exists for the specific experiment branch or context

## 6. Future Environment Gate Checklist

Future environment gates are design targets only:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0`
- `RB_TOPOCORE_V6_SHADOW_REQUIRE_LOCAL=0|1`
- `RB_TOPOCORE_V6_SHADOW_OUTPUT_MODE=summary|json`
- `RB_TOPOCORE_V6_SHADOW_MAX_FIXTURES=<optional>`

Rules:

- all defaults must be safe
- disabled means complete no-op
- artifacts default off
- fail-closed default is `0`
- missing dependency means v5-only
- no `decide_raw` under any mode
- no artifact publication by default

## 7. Operator Runbook

Future operator procedure:

Step 0 - Confirm baseline

- confirm `main` commit
- confirm clean branch
- confirm validation is green
- confirm experiment branch is approved

Step 1 - Confirm environment

- confirm `topocore_v6` availability only in approved context
- confirm default CI does not require it
- confirm flags are explicitly set only for the experiment

Step 2 - Run disabled/default checks

- verify no-op behavior when disabled
- verify main command behavior is unchanged

Step 3 - Run manual/local validation

- run the existing local validation harness
- collect sanitized summary only
- no raw logs or raw artifacts

Step 4 - Run advisory experiment context

- enabled only in approved branch or context
- v5 remains primary
- v6 advisory remains non-user-visible
- collect sanitized advisory artifact only

Step 5 - Review artifacts

- apply the advisory artifact review checklist
- classify findings
- record stop/go outcome

Step 6 - Stop or continue

- stop immediately on any stop condition
- continue only after human approval

Important:

- Sprint 32 documents this procedure only
- Sprint 32 does not run the procedure

## 8. Evidence Capture Checklist

Required evidence categories:

- baseline commit
- validation status
- command type
- fixture or approved experiment context
- v5 primary safe snapshot
- v6 advisory safe snapshot
- decision-diff severity
- advisory artifact go/no-go hint
- failure category if any
- forbidden-output scan result
- dependency or install status
- reviewer decision
- stop/go outcome

Forbidden evidence:

- raw query text
- raw code
- raw diff
- raw prompts
- system prompts
- secrets
- tokens
- API keys
- private keys
- `.env` contents
- `decide_raw` output
- `compression_stats`
- raw traces
- governance internals
- event internals
- artifact internals

## 9. Advisory Artifact Human Review Checklist

For each future advisory artifact, the reviewer must confirm:

- `schema_version` is present
- `artifact_kind` is expected
- `mode` is manual/local or approved advisory context
- v5 primary snapshot is sanitized
- v6 advisory snapshot is sanitized
- decision-diff report is sanitized
- go/no-go hint is present
- severity is present
- failure category is sanitized
- no forbidden fields appear
- fix-like cases do not authorize patching
- v6 more permissive than v5 is escalated
- high-severity mismatches are blocked or reviewed
- dependency or install issues are documented
- artifact is not posted to PR comments/checks

## 10. Stop Conditions

Future advisory experiment must stop immediately if:

- forbidden raw/internal output appears
- `decide_raw` is called or exposed
- `topocore_v6` becomes required in default CI
- disabled mode is not a no-op
- missing dependency fails default flow
- v6 failure can fail the main command
- v6 output changes user-visible result
- PR comments/checks change
- patch/fix behavior changes
- v6 advisory is more permissive than v5 in blocked, fix, or security-sensitive cases
- high-severity decision-diff mismatch remains unresolved
- artifact is persisted or published without explicit approval
- workflow or `action.yml` changes are required unexpectedly
- branch discipline or validation becomes unstable

## 11. Rollback and Disable Procedure

Future rollback principles:

- set `RB_TOPOCORE_V6_SHADOW_ENABLED=0`
- unset all `RB_TOPOCORE_V6_SHADOW_*` flags
- remove experiment-only environment from branch or runner
- confirm v5-only behavior
- rerun validation
- confirm no user-visible output changes
- document rollback reason
- do not attempt automatic recovery by enabling broader behavior

## 12. Reviewer Roles

Future review roles:

- implementation owner
  - confirms branch and validation state
- runtime owner
  - confirms v5 behavior is unchanged
- safety reviewer
  - checks forbidden-output and stop conditions
- product reviewer
  - confirms no user-visible behavior change
- TopoCore/platform reviewer
  - reviews v6 advisory compatibility findings if needed

No approvals are automated in Sprint 32.

## 13. Experiment Report Template

Future manual report template:

- experiment label
- baseline commit
- branch/context
- command type
- fixture/context source
- validation status
- advisory status
- decision-diff severity
- go/no-go hint
- failure category
- reviewer notes
- stop/go decision
- next action

Important:

- this is a future manual report template only
- no report is generated automatically in Sprint 32

## 14. Phase 4 Remaining Work

Remaining planned Phase 4 work:

- Sprint 33 - Optional Runtime-Adjacent Approval Gate / Phase 4 Checkpoint

Purpose:

- decide whether any still-disabled runtime-adjacent implementation is allowed
- confirm whether Phase 4 remains docs-only or can move to a narrowly bounded implementation
- explicitly approve or block the next phase

## 15. Explicit Non-Goals for Sprint 32

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

## 16. Acceptance Criteria

Sprint 32 is complete only if:

- the new controlled advisory experiment runbook document exists
- it clearly states Sprint 32 is docs-only
- it defines the controlled advisory experiment procedure
- it defines required preconditions
- it defines the future env-gate checklist
- it defines the operator runbook
- it defines the evidence capture checklist
- it defines the human artifact review checklist
- it defines stop conditions
- it defines the rollback and disable procedure
- it defines reviewer roles
- it defines the future report template
- it preserves v5/TKYA as the active primary runtime
- it keeps TopoCore v6 disabled, manual, local, and advisory only
- it introduces no runtime behavior changes
