# TopoCore v6 Fix-Lite Decision Path

## 1. Purpose

Sprint 45 decides and implements the guarded v6 Fix-Lite decision path.

Current truth:

- v5 remains the default and fallback
- GitHub runtime default behavior is unchanged
- patch application is not included
- v5 removal is not included

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 45:
  - `8c6f6da Expand TopoCore v6 backend review verify coverage`
- Sprint 43 introduced selectable backend support
- Sprint 44 expanded v6 backend to review and verify paths
- fix was not migrated before Sprint 45

## 3. Fix Path Decision

Sprint 45 decision:

- fix may use v6 only as guarded decision or governance input when `RB_TOPOCORE_BACKEND=v6` is explicitly selected
- patch application remains controlled by RepoBrain's existing safety stack
- no patch application is introduced
- no commit, branch, or PR creation is introduced
- no user-visible default behavior is changed

## 4. Fix-Lite Scope

Fix-Lite means:

- RepoBrain can send fix-like inputs through the existing v6 backend selector seam
- the v6 request remains product-safe and summary-only
- the v6 result is treated as conservative decision input only
- RepoBrain remains responsible for patch safety, rendering, and any later mutation workflow

Fix-Lite must not:

- apply a patch
- modify files
- create commits
- create branches
- create PRs
- claim autofix

Fix governance mapping:

- `no_patch_reason` and patch-safety notes flow through `scenario_summary`
- patch-governance reason codes and safety notes contribute to `risk_summary`

## 5. Summary Mapping

Fix summary mapping to real v6 policy keys:

- `evidence_summary`
- `bit_matrix_summary`
- `verification_summary`
- `project_audit_summary`
- `risk_summary`
- `scenario_summary`

Current rule:

- raw diff, raw code, patch body, prompts, secrets, tokens, private keys, and `decide_raw` are excluded from the v6 policy payload

## 6. Safe Decision Normalization

Extracted v6 fields:

- `status`
- `action`
- `reference_hash`
- `selected_count`
- `blocked`
- `confidence_band`
- `message_code`

Conservative fix markers:

- `patch_authorized=false`
- `patch_applied=false`
- `files_modified=false`
- `branch_created=false`
- `commit_created=false`
- `pr_created=false`

Current note:

- these markers are internal runtime metadata in the local selector path, not a new user-facing fix contract

## 7. Fallback Behavior

Current fallback behavior:

- default backend remains v5
- missing v6 dependency falls back to v5 by default
- strict local v6 failure happens only with `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`
- no default CI private dependency is introduced

## 8. Explicit Non-Claims

Sprint 45 does not claim:

- patch applied
- autofix
- file modified
- branch created
- PR created
- commit created
- safe to merge
- security approved
- PR approved or rejected

## 9. Sprint 46 Target

Sprint 46 target:

- Sprint 46 - v6 Default Lab Runtime and v5 Fallback Policy

Expected scope:

- decide whether v6 becomes the default for lab or runtime
- keep v5 fallback or mark v5 deprecated
- do not remove v5 yet unless explicitly approved
- confirm command coverage across ask, review, verify, and fix-lite

## 10. Non-Goals

Current non-goals:

- no v5 removal
- no workflow or `action.yml` change
- no default CI private dependency
- no `decide_raw`
- no patch application
- no commit, branch, or PR creation
- no PR, check, or comment behavior change by default
- no `repobrain-community` change

See also:

- `docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md`
- `docs/architecture/TOPOCORE_V6_REVIEW_VERIFY_BACKEND_EXPANSION.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
- `docs/architecture/TOPOCORE_V6_DEFAULT_LAB_RUNTIME_POLICY.md`
