# TopoCore v6 Stub Compatibility Tests

## 1. Purpose

Sprint 19 adds fake and stub compatibility coverage only.

Current truth:

- Sprint 19 does not wire TopoCore v6 into runtime
- Sprint 19 does not require private TopoCore v6 access
- Sprint 19 does not replace v5/TKYA

This sprint exists to prove that the existing adapter preview shape can be compared against fake or stub v6-style payload expectations without introducing runtime risk.

## 2. Relationship to Sprints 16-18

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`

Relationship:

- Sprint 16 defined the controlled migration strategy
- Sprint 17 defined the GitHub Models LLM summary contract
- Sprint 18 added the inert adapter skeleton
- Sprint 19 validates adapter shape against fake or stub v6-style fixtures and expectations

See also:

- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`

## 3. What Is Being Tested

Sprint 19 tests cover:

- request preview shape
- summary-family mapping
- safe candidate refs
- unsafe metadata blocking
- fake `ExternalDecisionView`-like product-level outputs
- no-runtime-wiring guard

The test focus is compatibility and safety, not runtime activation.

## 4. What Is Not Being Tested

- no live TopoCore v6 import
- no `create_topocore()` call
- no `decide()` call
- no `decide_external()` call
- no shadow mode
- no canary
- no route migration
- no fix migration
- no private dependency installation

## 5. Future Follow-Up

The next sprint may introduce either:

- local or private v6 validation planning, or
- a disabled or manual local validation harness

That follow-up should remain opt-in and must not affect CI or live runtime unless explicitly approved.
