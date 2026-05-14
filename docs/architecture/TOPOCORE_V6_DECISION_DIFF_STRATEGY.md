# TopoCore v6 Decision Diff Strategy

## 1. Purpose

Sprint 22 defines a safe decision-diff strategy for future v5 primary / v6 advisory analysis.

Current truth:

- this is not runtime shadow mode
- this is not canary
- this does not replace v5/TKYA
- this does not require TopoCore v6 in default CI

The purpose is to create a sanitized comparison format that can later support manual/local evidence gathering without exposing raw engine internals.

## 2. Relationship to Sprints 16-21

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`

Relationship:

- Sprint 16 defined the controlled migration strategy
- Sprint 17 defined the GitHub Models LLM summary contract
- Sprint 18 added the inert adapter skeleton
- Sprint 19 added stub compatibility tests
- Sprint 20 planned local/private validation harness
- Sprint 21 implemented the manual and disabled local validation harness
- Sprint 22 defines the future comparison strategy

See also:

- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`

## 3. Why Decision Diff Is Needed

- v5 remains the current primary decision layer
- v6 must first be evaluated as advisory and manual/local output
- raw decisions cannot be compared or exposed directly
- only sanitized snapshots should be compared
- diff reports are evidence for future shadow or canary decisions

## 4. Snapshot Inputs

### A. v5 primary snapshot

- `route`
- selected safe chunk ids
- verification gate summary
- execution mode
- safe reason codes
- `no_patch_reason` if applicable

### B. v6 advisory snapshot

- `status`
- `action`
- selected safe ids if available
- safe reason code
- `needs_more_information` reason
- blocked reason
- confidence hint

Raw engine internals are forbidden.

## 5. Diff Categories

- `aligned`
- `route_status_mismatch`
- `evidence_selection_mismatch`
- `v6_more_conservative`
- `v6_more_permissive`
- `needs_more_information_mismatch`
- `blocked_mismatch`
- `fix_governance_mismatch`
- `insufficient_data`
- `adapter_contract_issue`
- `platform_semantic_gap`

## 6. Severity Rules

- `info`: aligned or expected minor differences
- `low`: harmless wording or status difference
- `medium`: conservative mismatch, missing information, or evidence mismatch
- `high`: v6 more permissive than v5, fix-governance mismatch, or blocked/proceed disagreement

## 7. Forbidden Outputs

- `decide_raw`
- `compression_stats`
- `raw_trace`
- `governance_internals`
- `event_internals`
- `artifact_internals`
- `raw_query`
- `raw_code`
- secrets
- tokens
- hidden prompts

## 8. Relationship to Shadow Mode

- decision diff is a prerequisite for shadow mode
- Sprint 22 does not activate shadow mode
- future shadow mode should only be considered after:
  - manual/local v6 validation evidence
  - stable diff format
  - accepted mismatch taxonomy
  - clear stop/go criteria

## 9. Future Follow-Up

The next sprint may define:

- a shadow-mode design document, or
- manual/local decision-diff harness integration

Any follow-up should still avoid live GitHub runtime switching unless explicitly approved.
