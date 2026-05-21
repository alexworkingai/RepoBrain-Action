# TopoCore v6 Migration Documentation Index

## 1. Purpose

Sprint 38 consolidates documentation navigation after the Phase 6 NO-GO checkpoint.

Current truth:

- v6 is now the active authoritative runtime direction for RepoBrain issue-comment lab mode
- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1` is the intended current operating state
- v5 runtime execution has been removed
- Sprint 64 disabled v5 fallback by default
- Sprint 65 removed deprecated emergency v5 execution
- Sprint 66 removed orphaned vendor assets and residual TKYA runtime residue
- Sprint 67 removes final standalone v5 residue and closes the post-removal documentation gap
- Sprint 68 records final live sanity and closes the v6-only transition
- Sprint 69 starts the direct external repository pilot and removes `repobrain-community` from the working product architecture
- Sprint 70 validates the external command matrix on Elen-MCP
- Sprint 71 validates and improves external retrieval/evidence quality on Elen-MCP
- Sprint 72 productionizes external PR `verify` semantics on Elen-MCP
- Sprint 73 productizes external PR `fix` semantics as safe proposal/governance on Elen-MCP

This index exists to reduce documentation fragmentation and make the current migration track easy to navigate from baseline runtime through the latest checkpoint state.

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 38:
  - `b814bc1 Docs: record TopoCore v6 phase 6 no-go checkpoint`
- validation from Sprint 37:
  - `pytest` passed with `725` tests
- Phase 6 result:
  - NO-GO for immediate controlled advisory experiment implementation
- current state:
  - still-disabled advisory boundary exists
  - manual/local validation exists
  - no runtime advisory activation exists
  - no canary exists
  - no route migration exists
  - no fix migration exists
  - no v5 replacement exists

## 3. Phase Map

| Phase | Sprint range | Status | Main output | Runtime behavior changed? |
|---|---|---|---|---|
| Phase 1 - Controlled Migration Foundation | Sprints 16-22 | Complete | Adapter skeleton, validation harness plan, decision-diff foundation | No |
| Phase 2 - Shadow Readiness / Advisory Evidence Layer | Sprints 23-25 | Complete | Shadow-mode go/no-go framing, advisory artifact format, manual artifact harness | No |
| Phase 3 - Disabled Advisory Shadow Path Preparation | Sprints 27-30 | Complete | Runtime seam design, disabled shadow skeleton, guardrails, Phase 3 review | No |
| Phase 4 - Controlled Advisory Shadow Experiment Planning | Sprints 31-33 | Complete | Scope, runbook, and runtime-adjacent approval gate | No |
| Phase 5 - Still-Disabled Runtime-Adjacent Advisory Integration Boundary | Sprints 34-35 | Complete | Still-disabled advisory boundary and boundary guard checkpoint | No |
| Phase 6 - Controlled Advisory Experiment Proposal | Sprints 36-37 | Complete / NO-GO for implementation | Proposal plus explicit NO-GO checkpoint | No |
| Phase 7 - Stabilization and Evidence Collection | Sprints 38+ | Starting | Consolidated indexes, stabilization navigation, evidence-collection support | No |

## 4. Document Index by Phase

Baseline and current runtime:

- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

Phase 1:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`

Phase 2:

- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`

Phase 3:

- `docs/architecture/TOPOCORE_V6_PHASE_1_2_CLOSEOUT_AND_PHASE_3_SCOPE.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_PATH_RUNTIME_SEAM_DESIGN.md`
- `docs/architecture/TOPOCORE_V6_DISABLED_ADVISORY_PATH_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_PATH_GUARD_TESTS.md`
- `docs/architecture/TOPOCORE_V6_PHASE_3_REVIEW_GO_NOGO.md`

Phase 4:

- `docs/architecture/TOPOCORE_V6_PHASE_4_SCOPE_AND_CONTROLLED_ADVISORY_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_CONTROLLED_ADVISORY_EXPERIMENT_RUNBOOK.md`
- `docs/architecture/TOPOCORE_V6_PHASE_4_CHECKPOINT_RUNTIME_ADJACENT_APPROVAL.md`

Phase 5:

- `docs/architecture/TOPOCORE_V6_STILL_DISABLED_ADVISORY_BOUNDARY.md`
- `docs/architecture/TOPOCORE_V6_PHASE_5_BOUNDARY_GUARD_CHECKPOINT.md`

Phase 6:

- `docs/architecture/TOPOCORE_V6_PHASE_6_CONTROLLED_ADVISORY_EXPERIMENT_PROPOSAL.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

