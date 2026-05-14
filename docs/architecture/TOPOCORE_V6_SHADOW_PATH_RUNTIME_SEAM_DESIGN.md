# TopoCore v6 Shadow Path Runtime Seam Design

## 1. Purpose

Sprint 27 defines the future runtime seam for a disabled advisory shadow path.

Current truth:

- Sprint 27 does not implement the seam
- Sprint 27 does not activate shadow mode
- Sprint 27 does not change GitHub runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains manual, local, and advisory only

This sprint is design-only. The goal is to define where a future disabled advisory path could later attach without changing current product behavior.

## 2. Current Phase Baseline

Current phase baseline:

- Phase 1 is complete: Controlled Migration Foundation, Sprints 16-22
- Phase 2 is complete: Shadow Readiness / Advisory Evidence Layer, Sprints 23-25
- Sprint 26 closed both phases and defined Phase 3
- Phase 3 is Disabled Advisory Shadow Path Preparation
- Phase 3 is limited to `3` to `4` sprints maximum
- Sprint 27 is the first Phase 3 sprint

Reference documents:

- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`
- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

## 3. Current Runtime Path to Protect

The current protected runtime path is:

`GitHub event`
-> `.github/workflows/repobrain.yml`
-> `action.yml`
-> `scripts/run_github.py`
-> `repobrain.github_flow.run_github_flow(...)`
-> command parsing
-> current v5/TKYA path
-> GitHub Models prompt/synthesis paths where applicable
-> patch/fix safety stack where applicable
-> markdown rendering
-> PR comment/check publication

Rules:

- this path must remain unchanged in Sprint 27
- any future shadow mode must not alter comments, checks, routes, patch behavior, or final decisions

## 4. Runtime Seam Candidate

Recommended future seam:

After RepoBrain has collected command context, PR metadata, retrieval or candidate data, verification/check signals, and LLM summaries, but before final product rendering.

Current primary path:

`RepoBrain context`
-> `v5/TKYA primary decision`
-> `existing product rendering`
-> `comments/checks`

Future advisory path:

`sanitized summary bundle`
-> `RepoBrainTopoCoreV6Adapter` preview
-> optional v6 advisory call
-> sanitized v6 advisory snapshot
-> decision-diff report
-> advisory artifact
-> internal/manual artifact only

Rules:

- v5 remains primary
- v6 does not influence final output
- v6 does not publish comments/checks
- v6 does not apply patches
- v6 does not change routing

## 5. Candidate Files for Future Seam

Likely future files where seam design may matter:

- `repobrain/github_flow.py`
  - likely future seam owner for collecting already-available RepoBrain context before rendering
- `repobrain/tky_local.py`
  - current local v5/TKYA bridge that remains primary and must not be replaced casually
- `repobrain/tky_engine.py`
  - current v5/TKYA contract surface that helps define what primary snapshots look like
- `repobrain/topocore_v6_adapter.py`
  - future safe adapter preview builder for sanitized advisory input shaping
- `repobrain/topocore_v6_decision_diff.py`
  - future safe comparator for primary vs advisory snapshots
- `repobrain/topocore_v6_advisory_artifact.py`
  - future safe in-memory artifact builder for sanitized advisory records
- `scripts/validate_topocore_v6_local.py`
  - current manual/local-only proving ground for advisory shape, diff, and artifact behavior

Important:

- the seam is not implemented today
- future work must not import `topocore_v6` into runtime modules casually
- if any future `topocore_v6` import is required, it must remain isolated behind an optional, manual, or advisory boundary

## 6. Sanitized Summary Bundle Boundary

The future runtime seam may accept:

Allowed:

- command
- task type
- safe query summary
- safe candidate IDs
- score hints
- PR context summary
- evidence summary
- unknowns summary
- risk hints
- verification result summaries
- review draft summary
- fix governance summary
- `no_patch` reason if applicable

Forbidden:

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
- `compression_stats`
- raw trace
- governance internals
- event internals
- artifact internals
- `decide_raw` output

## 7. Advisory Snapshot Boundary

Future sanitized v6 advisory snapshot may contain:

Allowed:

- `task_type`
- `status`
- `action`
- safe selected chunk IDs if available
- safe reason code
- confidence hint
- `needs_more_information` reason
- blocked reason
- fixture/run label if manual

Forbidden:

- raw TopoCore result object
- `decide_raw`
- internal traces
- `compression_stats`
- governance diagnostics
- raw query
- raw code
- raw evidence payloads

## 8. No-Op and Kill-Switch Behavior

Design-only future environment controls:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0`
- `RB_TOPOCORE_V6_SHADOW_MAX_FIXTURES=<optional future limit>`

Rules:

- default must be disabled
- disabled means complete no-op
- missing `topocore_v6` means v5-only behavior
- v6 failure must not fail the main RepoBrain command
- v6 failure must not block comment/check publication
- v6 failure must not trigger patch/fix behavior
- fail-closed must not be enabled by default for GitHub runtime
- these envs are design-only in Sprint 27

## 9. Failure Isolation

The future advisory path must isolate failures as follows:

- adapter error -> sanitized advisory failure only
- missing dependency -> v5-only fallback
- v6 platform error -> sanitized advisory failure only
- forbidden output issue -> block artifact, keep v5-only
- decision-diff high severity -> mark advisory artifact blocked, do not alter runtime
- artifact build failure -> sanitized advisory failure only
- any exception -> sanitized category, no raw exception dump

## 10. Artifact Handling

Artifact handling rules:

- Sprint 27 does not introduce artifact persistence
- future shadow artifacts must be disabled by default
- future artifact persistence must require explicit opt-in
- no advisory artifact may be posted to PR comments/checks
- no artifact may contain raw query, code, diff, secrets, or internals
- manual/local artifact behavior from Sprint 25 remains the only current artifact integration

## 11. Runtime-Seam Acceptance Gates for Future Sprint 28

The following must be true before Sprint 28 can implement any disabled skeleton:

- Sprint 27 seam design is accepted
- no change to current runtime outputs
- explicit env-gated disabled default
- no private dependency in default CI
- no `topocore_v6` import at module import time in runtime modules
- kill switch is defined
- no-op tests are planned
- forbidden-output tests are planned
- failure-isolation tests are planned
- no fix-path behavior change
- no PR/check/comment publication change

## 12. Relationship to Future Sprint 28

Possible next step:

- Sprint 28 - Disabled Advisory Path Skeleton

Allowed only if approved:

- hard-disabled no-op skeleton
- no live v6 call by default
- no user-visible output changes
- no default CI private dependency
- no shadow activation by default

Not allowed:

- canary
- route migration
- v5 replacement
- fix migration
- patch behavior change

## 13. Explicit Non-Goals for Sprint 27

- no runtime code changes
- no tests required unless a documentation validation issue requires it
- no shadow-mode implementation
- no disabled advisory skeleton implementation
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

## 14. Acceptance Criteria

Sprint 27 is complete only if:

- the new runtime seam design document exists
- it clearly states Sprint 27 is design-only
- it clearly states shadow mode is not activated
- it clearly keeps v5/TKYA as the active primary runtime
- it defines the future runtime seam
- it identifies candidate files without changing them
- it defines sanitized summary bundle boundaries
- it defines advisory snapshot boundaries
- it defines no-op and kill-switch behavior
- it defines failure isolation
- it defines artifact handling
- it defines acceptance gates for Sprint 28
- it introduces no runtime behavior changes
