# TopoCore v6 Review Verify Backend Expansion

## 1. Purpose

Sprint 44 expands selectable v6 backend coverage to review and verify-oriented lab paths.

Current truth:

- v5 remains the default and fallback
- GitHub runtime default behavior is unchanged
- fix migration is not included
- v5 removal is not included

## 2. Current Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 44:
  - `e0e8de5 Add selectable TopoCore v5 v6 backend`
- Sprint 43 introduced backend selection:
  - `RB_TOPOCORE_BACKEND=v5|v6`
  - `RB_TKYA_BACKEND` remains backward-compatible
- real local v6 backend smoke passed
- GitHub default runtime still used v5 before Sprint 44

## 3. Review/Verify Scope

Sprint 44 scope:

- review-oriented local or lab TKY decisions can continue to select v5 by default or v6 explicitly
- verify-oriented local or lab TKY decisions can now enter the same backend selector seam
- `repobrain/topocore_backend.py` carries the review or verify summary shaping for the v6 path
- `repobrain/tky_local.py` keeps the integration narrow by normalizing verify-like requests into a review-compatible engine request while preserving the requested command family for v6 policy shaping
- `repobrain/github_flow.py` was not changed
- default GitHub output behavior was not changed

## 4. Summary Mapping

Review and verify summary mapping to real v6 policy keys:

- `evidence_summary`
  - candidate counts
  - candidate ids
  - safe command-family markers
- `bit_matrix_summary`
  - candidate count
  - candidate ids only
- `verification_summary`
  - local verification capability flags
  - verification mode
  - safe command-family markers
- `project_audit_summary`
  - PR-context availability
  - PR or issue identifiers
  - changed-file and diff-hunk counts only
- `risk_summary`
  - bounded risk items for review or verify context
- `scenario_summary`
  - unknowns
  - scenario branches
  - command-family markers

Current rule:

- no raw diff, raw code, raw file contents, raw prompts, secrets, tokens, private keys, or `decide_raw` enter the v6 policy payload

## 5. Safe Decision Normalization

Extracted v6 fields:

- `status`
- `action`
- `reference_hash`
- `selected_count`
- `blocked`
- `confidence_band`
- `message_code`

Current rule:

- no raw v6 object is exposed
- `decide_raw` remains forbidden

## 6. Fallback Behavior

Current fallback behavior:

- default backend remains v5
- missing v6 dependency falls back to v5 by default
- strict local v6 failure happens only with `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`
- no default CI private dependency is introduced

## 7. Fix Exclusion

Current exclusion:

- fix is not migrated
- patch behavior is unchanged
- no commit, branch, or PR creation is introduced
- no safe-to-merge, security, approval, or rejection verdicts are introduced

## 8. Sprint 45 Target

Sprint 45 target:

- Sprint 45 - Fix Path Decision and Guarded v6 Fix-Lite Design

Expected scope:

- decide whether fix stays on v5, moves to v6 decision-only, or gets a guarded v6 fix-lite path
- still no patch application unless explicitly approved
- preserve the current patch safety stack

## 9. Non-Goals

Current non-goals:

- no v5 removal
- no workflow or `action.yml` change
- no default CI private dependency
- no `decide_raw`
- no fix migration
- no patch behavior change
- no PR, check, or comment behavior change by default
- no `repobrain-community` change

See also:

- `docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md`
- `docs/architecture/TOPOCORE_V6_REAL_ADAPTER_IMPLEMENTATION.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
- `docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md`