Phase 7:

- `docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
- `docs/architecture/TOPOCORE_V6_PRIVATE_DEPENDENCY_STRATEGY_PROPOSAL.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_EVIDENCE_COLLECTION_AND_PHASE_7_CHECKPOINT.md`
- `docs/architecture/TOPOCORE_V6_REAL_INTEGRATION_CONTRACT_LOCK.md`
- `docs/architecture/TOPOCORE_V6_REAL_ADAPTER_IMPLEMENTATION.md`
- `docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md`
- `docs/architecture/TOPOCORE_V6_REVIEW_VERIFY_BACKEND_EXPANSION.md`
- `docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_DEFAULT_LAB_RUNTIME_POLICY.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_RUNTIME_LAB_SWITCH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_DEPENDENCY_GATE.md`
- `docs/architecture/TOPOCORE_V6_WORKFLOW_DISPATCH_MEANINGFUL_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_IMPORT_BLOCKER_FIX.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_TKYA_ARTIFACT_OPTIONALITY.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_RUNTIME.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_GATE_PROPAGATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`
- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_READINESS_ASSESSMENT.md`
- `docs/architecture/TOPOCORE_V6_OBSERVATION_AND_V5_DEPRECATION_RUNWAY.md`
- `docs/architecture/TOPOCORE_V6_SPRINT_57_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_PR_PATH_AND_SCOPED_COMMAND_OBSERVATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_PR_OUTPUT_BACKEND_EVIDENCE_FIX.md`
- `docs/architecture/TOPOCORE_V6_SPRINT_60_FRESH_PR_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_CANDIDATE.md`
- `docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md`
- `docs/architecture/TOPOCORE_V6_OPT_IN_V5_OFF_SIMULATION.md`
- `docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md`
- `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`
- `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`
- `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`
- `docs/architecture/TOPOCORE_V6_FINAL_V6_ONLY_CLOSEOUT.md`
- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- `docs/architecture/SPRINT_69_EXTERNAL_REPO_PILOT_AND_COMMUNITY_REMOVAL.md`
- `docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md`
- `docs/architecture/SPRINT_71_EXTERNAL_RETRIEVAL_EVIDENCE_QUALITY.md`
- `docs/architecture/SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md`
- `docs/architecture/SPRINT_73_FIX_COMMAND_PRODUCT_PATH.md`

## 5. Recommended Reading Paths

Quick project state:

- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`
- `docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md`

Migration architecture:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`

Safety and advisory readiness:

- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_ARTIFACT_FORMAT_AND_SHADOW_PLAN.md`
- `docs/architecture/TOPOCORE_V6_PHASE_5_BOUNDARY_GUARD_CHECKPOINT.md`

GitHub runtime and issue-comment lab track:

- `docs/architecture/TOPOCORE_V6_GITHUB_RUNTIME_LAB_SWITCH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_DEPENDENCY_GATE.md`
- `docs/architecture/TOPOCORE_V6_WORKFLOW_DISPATCH_MEANINGFUL_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_IMPORT_BLOCKER_FIX.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_TKYA_ARTIFACT_OPTIONALITY.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_RUNTIME.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_GATE_PROPAGATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`

Deprecation readiness and post-transition assessment:

- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`
- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_READINESS_ASSESSMENT.md`
- `docs/architecture/TOPOCORE_V6_OBSERVATION_AND_V5_DEPRECATION_RUNWAY.md`
- `docs/architecture/TOPOCORE_V6_SPRINT_57_OBSERVATION_RESULTS.md`

Observation blocker fixes and PR/scoped-command evidence:

- `docs/architecture/TOPOCORE_V6_SPRINT_57_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_PR_PATH_AND_SCOPED_COMMAND_OBSERVATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_PR_OUTPUT_BACKEND_EVIDENCE_FIX.md`

Fresh PR observation and v6 lab default decision:

- `docs/architecture/TOPOCORE_V6_PR_OUTPUT_BACKEND_EVIDENCE_FIX.md`
- `docs/architecture/TOPOCORE_V6_SPRINT_60_FRESH_PR_OBSERVATION_RESULTS.md`

v6 active lab default and v5 deprecation candidate:

- `docs/architecture/TOPOCORE_V6_SPRINT_60_FRESH_PR_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_CANDIDATE.md`

Code-level deprecation preparation and v5 fallback retirement runway:

- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_CANDIDATE.md`
- `docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md`

