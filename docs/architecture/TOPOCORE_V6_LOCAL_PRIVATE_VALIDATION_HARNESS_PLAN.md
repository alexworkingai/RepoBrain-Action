# TopoCore v6 Local/Private Validation Harness Plan

## 1. Purpose

Sprint 20 defines the plan for a future manual and local validation harness.

Current truth:

- Sprint 20 does not implement the harness
- Sprint 20 does not wire TopoCore v6 into runtime
- Sprint 20 does not replace current v5/TKYA
- Sprint 20 does not require private TopoCore v6 in CI
- Sprint 20 prepares the next safe step after the stub compatibility tests

This sprint is planning only. It exists to define how RepoBrain-Action can later validate the existing adapter skeleton against a real local or private TopoCore v6 installation without introducing runtime risk.

See also:

- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`

## 2. Current Baseline

Current baseline summary:

- Sprint 16 defined the v5 -> v6 controlled migration blueprint
- Sprint 17 defined the GitHub Models LLM summary contract
- Sprint 18 added the inert `RepoBrainTopoCoreV6Adapter` skeleton
- Sprint 19 added fake and stub compatibility tests
- current `main` still uses embedded v5/TKYA as the active runtime
- TopoCore v6 is still a future local and private validation target only

Reference documents:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

## 3. Why a Local/Private Harness Is Needed

The current fake and stub tests prove adapter shape, but they do not prove compatibility with a real TopoCore v6 public facade.

Why the next step must be local and private first:

- fake and stub tests prove adapter shape but not real v6 facade compatibility
- real v6 validation requires access to private or local TopoCore v6
- CI must remain green without private dependency access
- validation must remain opt-in and manually triggered
- v5 must remain the active runtime until real evidence supports further migration

So the harness is a controlled evidence-gathering tool, not a runtime switch.

## 4. Harness Scope

The future harness should validate:

- importing `topocore_v6` only in manual and local mode
- creating TopoCore v6 through the public facade only
- passing adapter request preview data into a real v6-compatible request shape
- checking `decide()` for trusted integration output
- checking `decide_external()` for product-safe external output
- verifying no `decide_raw` output is shown or persisted
- verifying safe external result shape
- verifying expected outcomes for ask, review, and fix-like fixture payloads
- verifying blocked or `needs_more_information` outcomes for weak or unsafe inputs

## 5. Harness Non-Scope

The future harness must not:

- run in default CI
- change live GitHub runtime
- change `action.yml`
- change workflows
- change `RB_TKYA_BACKEND=v5`
- replace v5/TKYA
- run during normal user commands
- call GitHub Models
- call live GitHub APIs
- apply patches
- modify files
- create commits
- create branches
- create PRs
- expose `decide_raw` output
- expose governance internals, traces, compression stats, raw query text, raw code, secrets, or hidden prompts

## 6. Proposed Future Harness Shape

Suggested future files, not to be created in Sprint 20:

- `scripts/validate_topocore_v6_local.py`
- `tests/manual/test_topocore_v6_local_validation.py`

Suggested execution model:

- disabled by default
- runs only when explicitly invoked by a developer
- requires a local or private `topocore_v6` installation
- detects missing `topocore_v6` and exits with a clear skipped or manual-only message
- does not fail normal CI when `topocore_v6` is absent
- does not use network
- does not use live GitHub Models traffic
- uses local fixture payloads only

## 7. Proposed Environment Controls

Future opt-in controls:

- `RB_TOPOCORE_V6_LOCAL_VALIDATE=1`
- `RB_TOPOCORE_V6_REQUIRE_LOCAL=0|1`
- `RB_TOPOCORE_V6_VALIDATION_FIXTURES=<optional path>`
- `RB_TOPOCORE_V6_ALLOW_DECIDE_RAW=0`

Rules:

- `RB_TOPOCORE_V6_ALLOW_DECIDE_RAW` must default to `0`
- `decide_raw` must remain developer-only and must not be printed to user-facing output
- missing env opt-in means the harness does not run

## 8. Proposed Fixture Strategy

### A. Minimal ask fixture

- `task_type: ask`
- safe query
- one or more safe candidates
- evidence summary

### B. Review-like fixture

- `task_type: review`
- PR context summary
- evidence summary
- risk hints
- verification results

### C. Weak-context fixture

- missing evidence
- unknowns
- expected `needs_more_information` style outcome

### D. Blocked/safety fixture

- unsafe request intent or unsafe metadata
- expected blocked or stop style outcome

### E. Fix-like governance fixture

- fix draft summary
- no patch authorization
- localized target hints
- expected product-safe output only

## 9. Proposed Validation Matrix

| Fixture | Adapter input | Expected v6 call type | Expected safe outcome | Forbidden outputs | CI status |
|---|---|---|---|---|---|
| minimal ask | ask-style preview bundle with safe candidates | `decide()` and sanitized external view | bounded ask-ready outcome | `decide_raw`, `compression_stats`, `raw_trace`, `governance_internals`, `event_internals`, `artifact_internals`, `raw_query`, `raw_code`, secrets | manual/local only, not required for default CI |
| review-like | review-style preview bundle with PR context and verification signals | `decide()` and `decide_external()` | bounded review-safe output | `decide_raw`, `compression_stats`, `raw_trace`, `governance_internals`, `event_internals`, `artifact_internals`, `raw_query`, `raw_code`, secrets | manual/local only, not required for default CI |
| weak context | sparse preview bundle with unknowns and missing evidence | `decide_external()` | `needs_more_information` style outcome | `decide_raw`, `compression_stats`, `raw_trace`, `governance_internals`, `event_internals`, `artifact_internals`, `raw_query`, `raw_code`, secrets | manual/local only, not required for default CI |
| blocked/safety | unsafe or policy-blocked preview bundle | `decide_external()` | blocked or stop style outcome | `decide_raw`, `compression_stats`, `raw_trace`, `governance_internals`, `event_internals`, `artifact_internals`, `raw_query`, `raw_code`, secrets | manual/local only, not required for default CI |
| fix-like governance | fix-style preview bundle with no-patch governance signals | `decide_external()` | product-safe fix output with no patch authorization | `decide_raw`, `compression_stats`, `raw_trace`, `governance_internals`, `event_internals`, `artifact_internals`, `raw_query`, `raw_code`, secrets | manual/local only, not required for default CI |

## 10. Dependency Strategy

Dependency strategy for the next phase:

- TopoCore v6 remains private and local at this phase
- RepoBrain-Action default CI must not require private TopoCore v6 access
- no package dependency is added in Sprint 20
- future manual validation may assume a developer has installed TopoCore v6 locally
- future CI or private dependency strategy remains separate and must be approved later

## 11. Expected Future Harness Outputs

Allowed harness outputs:

- compact pass or fail summary
- fixture name
- safe external status or action
- adapter compatibility status
- missing dependency skip message
- sanitized error category

Forbidden harness outputs:

- raw TopoCore internals
- `decide_raw` output
- raw query text in external output
- raw code payloads
- secrets
- tokens
- hidden prompts
- governance internals
- trace internals
- compression stats

## 12. Failure Taxonomy

The future local harness should reuse the existing failure taxonomy:

- LLM summary issue
- RepoBrain adapter issue
- insufficient GitHub data
- user request ambiguity
- v5/v6 semantic mismatch
- TopoCore v6 platform issue
- policy/security block
- private dependency/install issue

The harness should classify failures explicitly and stop in bounded fashion. It must not retry indefinitely.

Recommended future behavior:

- schema or adapter mismatch: stop and classify
- missing dependency: skip with manual-only message
- policy or security block: stop with blocked classification
- weak evidence: return `needs_more_information` classification

## 13. Relationship to Shadow Mode

This harness is not shadow mode.

It is a prerequisite before shadow mode should be considered.

Shadow mode should only be considered after:

- adapter skeleton exists
- stub compatibility tests pass
- manual or local v6 validation is proven
- decision diff strategy is defined

## 14. Explicit Non-Goals for Sprint 20

- no runtime code changes
- no harness implementation yet
- no manual test file yet unless purely documentation-linked and inactive
- no scripts added
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency
- no `topocore_v6` import
- no `create_topocore()` call
- no `decide()` call
- no `decide_external()` call
- no `decide_raw` exposure
- no v5 replacement
- no shadow mode
- no canary
- no route migration
- no fix migration
- no patch behavior change
- no LLM provider change
- no `repobrain-community` change

## 15. Acceptance Criteria

Sprint 20 is complete only if:

- the new local and private validation harness plan document exists
- it clearly states the harness is future, manual, and local only
- it clearly states Sprint 20 does not implement the harness
- it clearly states default CI must not require private TopoCore v6
- it defines proposed future env controls
- it defines fixture families
- it defines a validation matrix
- it defines allowed and forbidden harness outputs
- it defines dependency strategy
- it preserves v5/TKYA as the current active runtime
- it does not claim v6 is wired
- it introduces no runtime behavior changes
