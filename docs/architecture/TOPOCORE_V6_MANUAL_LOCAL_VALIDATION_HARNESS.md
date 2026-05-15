# TopoCore v6 Manual/Local Validation Harness

## 1. Purpose

Sprint 21 introduces a manual and disabled local validation harness.

Current truth:

- it is not runtime wiring
- it is not shadow mode
- it is not canary
- it does not replace v5/TKYA
- it does not require TopoCore v6 in default CI

The harness exists only as an opt-in developer tool for local validation.

## 2. Relationship to Sprints 16-20

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`
- `docs/architecture/GITHUB_MODELS_LLM_SUMMARY_CONTRACT_TOPOCORE_V6.md`
- `docs/architecture/TOPOCORE_V6_ADAPTER_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_STUB_COMPATIBILITY_TESTS.md`
- `docs/architecture/TOPOCORE_V6_LOCAL_PRIVATE_VALIDATION_HARNESS_PLAN.md`

Relationship:

- Sprint 20 planned the harness
- Sprint 21 implements the disabled and manual version only

See also:

- `docs/architecture/TOPOCORE_V6_DECISION_DIFF_STRATEGY.md`
- `docs/architecture/TOPOCORE_V6_SHADOW_MODE_DESIGN_AND_GO_NOGO.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_PRIVATE_DEPENDENCY_STRATEGY_PROPOSAL.md`

## 3. How to Run Manually

PowerShell:

```powershell
$env:RB_TOPOCORE_V6_LOCAL_VALIDATE="1"
python scripts/validate_topocore_v6_local.py
```

Optional strict mode:

```powershell
$env:RB_TOPOCORE_V6_REQUIRE_LOCAL="1"
$env:RB_TOPOCORE_V6_LOCAL_VALIDATE="1"
python scripts/validate_topocore_v6_local.py
```

## 4. Default Behavior

- without `RB_TOPOCORE_V6_LOCAL_VALIDATE=1`, the script skips and exits `0`
- missing `topocore_v6` does not fail default CI
- strict failure requires `RB_TOPOCORE_V6_REQUIRE_LOCAL=1`

## 5. Safety Boundaries

- public facade only
- no internal modules
- no `decide_raw`
- no raw traces
- no `compression_stats`
- no governance internals
- no raw query, raw code, or secrets
- no GitHub runtime wiring
- no patch application

## 6. What the Harness Validates

The harness validates that:

- adapter preview data can be converted into v6 request-like objects
- the public facade can be created locally when available
- `decide()` and `decide_external()` can be called for local fixtures
- output remains sanitized and product-level

## 7. What the Harness Does Not Validate

- no live GitHub Models
- no live GitHub API
- no real PR runtime
- no shadow mode
- no canary
- no v5/v6 route parity
- no fix migration
- no patch application

## 8. Future Follow-Up

The next sprint may define:

- decision diff strategy, or
- a shadow-mode design document

Shadow mode should not be activated until manual validation evidence is accepted.