v5-off simulation and fallback retirement runway:

- `docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md`
- `docs/architecture/TOPOCORE_V6_OPT_IN_V5_OFF_SIMULATION.md`

v6 authoritative default and v5 disabled-by-default runway:

- `docs/architecture/TOPOCORE_V6_OPT_IN_V5_OFF_SIMULATION.md`
- `docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md`

v5 runtime removal:

- `docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md`
- `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`

physical v5 cleanup and vendor asset removal:

- `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`
- `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`

final v5 residue cleanup and post-removal hardening:

- `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`
- `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`

final v6-only closeout, live sanity, and post-removal hardening:

- `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`
- `docs/architecture/TOPOCORE_V6_FINAL_V6_ONLY_CLOSEOUT.md`

direct external pilot, product-host install path, and post-community architecture:

- `docs/architecture/TOPOCORE_V6_FINAL_V6_ONLY_CLOSEOUT.md`
- `docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md`
- `docs/architecture/SPRINT_69_EXTERNAL_REPO_PILOT_AND_COMMUNITY_REMOVAL.md`

external command matrix validation on the pilot repo:

- `docs/architecture/SPRINT_69_EXTERNAL_REPO_PILOT_AND_COMMUNITY_REMOVAL.md`
- `docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md`

external retrieval and evidence quality on the pilot repo:

- `docs/architecture/SPRINT_70_EXTERNAL_COMMAND_MATRIX_ELEN_MCP.md`
- `docs/architecture/SPRINT_71_EXTERNAL_RETRIEVAL_EVIDENCE_QUALITY.md`

Why implementation is currently blocked:

- `docs/architecture/TOPOCORE_V6_PHASE_6_CONTROLLED_ADVISORY_EXPERIMENT_PROPOSAL.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

## 6. Current Decision State

Current decision state:

- v6 authoritative default is approved
- issue-comment lab v6 default is approved
- deprecated v5 runtime execution has been removed
- orphaned vendor assets have been removed
- final residue cleanup is complete
- final live v6 sanity has passed
- the v6-only transition is closed out
- direct external pilot architecture now points to `RepoBrain-Action`, not `repobrain-community`
- external issue and PR command matrix validation on `Elen-MCP-v.2.2.0` has passed
- external retrieval and evidence quality validation on `Elen-MCP-v.2.2.0` has passed
- fix migration remains conservative
- patch behavior expansion is not approved
- production and Marketplace switch are not approved

## 7. Repository Boundary Summary

Repository boundary summary:

RepoBrain-Action:

- primary/private GitHub runtime
- current v5/TKYA contract truth
- future v6 adapter around public facade
- GitHub Models orchestration
- safe product-level output mapping
- manual/local advisory validation
- still-disabled advisory boundary and tests

TopoCore v6:

- foundation decision library
- public facade
- decision contracts
- typed-summary ingestion
- safe external decision boundary

`repobrain-community`:

- public external GitHub foundation host
- reusable external workflow
- public install template
- bounded external command surface

`elen-mcp-prod_v2`:

- validation-only surface

## 8. Phase 7 Stabilization Scope

Allowed Phase 7 scope:

- documentation consolidation
- test index consolidation
- manual evidence checklist
- private dependency strategy proposal as docs-only
- cleanup of navigation links
- no runtime activation

Not allowed:

- advisory experiment implementation
- canary
- route migration
- v5 replacement
- fix migration
- patch behavior change
- user-visible output change
