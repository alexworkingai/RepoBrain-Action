# TopoCore v6 Final v5 Residue Sweep

## 1. Purpose

Sprint 67 performs the final v5 residue sweep after runtime removal and vendor removal.
It deletes standalone v5 docs discovered after Sprint 66.
It verifies that remaining v5 references are only historical or unsupported legacy diagnostics.

## 2. Baseline

- latest accepted main before Sprint 67: `0bc0712 Remove orphaned v5 vendor assets`
- Sprint 65 removed runtime execution
- Sprint 66 removed vendor assets
- user-discovered leftover docs:
  - `docs/topocore v5 architecture.md`
  - `docs/topocore v5 complete guide.md`

## 3. Discovery Results

Discovery found four main categories of residue:

- standalone v5-only docs in `docs/`
- active architecture notes whose top sections still read like v5 fallback or `lite` execution were current
- env reference rows that still listed legacy v5 or `lite` values alongside supported selectors
- legitimate historical docs and compatibility stubs that still mention v5 only as removed prior state

Action taken:

- deleted the two standalone v5 guides
- updated active policy docs to mark them as historical checkpoints and point to current v6-only policy docs
- updated env documentation to show supported selectors as `auto` and `v6` only
- kept historical migration documents only where they now read as superseded history

## 4. Deleted Files

- `docs/topocore v5 architecture.md`
- `docs/topocore v5 complete guide.md`

## 5. Remaining Allowed References

| File or path | Reference type | Reason allowed |
|---|---|---|
| `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md` | historical migration record | preserves the pre-removal baseline and is now marked historical |
| `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md` | historical migration record | preserves original migration framing and is now marked historical |
| `docs/architecture/TOPOCORE_V6_*` removal and deprecation notes | historical migration record | record the staged transition from fallback to removal |
| `docs/env_reference.md` | unsupported legacy env diagnostic | documents removed legacy envs as unsupported or obsolete |
| `repobrain/tky_engine.py` | compatibility stub or contract | stable request and decision contract with no v5 execution |
| `repobrain/tkya/engine.py` | compatibility stub or contract | import-stability stub that returns sanitized removed-runtime errors only |
| `tests/test_topocore_v5_runtime_removed.py` and `tests/test_topocore_v5_vendor_assets_removed.py` | absence or removal tests | guard against returning removed runtime or vendor residue |

## 6. Current Runtime Policy

Supported:

- `auto`
- `v6`

Unsupported:

- `v5`
- `lite`
- `RB_TKYA_BACKEND` values `v5` and `lite`
- `RB_TOPOCORE_ALLOW_DEPRECATED_V5`
- `RB_TOPOCORE_V5_SIMULATE_DISABLED`

Current behavior:

- no v5 fallback
- no vendor assets
- no runtime execution through legacy inputs
- safe unsupported diagnostics only for old env values

## 7. Static Proof

Sprint 67 static proof confirms:

- no `docs/topocore v5 architecture.md`
- no `docs/topocore v5 complete guide.md`
- no `repobrain::tkya::vendor`
- no `canary_v5` workflow
- no active workflow or action support for v5 or `lite` selectors
- no active code, test, workflow, or action content using legacy lower-case `topocore_v5` runtime markers
- no v5 vendor execution tests remain

## 8. Live v6 Sanity

Post-merge live v6 sanity was not run in Sprint 67.
If needed, it should be executed on `main` only, because `issue_comment` runs the main branch workflow.

## 9. Safety Boundaries

- no patch application
- no file modification by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no production or Marketplace switch
- no `repobrain-community` change

## 10. Next Step

If a live v6 sanity check is still desired, run one minimal `issue_comment` or `workflow_dispatch` check on `main`.
If that passes, Sprint 68 can be a final migration closeout and documentation polish sprint rather than another v5-removal sprint.

## 11. Non-Goals

- no patch or autofix
- no production or Marketplace switch
- no `repobrain-community` change
