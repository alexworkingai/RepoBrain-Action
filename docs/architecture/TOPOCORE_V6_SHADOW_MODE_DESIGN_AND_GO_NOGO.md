# TopoCore v6 Shadow Mode Design and Go/No-Go Criteria

## 1. Purpose

Sprint 23 defines shadow-mode design and go/no-go criteria only.

Current truth:

- it does not activate shadow mode
- it does not wire TopoCore v6 into GitHub runtime
- it does not replace current embedded v5/TKYA
- it does not change command behavior
- it prepares the decision framework for a later advisory-only experiment

See also:

- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_PATH_RUNTIME_SEAM_DESIGN.md`

This sprint is documentation only. It exists to define when a future shadow-mode experiment may be considered and what evidence must exist before that happens.

## 2. Current Baseline

Current baseline summary:

- Sprint 16 defined the v5 -> v6 migration blueprint
- Sprint 17 defined GitHub Models LLM summary contracts
- Sprint 18 added the inert adapter skeleton
- Sprint 19 added fake and stub compatibility tests
- Sprint 20 planned the local/private validation harness
- Sprint 21 added the manual/disabled local validation harness
- Sprint 22 added the sanitized decision-diff helper and strategy
- current `main` still uses embedded v5/TKYA as the active runtime
- TopoCore v6 remains future, manual, local, and advisory only

Reference documents:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

## 3. Definition of Shadow Mode

Future shadow mode means:

- v5/TKYA remains the only active product decision path
- v6 receives sanitized advisory inputs in parallel
- v6 output is never shown directly to users
- v6 output never changes PR comments, check runs, patch behavior, routing, or final user-visible decisions
- v6 advisory results are captured only as sanitized internal or manual artifacts
- decision-diff reports compare v5 primary and v6 advisory snapshots

Shadow mode is not:

- canary
- route migration
- v5 replacement
- external/public behavior

## 4. Preconditions Before Any Future Shadow Mode

The following must be true before any shadow-mode implementation work can begin:

- current v5/TKYA baseline is green
- adapter skeleton is stable
- stub compatibility tests pass
- manual/local v6 validation harness passes in at least one developer environment
- decision-diff report format is accepted
- forbidden-output scans pass
- no `topocore_v6` dependency is required by default CI
- no raw or internal v6 data is exposed
- a clear rollback/disable switch is defined
- explicit human approval is given before any runtime-adjacent work

## 5. Manual Evidence Threshold

Minimum evidence required before shadow-mode implementation can even be proposed:

- at least `3` manual/local validation runs
- at least one ask-like fixture
- at least one review-like fixture
- at least one weak-context fixture
- at least one blocked/safety fixture
- at least one fix-like governance fixture
- zero forbidden-output leaks
- zero `decide_raw` exposure
- zero patch authorization from the v6 advisory path
- all high-severity decision-diff mismatches reviewed and classified
- all private dependency/install issues documented

## 6. Go Criteria

Shadow-mode implementation may be considered only if:

- default CI remains independent of private TopoCore v6
- all existing tests remain green
- manual validation evidence exists
- decision-diff output is sanitized and stable
- v6 advisory is more conservative or aligned in safety-sensitive cases
- no v6 advisory result authorizes patch application
- no v6 advisory result claims safe-to-merge, security verdict, approval, or rejection
- no forbidden internals appear in logs, artifacts, reports, comments, or checks
- a kill switch is specified
- the implementation plan is limited to advisory-only collection

## 7. No-Go Criteria

Shadow-mode implementation must be blocked if:

- v6 appears more permissive than v5 in blocked, fix, or security-sensitive cases
- decision-diff reports contain high-severity unresolved mismatches
- any forbidden output appears
- `decide_raw` is exposed or called outside trusted local development
- private dependency would become required in default CI
- any runtime path would change visible user output
- any patch/fix behavior would change
- any workflow or `action.yml` change is required before design approval
- missing `topocore_v6` causes default CI failure
- failure categories are unclear or unclassified

## 8. Future Shadow-Mode Architecture Shape

Conceptual future architecture:

`GitHub event / PR context`
-> `current RepoBrain runtime`
-> `v5/TKYA primary decision`
-> `sanitized summary bundle`
-> `future optional v6 advisory call`
-> `sanitized v6 advisory snapshot`
-> `decision-diff report`
-> `internal/manual artifact only`

Architecture rules:

- v5 remains primary
- v6 does not influence output
- v6 does not apply patches
- v6 does not publish comments/checks
- v6 does not call GitHub Models
- v6 does not scan GitHub
- RepoBrain remains the owner of safe product mapping

## 9. Artifact and Storage Policy

Allowed future artifacts:

- sanitized decision-diff report
- fixture name
- command type
- safe reason code
- safe route/status/action category
- safe selected chunk id overlap
- sanitized failure category

Forbidden future artifacts:

- raw query text
- raw code
- raw diff content
- raw prompts
- system prompts
- secrets
- tokens
- api keys
- private keys
- `.env` contents
- `decide_raw` output
- `compression_stats`
- raw traces
- governance internals
- event internals
- artifact internals

## 10. Kill Switch and Runtime Safety

Future kill-switch principles:

- shadow mode must be disabled by default
- one environment flag should disable all v6 advisory behavior immediately
- missing `topocore_v6` must degrade to v5-only behavior
- v6 failure must never fail the main RepoBrain command
- v6 failure must never block PR comment/check publication
- v6 failure must never trigger patch/fix behavior
- v6 failure must be recorded only as sanitized internal status

Suggested future environment names:

- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`

These names are design-only in Sprint 23 and must not be implemented yet.

## 11. Failure Taxonomy

Future shadow-mode analysis should reuse and extend the established categories:

- LLM summary issue
- RepoBrain adapter issue
- insufficient GitHub data
- user request ambiguity
- v5/v6 semantic mismatch
- TopoCore v6 platform issue
- policy/security block
- private dependency/install issue
- forbidden-output issue
- shadow-mode infrastructure issue

Rules:

- no infinite retry loop
- no automatic route migration based on one run
- high-severity mismatches require human review

## 12. Relationship to Canary

- canary is later than shadow mode
- Sprint 23 does not design canary in detail
- no canary should be considered until shadow mode has stable evidence
- canary would be runtime-affecting and requires separate approval

## 13. Explicit Non-Goals for Sprint 23

- no runtime code changes
- no shadow-mode implementation
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

## 14. Acceptance Criteria

Sprint 23 is complete only if:

- the new shadow-mode design/go-no-go document exists
- it clearly states shadow mode is not activated
- it clearly keeps v5/TKYA as the active primary runtime
- it defines shadow mode precisely
- it defines preconditions
- it defines manual evidence threshold
- it defines go criteria
- it defines no-go criteria
- it defines artifact/storage boundaries
- it defines kill-switch principles
- it defines relationship to canary
- it does not claim v6 is wired into runtime
- it introduces no runtime behavior changes
